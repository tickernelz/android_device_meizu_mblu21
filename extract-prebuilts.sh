#!/bin/bash
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "usage: $0 <partition_dump_dir> <lpunpack_super_dir>" >&2
    exit 1
fi

DUMP="$1"
SUPER="$2"
MY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANDROID_ROOT="${ANDROID_ROOT:-${MY_DIR}/../../..}"
VENDOR_DIR="${ANDROID_ROOT}/vendor/meizu/mblu21"
AVBTOOL="${AVBTOOL:-${ANDROID_ROOT}/external/avb/avbtool.py}"
UNPACK_BOOTIMG="${UNPACK_BOOTIMG:-${ANDROID_ROOT}/system/tools/mkbootimg/unpack_bootimg.py}"
OUT="${VENDOR_DIR}/images"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

mkdir -p "${OUT}"

for part in boot dtbo; do
    install -m 0644 "${DUMP}/${part}_a.bin" "${OUT}/${part}.img"
    python3 "${AVBTOOL}" erase_footer --image "${OUT}/${part}.img"
done

for part in vendor odm vendor_dlkm system_dlkm; do
    install -m 0644 "${SUPER}/${part}_a.img" "${OUT}/${part}.img"
done

python3 "${UNPACK_BOOTIMG}" --boot_img "${DUMP}/vendor_boot_a.bin" --out "${WORK}/vendor_boot" >/dev/null
mkdir -p "${WORK}/ramdisk"
lz4 -dc "${WORK}/vendor_boot/vendor_ramdisk00" | (cd "${WORK}/ramdisk" && cpio -idm --quiet)

rm -rf "${VENDOR_DIR}/dtb" "${VENDOR_DIR}/vendor_ramdisk"
mkdir -p "${VENDOR_DIR}/dtb" "${VENDOR_DIR}/vendor_ramdisk/lib/modules" "${VENDOR_DIR}/vendor_ramdisk/first_stage_ramdisk"
install -m 0644 "${WORK}/vendor_boot/dtb" "${VENDOR_DIR}/dtb/ums9230_6h10.dtb"
install -m 0644 "${WORK}/ramdisk/lib/modules/"*.ko "${WORK}/ramdisk/lib/modules/modules.load" "${WORK}/ramdisk/lib/modules/modules.load.recovery" "${VENDOR_DIR}/vendor_ramdisk/lib/modules/"
install -m 0644 "${WORK}/ramdisk/first_stage_ramdisk/"fstab.* "${VENDOR_DIR}/vendor_ramdisk/first_stage_ramdisk/"
install -m 0644 "${WORK}/ramdisk/"ueventd.*.rc "${VENDOR_DIR}/vendor_ramdisk/"

(cd "${OUT}" && sha256sum -c ../images.sha256)
(cd "${VENDOR_DIR}/vendor_ramdisk" && sha256sum -c ../vendor_ramdisk.sha256)
(cd "${VENDOR_DIR}/dtb" && sha256sum -c ../dtb.sha256)
