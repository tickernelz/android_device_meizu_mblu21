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
OUT="${VENDOR_DIR}/images"

mkdir -p "${OUT}"

for part in boot vendor_boot dtbo; do
    install -m 0644 "${DUMP}/${part}_a.bin" "${OUT}/${part}.img"
    python3 "${AVBTOOL}" erase_footer --image "${OUT}/${part}.img"
done

for part in vendor odm vendor_dlkm system_dlkm; do
    install -m 0644 "${SUPER}/${part}_a.img" "${OUT}/${part}.img"
done

cd "${OUT}"
sha256sum -c ../images.sha256
