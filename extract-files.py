#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import os
import re
import shutil
import struct
import sys
from os import path
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

from extract_utils.args import ArgsSource, parse_args
from extract_utils.extract import ExtractCtx, extract_fns_user_type
from extract_utils.extract_recovery import (
    extract_ramdisk,
    parse_mkbootimg_fragments,
    unpack_bootimg,
)
from extract_utils.file import File
from extract_utils.fixups_blob import (
    BlobFixupCtx,
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.lp import LpImage
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils.tools import apktool_path, java_path
from extract_utils.utils import file_path_sha1, run_cmd

BLOCK_DEVICE_PARTITIONS = {
    'by-name': [
        'boot',
        'l_agdsp',
        'l_gdsp',
        'l_ldsp',
        'l_modem',
        'pm_sys',
        'vendor_boot',
    ],
    'mapper': [
        'odm',
        'system_dlkm',
        'vendor',
        'vendor_dlkm',
    ],
}

IMAGE_PARTITIONS = ['odm', 'vendor']

AVB_FOOTER_MAGIC = b'AVBf'
AVB_FOOTER_SIZE = 64
VENDOR_RAMDISK_TYPE_PLATFORM = 1


def is_dump_root_file(file_path: str, dump_dir: str):
    return path.samefile(path.dirname(file_path), dump_dir)


def read_avb_footer(file_path: str):
    with open(file_path, 'rb') as f:
        f.seek(-AVB_FOOTER_SIZE, os.SEEK_END)
        footer = f.read(AVB_FOOTER_SIZE)

    magic, _, _, image_size, vbmeta_offset, vbmeta_size = struct.unpack_from(
        '!4s2L3Q', footer
    )
    if magic != AVB_FOOTER_MAGIC:
        return None

    return image_size, vbmeta_offset, vbmeta_size


def read_avb_public_key(file_path: str):
    footer = read_avb_footer(file_path)
    assert footer is not None, f'{file_path} has no AVB footer'
    _, vbmeta_offset, vbmeta_size = footer

    with open(file_path, 'rb') as f:
        f.seek(vbmeta_offset)
        vbmeta = f.read(vbmeta_size)

    (authentication_size,) = struct.unpack_from('!Q', vbmeta, 12)
    key_offset, key_size = struct.unpack_from('!2Q', vbmeta, 64)
    key_start = 256 + authentication_size + key_offset
    return vbmeta[key_start : key_start + key_size]


def link_unslotted_image(ctx: ExtractCtx, file_path: str, dump_dir: str):
    if not is_dump_root_file(file_path, dump_dir):
        return None

    file_name = path.basename(file_path)
    partition = file_name.split('.', 1)[0].removesuffix('_a')
    link_path = path.join(dump_dir, f'{partition}.img')
    if not path.lexists(link_path):
        os.symlink(file_name, link_path)

    return None


def extract_logical_images(ctx: ExtractCtx, file_path: str, dump_dir: str):
    if not is_dump_root_file(file_path, dump_dir):
        return None

    images_dir = path.join(dump_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    partition, _ = path.splitext(path.basename(file_path))
    if partition != 'super':
        image_path = path.join(images_dir, f'{partition}.img')
        if not path.exists(image_path):
            shutil.copyfile(file_path, image_path)
        return None

    with open(file_path, 'rb') as f:
        super_image = LpImage(f)
        for partition in IMAGE_PARTITIONS:
            image_path = path.join(images_dir, f'{partition}.img')
            if not path.exists(image_path):
                super_image.extract_partition(partition, image_path)

    return None


def extract_boot_images(ctx: ExtractCtx, file_path: str, dump_dir: str):
    if not is_dump_root_file(file_path, dump_dir):
        return None

    images_dir = path.join(dump_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    image_path = path.join(images_dir, path.basename(file_path))
    if not path.exists(image_path):
        shutil.copyfile(file_path, image_path)
        footer = read_avb_footer(image_path)
        if footer is not None:
            os.truncate(image_path, footer[0])

    return None


def extract_vendor_boot(ctx: ExtractCtx, file_path: str, dump_dir: str):
    if not is_dump_root_file(file_path, dump_dir):
        return None

    ramdisk_dir = path.join(dump_dir, 'vendor_ramdisk')
    if path.isdir(ramdisk_dir):
        return None

    with TemporaryDirectory() as tmp_dir:
        output = unpack_bootimg(file_path, tmp_dir)
        for fragment in parse_mkbootimg_fragments(output):
            if fragment.ramdisk_type == VENDOR_RAMDISK_TYPE_PLATFORM:
                extract_ramdisk(fragment.path, Path(ramdisk_dir))

    return None


def extract_modem_avb_key(ctx: ExtractCtx, file_path: str, dump_dir: str):
    if not is_dump_root_file(file_path, dump_dir):
        return None

    avb_dir = path.join(dump_dir, 'avb')
    os.makedirs(avb_dir, exist_ok=True)

    key_path = path.join(avb_dir, 'unisoc_modem.avbpubkey')
    if not path.exists(key_path):
        with open(key_path, 'wb') as f:
            f.write(read_avb_public_key(file_path))

    return None


TELEPHONY_METRICS = 'Lcom/android/internal/telephony/metrics/TelephonyMetrics;'
HIDDENAPI_FLAG = re.compile(
    r'^(whitelist|blacklist|greylist(-max-\w+)?|test-api|core-platform-api|max-target-\w+|sdk|unsupported|blocked|conditional)$'
)


def apktool(*args: str):
    run_cmd([java_path, '-jar', apktool_path, *args])


def read_text(file_path: str):
    with open(file_path) as f:
        return f.read()


def write_text(file_path: str, text: str):
    with open(file_path, 'w') as f:
        f.write(text)


def drop_telephony_metrics(smali_dir: str):
    metrics = re.escape(TELEPHONY_METRICS)
    for name in ('ImsRadioInterface.smali', 'ImsRadioInterface$RilHandler.smali'):
        file_path = path.join(smali_dir, 'com/spreadtrum/ims', name)
        text = re.sub(
            r'invoke-static \{\}, ' + metrics + r'->getInstance\(\)' + metrics
            + r'\n\n    move-result-object (v\d+)',
            r'const/4 \1, 0x0',
            read_text(file_path),
        )
        text = re.sub(
            r'\n    invoke-virtual(/range)? \{[^}]*\}, ' + metrics + r'->writeOn\w+\([^)]*\)V\n',
            '\n',
            text,
        )
        assert not re.search(
            r'invoke-[\w/]+ \{[^}]*\}, ' + metrics + '->', text
        ), f'{name}: TelephonyMetrics call left'
        write_text(file_path, text.replace(TELEPHONY_METRICS, 'Ljava/lang/Object;'))
    for root, _, files in os.walk(smali_dir):
        for name in files:
            assert TELEPHONY_METRICS not in read_text(
                path.join(root, name)
            ), f'{name}: TelephonyMetrics reference left'


def drop_call(smali_dir: str, smali_path: str, method: str):
    file_path = path.join(smali_dir, smali_path)
    text, count = re.subn(
        r'\n    invoke-virtual(/range)? \{[^}]*\}, ' + re.escape(method) + r'\n',
        '\n',
        read_text(file_path),
    )
    assert count == 1, f'{smali_path}: expected one call to {method}, found {count}'
    write_text(file_path, text)


def strip_hiddenapi_flags(smali_dir: str):
    for root, _, files in os.walk(smali_dir):
        for name in files:
            file_path = path.join(root, name)
            lines = read_text(file_path).split('\n')
            for i, line in enumerate(lines):
                if line.startswith(('.method ', '.field ')):
                    tokens = line.split(' ')
                    member = next(
                        j for j, t in enumerate(tokens) if '(' in t or ':' in t
                    )
                    kept = [t for t in tokens[1:member] if not HIDDENAPI_FLAG.match(t)]
                    lines[i] = ' '.join([tokens[0], *kept, *tokens[member:]])
            write_text(file_path, '\n'.join(lines))


def merge_boot_jars(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    *args,
    jars: List[Tuple[str, Optional[str]]],
    dropped_calls: List[Tuple[str, str]],
    tmp_dir: Optional[str] = None,
    **kwargs,
):
    assert tmp_dir is not None
    proprietary_dir = file_path[: -len(file.dst)]
    app_dir = path.join(tmp_dir, 'app')
    apktool('d', '-r', '-f', file_path, '-o', app_dir)
    smali_dir = path.join(app_dir, 'smali')
    if file.dst == IMS_APK:
        drop_telephony_metrics(smali_dir)
    for smali_path, method in dropped_calls:
        drop_call(smali_dir, smali_path, method)
    for index, (jar, only) in enumerate(jars, start=2):
        jar_dir = path.join(tmp_dir, f'jar{index}')
        apktool('d', '-r', '-f', path.join(proprietary_dir, jar), '-o', jar_dir)
        src = path.join(jar_dir, 'smali')
        dst = path.join(app_dir, f'smali_classes{index}')
        if only is None:
            shutil.copytree(src, dst)
        else:
            os.makedirs(path.join(dst, path.dirname(only)))
            for name in os.listdir(path.join(src, path.dirname(only))):
                if re.fullmatch(re.escape(path.basename(only)) + r'(\$\w+)?\.smali', name):
                    shutil.copy(path.join(src, path.dirname(only), name), path.join(dst, path.dirname(only)))
        strip_hiddenapi_flags(dst)
    apktool('b', app_dir, '-o', file_path)


IMS_APK = 'system_ext/priv-app/ims/ims.apk'
RADIO_INTERACTOR_APK = 'system_ext/priv-app/radio_interactor_service/radio_interactor_service.apk'
RADIO_INTERACTOR_COMMON = 'system/framework/radio_interactor_common.jar'


def pull_partitions_over_adb(dump_dir: str):
    run_cmd(['adb', 'wait-for-device'])
    run_cmd(['adb', 'root'])
    run_cmd(['adb', 'wait-for-device'])

    slot_suffix = run_cmd(
        ['adb', 'shell', 'getprop', 'ro.boot.slot_suffix']
    ).strip()

    for block_dir, partitions in BLOCK_DEVICE_PARTITIONS.items():
        for partition in partitions:
            run_cmd(
                [
                    'adb',
                    'pull',
                    f'/dev/block/{block_dir}/{partition}{slot_suffix}',
                    path.join(dump_dir, f'{partition}.img'),
                ]
            )


extract_fns: extract_fns_user_type = {
    r'^(.+_a\.(bin|img)|super\.bin)$': link_unslotted_image,
    r'^(super|odm|vendor)\.img$': extract_logical_images,
    r'^boot\.img$': extract_boot_images,
    r'^vendor_boot\.img$': extract_vendor_boot,
    r'^l_modem\.img$': extract_modem_avb_key,
}

blob_fixups: blob_fixups_user_type = {
    IMS_APK: blob_fixup()
        .call(
            merge_boot_jars,
            jars=[
                ('system/framework/unisoc_ims_common.jar', None),
                (RADIO_INTERACTOR_COMMON, None),
                ('system_ext/framework/unisoc-framework.jar', 'com/android/ims/internal/ImsCallForwardInfoEx'),
            ],
            dropped_calls=[],
        )
        .stripzip(),
    RADIO_INTERACTOR_APK: blob_fixup()
        .call(
            merge_boot_jars,
            jars=[(RADIO_INTERACTOR_COMMON, None)],
            dropped_calls=[
                (
                    'com/android/unisoc/telephony/server/ExtRadioNetworkIndication.smali',
                    'Lcom/android/internal/telephony/ServiceStateTracker;->startUpdateState(IIII)V',
                ),
            ],
        )
        .stripzip(),
    'vendor_ramdisk/first_stage_ramdisk/fstab.ums9230_6h10': blob_fixup()
        .regex_replace(r',avb(_keys)?=[^,\s]*', ''),
}  # fmt: skip

module = ExtractUtilsModule(
    'mblu21',
    'meizu',
    blob_fixups=blob_fixups,
    extract_fns=extract_fns,
    add_firmware_proprietary_file=True,
)

def unpinned_vendor_files():
    found = []
    for proprietary_file in module.proprietary_files:
        vendor_path = module.proprietary_file_vendor_path(proprietary_file)
        for file in proprietary_file.file_list.files:
            expected = file.fixup_hash or file.hash
            if expected is None:
                continue
            file_path = path.join(vendor_path, file.dst)
            if not path.isfile(file_path):
                found.append(f'{file.dst}: missing, pinned {expected}')
                continue
            actual = file_path_sha1(file_path)
            if actual != expected:
                found.append(f'{file.dst}: SHA-1 {actual}, pinned {expected}')
    return found


if __name__ == '__main__':
    with TemporaryDirectory() as adb_dump_dir:
        args = parse_args()
        if args.source == ArgsSource.ADB and not args.regenerate_makefiles:
            pull_partitions_over_adb(adb_dump_dir)
            sys.argv.append(adb_dump_dir)

        utils = ExtractUtils.device(module)
        utils.run()

    if not args.regenerate_makefiles:
        unpinned = unpinned_vendor_files()
        if unpinned:
            sys.exit('Extracted files do not match their pins:\n' + '\n'.join(unpinned))
