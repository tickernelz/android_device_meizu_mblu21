# Device tree for Meizu mBlu 21 (M416H)

LineageOS 24.0 (Android 17) device tree for the Meizu mBlu 21, model M416H.

| | |
|---|---|
| SoC | Unisoc T606 (UMS9230), board `ums9230_6h10` |
| Storage | UFS, A/B, virtual A/B with dynamic partitions (`super` 5,557,452,800 bytes, group `group_unisoc`) |
| Stock firmware | system Android 14 (U01005), vendor Android 13 (board API 33, FCM level 7, VNDK 33) |
| Kernel | stock GKI `5.15.149-android13-8` (Google build `ab12096863`) |

## Status

Tested on one M416H. Every row names the build it was tested with; a component without a row has not been tested.

| Component | Result | Build, date |
|---|---|---|
| Boot, display, touch, FBE unlock with a PIN, USB adb, charging | works | release [`lineage-24.0-20261103-UNOFFICIAL-mblu21`](https://github.com/tickernelz/lineage_build_mblu21/releases/tag/lineage-24.0-20261103-UNOFFICIAL-mblu21), this branch at `7dd4b55`, 2026-11-03 |
| Wi-Fi (5 GHz), Telkomsel LTE data | works | same release, 2026-11-03 |
| Rear and front camera: photo, video with audio | works | same release, 2026-11-03 |
| Microphone recording | works | same release, 2026-11-03 |
| SELinux enforcing: boot, Wi-Fi, LTE, Bluetooth on, camera, no crashes | works | local build with `79d312d` (branch `zha4374-selinux-voldown`), 2026-11-03 |
| Voice calls (two-way audio) and SMS send/receive, Telkomsel | works | local build with `79d312d`, 2026-11-03 |
| Volume Down in Android and Lineage Recovery without resetting the phone | works | local build with `0d92969` (branch `zha4374-selinux-voldown`), 2026-11-03 |

`79d312d` and `0d92969` are not on `lineage-24.0` yet, so a build of this branch still boots with SELinux permissive and Volume Down can reset the phone.

Not tested yet: Bluetooth pairing, VoLTE, outdoor GPS fix, battery deep sleep, OTA, MTP, speaker/earpiece/headset one by one, camera flash, fingerprint (the sensor on the test phone is broken in hardware).

## Layout

The kernel image is the stock Google GKI build; every kernel module the vendor ships is built from source except five Revo ODM modules:

| Image | Source |
|---|---|
| `boot` | stock, carrying the `Image` of Google GKI build `12096863` (`android13-5.15-2024-07`) byte for byte, re-signed |
| `vendor_boot` | built: DTB from `kernel/meizu/ums9230`, stock cmdline and bootconfig, first-stage modules built from source in the stock load order, stock fstabs and ueventd rules in the platform ramdisk, plus Lineage Recovery with fastbootd as a separate recovery ramdisk |
| `dtbo` | built from `kernel/meizu/ums9230`; its nine overlays are byte for byte the stock ones |
| `vendor`, `odm` | stock images, unchanged |
| `vendor_dlkm` | built: modules from `kernel/meizu/ums9230` and `kernel/meizu/ums9230-modules` in the stock load order |
| `system_dlkm` | built from the `zram` and `zsmalloc` modules of GKI build `12096863`, signed by Google |
| `init_boot`, `system`, `system_ext`, `product` | built from LineageOS source |
| `vbmeta*` | built; same chain layout and rollback index locations as stock, including the stock Unisoc key for `l_modem`, `l_ldsp`, `l_gdsp`, `pm_sys`, `l_agdsp` |

All rebuilt and re-signed images use the public AOSP test key (`external/avb/test/data/testkey_rsa4096.pem`), so the device must have an unlocked bootloader to boot them.

The device has no `recovery` partition: recovery and fastbootd live in `vendor_boot`.

## Firmware

LineageOS needs stock firmware `U01005` (`meizu/meizu_mblu/MEIZU_mblu:14/U01005/1745906188:user/release-keys`, security patch 2025-04-05) on both slots. The OTA does not carry firmware: `AB_OTA_PARTITIONS` has no modem, DSP or bootloader partition, so update_engine never writes `uboot`, `sml`, `trustos`, `teecfg`, `l_modem`, `l_ldsp`, `l_gdsp`, `l_agdsp` or `pm_sys`. Before the first LineageOS install, flash `U01005` and copy the active slot to the inactive one with LineageOS `copy-partitions`, so a slot switch never boots older or empty firmware.

The modem and DSP images still go into the target files as radio files, because `vbmeta` chains them with the stock Unisoc key and `add_img_to_target_files` opens every chained image to compute the `vbmeta` digest.

## Proprietary files

Every proprietary file is listed in `proprietary-files.txt` and `proprietary-firmware.txt` with its SHA-1, and comes from firmware `U01005`:

| Path in `vendor/meizu/mblu21` | Content |
|---|---|
| `proprietary/images/` | stock `boot` without its AVB footer, stock `vendor`, `odm` |
| `proprietary/vendor_ramdisk/` | fstabs and ueventd rules from the platform ramdisk of `vendor_boot`; the `fstab.ums9230_6h10` fixup removes its `avb` flags |
| `proprietary/system_dlkm/` | `zram.ko` and `zsmalloc.ko`, identical to the `system_dlkm` staging archive of GKI build `12096863` on ci.android.com |
| `proprietary/vendor_dlkm/` | the Revo ODM modules `flash_ic_gpio`, `focaltech_spi_v4_1`, `psc2965-charger`, `revofp_silead`, `spi_ilitek`, which have no published source; `modules/prebuilt` adds them to the kernel module build so they keep their stock place in `modules.load` |
| `proprietary/avb/unisoc_modem.avbpubkey` | public key in the AVB footer of `l_modem`, the key `vbmeta` uses for `l_modem`, `l_ldsp`, `l_gdsp`, `pm_sys`, `l_agdsp` |
| `radio/` | stock signed `l_modem`, `l_ldsp`, `l_gdsp`, `l_agdsp`, `pm_sys` |

`proprietary/images/vendor.img` (765,497,344 bytes) is over the GitHub file size limit, so it is gitignored in the vendor repository and comes from `extract-files.py`.

From a phone running LineageOS, with rooted debugging enabled:

```
./extract-files.py
```

The script pulls `boot`, `vendor_boot` and the modem and DSP partitions from `/dev/block/by-name`, and `vendor`, `odm`, `vendor_dlkm`, `system_dlkm` from `/dev/block/mapper`, all of the active slot, then extracts them like a stock dump.

From a stock dump:

```
./extract-files.py <dump_dir>
```

`<dump_dir>` holds partition images named `<partition>_a.bin` or `<partition>_a.img` (an `spd_dump r all_lite` dump, or the assets of the [`mblu21-stock-U01005-20261031`](https://github.com/tickernelz/android_stock_meizu_mblu21/releases/tag/mblu21-stock-U01005-20261031) release), or `<partition>.img`, with `super.bin`/`super.img` in place of the logical partition images. A file whose SHA-1 differs from its pin does not stop the extraction: `extract-files.py` prints `... but expected hash ...` for it, writes it anyway and exits 0, so check the output for that line. Once the vendor repository is checked out, only `boot_a.bin` and `vendor_a.img` are needed: the other pinned files are kept from the checkout.

`./setup-makefiles.py` regenerates the vendor makefiles from the lists.

The files belong to Meizu, Unisoc and their licensors. They are extracted from a phone owned by the publisher, unmodified except for the removed AVB footers and the fstab fixup above, and are published only so that LineageOS can be built for the device. No license is granted for them. Rights holders who want a file removed can open an issue in the vendor repository.

## Build

See [lineage_build_mblu21](https://github.com/tickernelz/lineage_build_mblu21) for the local manifest and build script.

## License

Apache-2.0.
