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
REMOVED = (
    'etc/selinux/precompiled_sepolicy',
    'etc/selinux/precompiled_sepolicy.plat_sepolicy_and_mapping.sha256',
    'etc/selinux/precompiled_sepolicy.system_ext_sepolicy_and_mapping.sha256',
)
SEPOLICY = 'etc/selinux/odm_sepolicy.cil'
SERVICE_CONTEXTS = 'etc/selinux/odm_service_contexts'
SELINUX_LABEL_OF = 'etc/selinux/odm_hwservice_contexts'
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


def escape(path):
    return re.sub(r'([.^$*+?()\[\]{}|\\])', r'\\\1', path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stock', required=True)
    parser.add_argument('--sepolicy', required=True)
    parser.add_argument('--service-contexts', required=True)
    parser.add_argument('--modules', required=True)
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

    for rel in REMOVED:
        if rel not in meta:
            sys.exit(f'stock odm has no /{rel}')
        os.remove(os.path.join(root, rel))
        del meta[rel]

    with open(os.path.join(root, SEPOLICY), 'ab') as f:
        f.write(open(args.sepolicy, 'rb').read())

    if SERVICE_CONTEXTS in meta:
        sys.exit(f'stock odm already has /{SERVICE_CONTEXTS}')
    shutil.copyfile(args.service_contexts, os.path.join(root, SERVICE_CONTEXTS))
    meta[SERVICE_CONTEXTS] = meta[SELINUX_LABEL_OF]

    for ko, (symbol, name) in FIRMWARE.items():
        rel = 'firmware/' + name
        if rel in meta:
            sys.exit(f'stock odm already has /{rel}')
        with open(os.path.join(root, rel), 'wb') as f:
            f.write(carve(os.path.join(args.modules, ko), symbol))
        meta[rel] = (0, 0, 0o644, FIRMWARE_LABEL)

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
