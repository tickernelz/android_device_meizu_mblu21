#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import os
import shutil
import struct
import sys
from os import path
from pathlib import Path
from tempfile import TemporaryDirectory

from extract_utils.args import ArgsSource, parse_args
from extract_utils.extract import ExtractCtx, extract_fns_user_type
from extract_utils.extract_recovery import (
    extract_ramdisk,
    parse_mkbootimg_fragments,
    unpack_bootimg,
)
from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.lp import LpImage
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils.utils import run_cmd

BLOCK_DEVICE_PARTITIONS = {
    'by-name': [
        'boot',
        'dtbo',
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

AVB_FOOTER_MAGIC = b'AVBf'
AVB_FOOTER_SIZE = 64
DTB_NAME = 'ums9230_6h10.dtb'
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
        for partition in BLOCK_DEVICE_PARTITIONS['mapper']:
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

    kernel_path = path.join(images_dir, 'kernel')
    if path.basename(file_path) == 'boot.img' and not path.exists(kernel_path):
        with TemporaryDirectory() as tmp_dir:
            unpack_bootimg(image_path, tmp_dir)
            shutil.move(path.join(tmp_dir, 'kernel'), kernel_path)

    return None


def extract_vendor_boot(ctx: ExtractCtx, file_path: str, dump_dir: str):
    if not is_dump_root_file(file_path, dump_dir):
        return None

    ramdisk_dir = path.join(dump_dir, 'vendor_ramdisk')
    if path.isdir(ramdisk_dir):
        return None

    dtb_dir = path.join(dump_dir, 'dtb')
    os.makedirs(dtb_dir, exist_ok=True)

    with TemporaryDirectory() as tmp_dir:
        output = unpack_bootimg(file_path, tmp_dir)
        for fragment in parse_mkbootimg_fragments(output):
            if fragment.ramdisk_type == VENDOR_RAMDISK_TYPE_PLATFORM:
                extract_ramdisk(fragment.path, Path(ramdisk_dir))

        shutil.copyfile(
            path.join(tmp_dir, 'dtb'),
            path.join(dtb_dir, DTB_NAME),
        )

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
    r'^(super|odm|system_dlkm|vendor|vendor_dlkm)\.img$': extract_logical_images,
    r'^(boot|dtbo)\.img$': extract_boot_images,
    r'^vendor_boot\.img$': extract_vendor_boot,
    r'^l_modem\.img$': extract_modem_avb_key,
}

blob_fixups: blob_fixups_user_type = {
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

if __name__ == '__main__':
    with TemporaryDirectory() as adb_dump_dir:
        args = parse_args()
        if args.source == ArgsSource.ADB and not args.regenerate_makefiles:
            pull_partitions_over_adb(adb_dump_dir)
            sys.argv.append(adb_dump_dir)

        utils = ExtractUtils.device(module)
        utils.run()
