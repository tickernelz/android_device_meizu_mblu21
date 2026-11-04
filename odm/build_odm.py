#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import argparse
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys

FIRMWARE = {
    'spi_ilitek.ko': ('CTPM_FW_DEF', 'ILITEK_FW_DEF.ili'),
    'focaltech_spi_v4_1.ko': ('fw_file', 'focaltech_ts_fw_.bin'),
}
PRECOMPILED = 'etc/selinux/precompiled_sepolicy'
POLICY_HASHES = (
    ('system', 'etc/selinux/plat_sepolicy.cil', 'etc/selinux/plat_sepolicy_and_mapping.sha256'),
    ('system_ext', 'etc/selinux/system_ext_sepolicy.cil',
     'etc/selinux/system_ext_sepolicy_and_mapping.sha256'),
    ('product', 'etc/selinux/product_sepolicy.cil', 'etc/selinux/product_sepolicy_and_mapping.sha256'),
)
POLICY_HASH_META = (0, 0, 0o644, 'u:object_r:vendor_configs_file:s0')
POLICY_VERSION = 30
DEFAULT_GENFS_LABELS_VERSION = 202404
SEPOLICY = 'etc/selinux/odm_sepolicy.cil'
SERVICE_CONTEXTS = 'etc/selinux/odm_service_contexts'
SERVICE_CONTEXTS_LABEL = 'u:object_r:vendor_service_contexts_file:s0'
PROPERTY_CONTEXTS = 'etc/selinux/odm_property_contexts'
FIRMWARE_LABEL = 'u:object_r:vendor_file:s0'
XATTR_PREFIX = {1: 'user.', 4: 'trusted.', 6: 'security.'}


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


class Erofs:
    def __init__(self, path):
        self.data = open(path, 'rb').read()
        sb = 1024
        if struct.unpack_from('<I', self.data, sb)[0] != 0xE0F5E1E2:
            sys.exit(f'{path}: not an EROFS image')
        self.blksz = 1 << self.data[sb + 12]
        self.build_time, = struct.unpack_from('<Q', self.data, sb + 24)
        self.meta, self.xattr = struct.unpack_from('<II', self.data, sb + 40)
        self.uuid = self.data[sb + 48:sb + 64]

    def entry(self, off):
        name_len, index, value_size = struct.unpack_from('<BBH', self.data, off)
        name = self.data[off + 4:off + 4 + name_len].decode()
        value = self.data[off + 4 + name_len:off + 4 + name_len + value_size]
        if index not in XATTR_PREFIX:
            sys.exit(f'unsupported xattr name index {index}')
        size = (4 + name_len + value_size + 3) & ~3
        return XATTR_PREFIX[index] + name, value, size

    def xattrs(self, nid):
        off = self.meta * self.blksz + nid * 32
        fmt, icount = struct.unpack_from('<HH', self.data, off)
        if not icount:
            return {}
        off += 64 if fmt & 1 else 32
        end = off + 12 + (icount - 1) * 4
        shared = self.data[off + 4]
        off += 12
        result = {}
        for _ in range(shared):
            xid, = struct.unpack_from('<I', self.data, off)
            name, value, _ = self.entry(self.xattr * self.blksz + xid * 4)
            result[name] = value
            off += 4
        while off < end:
            name, value, size = self.entry(off)
            result[name] = value
            off += size
        return result


def tree(root):
    paths = ['']
    for top, dirs, files in os.walk(root):
        dirs.sort()
        rel = os.path.relpath(top, root)
        rel = '' if rel == '.' else rel + '/'
        paths += [rel + n for n in sorted(dirs) + sorted(files)]
    return sorted(paths)


def metadata(binary, image, root):
    fs = Erofs(image)
    meta = {}
    for path in tree(root):
        out = run(binary, f'--path=/{path}', image)
        nid = int(re.search(r'NID: (\d+)', out).group(1))
        uid, gid, mode = re.search(r'Uid: (\d+)\s+Gid: (\d+)\s+Access: ([0-7]+)/', out).groups()
        xattrs = fs.xattrs(nid)
        extra = set(xattrs) - {'security.selinux'}
        if extra:
            sys.exit(f'/{path}: unsupported xattrs {sorted(extra)}')
        label = xattrs.get('security.selinux', b'').rstrip(b'\0').decode()
        meta[path] = (int(uid), int(gid), int(mode, 8), label)
    return fs, meta


def carve(ko, symbol):
    data = open(ko, 'rb').read()
    shoff, = struct.unpack_from('<Q', data, 0x28)
    shentsize, shnum = struct.unpack_from('<HH', data, 0x3a)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, shoff + i * shentsize) for i in range(shnum)]
    for sh in sections:
        if sh[1] != 2:
            continue
        strtab = sections[sh[6]]
        for off in range(sh[4], sh[4] + sh[5], sh[9]):
            name, _, _, shndx, value, size = struct.unpack_from('<IBBHQQ', data, off)
            end = data.index(b'\0', strtab[4] + name)
            if data[strtab[4] + name:end].decode() == symbol:
                target = sections[shndx]
                if target[1] == 8:
                    sys.exit(f'{ko}: {symbol} has no file data')
                return data[target[4] + value:target[4] + value + size]
    sys.exit(f'{ko}: symbol {symbol} not found')


def first_line(path):
    return open(path).read().split('\n')[0]


def extract_selinux(tool, image, dest, sub):
    with open(image, 'rb') as f:
        head = f.read(4)
        f.seek(1024)
        erofs = struct.unpack('<I', f.read(4))[0] == 0xE0F5E1E2
    if erofs:
        run(tool('fsck.erofs'), f'--extract={dest}', '--no-preserve', image)
        return
    if struct.unpack('<I', head)[0] == 0xED26FF3A:
        raw = dest + '.raw'
        run(tool('simg2img'), image, raw)
        image = raw
    etc = os.path.join(dest, sub, 'etc')
    os.makedirs(etc)
    src = '/' + os.path.join(sub, 'etc/selinux') if sub else '/etc/selinux'
    run(tool('debugfs'), '-R', f'rdump {src} {etc}', image)
    if not os.path.isdir(os.path.join(etc, 'selinux')):
        sys.exit(f'{image}: no {src}')
    if image.endswith('.raw'):
        os.remove(image)


def split_policy(secilc, parts, out):
    plat = os.path.join(parts['system'], 'etc/selinux')
    vendor = os.path.join(parts['vendor'], 'etc/selinux')
    version = first_line(os.path.join(vendor, 'plat_sepolicy_vers.txt'))
    if not version:
        sys.exit('vendor plat_sepolicy_vers.txt is empty')
    try:
        genfs = int(open(os.path.join(vendor, 'genfs_labels_version.txt')).read().strip())
    except (FileNotFoundError, ValueError):
        genfs = DEFAULT_GENFS_LABELS_VERSION
    genfs_cil = os.path.join(plat, f'plat_sepolicy_genfs_{genfs}.cil')
    if not os.path.exists(genfs_cil) and genfs >= 202504:
        sys.exit(f'system has no {os.path.basename(genfs_cil)}')
    for required in ('plat_pub_versioned.cil', 'vendor_sepolicy.cil'):
        if not os.path.exists(os.path.join(vendor, required)):
            sys.exit(f'vendor has no etc/selinux/{required}')
    optional = [
        os.path.join(plat, f'mapping/{version}.compat.cil'),
        os.path.join(parts['system_ext'], 'etc/selinux/system_ext_sepolicy.cil'),
        os.path.join(parts['system_ext'], f'etc/selinux/mapping/{version}.cil'),
        os.path.join(parts['system_ext'], f'etc/selinux/mapping/{version}.compat.cil'),
        os.path.join(parts['product'], 'etc/selinux/product_sepolicy.cil'),
        os.path.join(parts['product'], f'etc/selinux/mapping/{version}.cil'),
        os.path.join(vendor, 'plat_pub_versioned.cil'),
        os.path.join(vendor, 'vendor_sepolicy.cil'),
        os.path.join(parts['odm'], SEPOLICY),
        genfs_cil,
    ]
    run(secilc, os.path.join(plat, 'plat_sepolicy.cil'), '-m', '-M', 'true', '-G', '-N', '-v',
        '-c', str(POLICY_VERSION), os.path.join(plat, f'mapping/{version}.cil'),
        '-o', out, '-f', os.devnull, *[f for f in optional if os.path.exists(f)])


def escape(path):
    return re.sub(r'([.^$*+?()\[\]{}|\\])', r'\\\1', path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stock', required=True)
    parser.add_argument('--sepolicy', required=True)
    parser.add_argument('--service-contexts', required=True)
    parser.add_argument('--property-contexts', required=True)
    parser.add_argument('--modules', required=True)
    parser.add_argument('--system', required=True)
    parser.add_argument('--system-ext', required=True)
    parser.add_argument('--product', required=True)
    parser.add_argument('--vendor', required=True)
    parser.add_argument('--host-bin', required=True)
    parser.add_argument('--avbtool', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    tool = lambda name: os.path.join(args.host_bin, name)

    work = args.out + '.work'
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    root = os.path.join(work, 'root')
    run(tool('fsck.erofs'), f'--extract={root}', '--no-preserve', args.stock)
    stock, meta = metadata(tool('dump.erofs'), args.stock, root)

    with open(os.path.join(root, SEPOLICY), 'ab') as f:
        f.write(open(args.sepolicy, 'rb').read())
    with open(os.path.join(root, PROPERTY_CONTEXTS), 'ab') as f:
        f.write(b'\n' + open(args.property_contexts, 'rb').read())

    if SERVICE_CONTEXTS in meta:
        sys.exit(f'stock odm already has /{SERVICE_CONTEXTS}')
    shutil.copyfile(args.service_contexts, os.path.join(root, SERVICE_CONTEXTS))
    meta[SERVICE_CONTEXTS] = (0, 0, 0o644, SERVICE_CONTEXTS_LABEL)

    for ko, (symbol, name) in FIRMWARE.items():
        rel = 'firmware/' + name
        if rel in meta:
            sys.exit(f'stock odm already has /{rel}')
        with open(os.path.join(root, rel), 'wb') as f:
            f.write(carve(os.path.join(args.modules, ko), symbol))
        meta[rel] = (0, 0, 0o644, FIRMWARE_LABEL)

    parts = {'odm': root}
    for name, image, sub in (('system', args.system, 'system'), ('system_ext', args.system_ext, ''),
                             ('product', args.product, ''), ('vendor', args.vendor, '')):
        extract_selinux(tool, image, os.path.join(work, name), sub)
        parts[name] = os.path.join(work, name, sub)
    if PRECOMPILED not in meta:
        sys.exit(f'stock odm has no /{PRECOMPILED}')
    split_policy(tool('secilc'), parts, os.path.join(root, PRECOMPILED))
    for name, cil, rel in POLICY_HASHES:
        actual = os.path.join(parts[name], rel)
        target = PRECOMPILED + '.' + os.path.basename(rel)
        if os.path.exists(actual):
            shutil.copyfile(actual, os.path.join(root, target))
            meta.setdefault(target, POLICY_HASH_META)
        elif os.path.exists(os.path.join(parts[name], cil)):
            sys.exit(f'{name} has /{cil} but no /{rel}')
        elif target in meta:
            os.remove(os.path.join(root, target))
            del meta[target]

    contexts = os.path.join(work, 'file_contexts')
    fs_config = os.path.join(work, 'fs_config')
    with open(contexts, 'w') as fc, open(fs_config, 'w') as cfg:
        for path, (uid, gid, mode, label) in sorted(meta.items()):
            fc.write(f'{escape("/odm/" + path) if path else "/odm(/.*)?"} {label}\n')
            cfg.write(f'{"odm/" + path if path else "/"} {uid} {gid} {mode:o}\n')

    raw = os.path.join(work, 'odm.img')
    run(tool('mkfs.erofs'), '-zlz4hc,9', f'-T{stock.build_time}', '--all-time',
        f'-U{stock.uuid.hex()[:8]}-{stock.uuid.hex()[8:12]}-{stock.uuid.hex()[12:16]}-'
        f'{stock.uuid.hex()[16:20]}-{stock.uuid.hex()[20:]}',
        '--mount-point=odm', f'--fs-config-file={fs_config}', f'--file-contexts={contexts}',
        raw, root)

    check = os.path.join(work, 'check')
    run(tool('fsck.erofs'), f'--extract={check}', '--no-preserve', raw)
    _, built = metadata(tool('dump.erofs'), raw, check)
    if built != meta:
        for path in sorted(set(built) | set(meta)):
            if built.get(path) != meta.get(path):
                print(f'/{path}: expected {meta.get(path)} built {built.get(path)}', file=sys.stderr)
        sys.exit('odm metadata mismatch')
    run('diff', '-r', '--no-dereference', root, check)

    info = run(args.avbtool, 'info_image', '--image', args.stock)
    props = re.findall(r"Prop: (\S+) -> '([^']*)'", info)
    cmd = [args.avbtool, 'add_hashtree_footer', '--image', raw, '--partition_name', 'odm',
           '--hash_algorithm', 'sha256', '--do_not_generate_fec',
           '--partition_size', str(-(-os.path.getsize(raw) * 102 // 100 // 4096) * 4096 + 1024 * 1024),
           '--salt', hashlib.sha256(open(raw, 'rb').read()).hexdigest()]
    for key, value in props:
        cmd += ['--prop', f'{key}:{value}']
    run(*cmd)
    os.replace(raw, args.out)
    shutil.rmtree(work)


if __name__ == '__main__':
    main()
