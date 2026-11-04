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
| Emergency call, GPS, MTP, USB tethering | works (manual test by Zhafron) | 2026-11-03 |
| A/B OTA through the LineageOS Updater, data kept, root re-patched with `ksud boot-patch` before the reboot | works: r3 to `_b`, r4 to `_a`, r5 to `_b`, r6 to `_a`, r7 to `_b` | pre-releases r3-r7 (branch `zha4555-volte`), 2026-11-03 |
| Unisoc IMS stack (`com.spreadtrum.ims` bound as MMTEL, `ims_bridged`, `srmi_proxyd`, RadioInteractor `irit`): 0 SELinux denials and 0 crashes for these domains after 17 minutes | runs | pre-release r7, 2026-11-03 |
| Every vendor kernel module built from source (181 in `vendor_dlkm` and `vendor_boot`, the five Revo ODM modules included): ABI check 181/181 against the stock kernel, `lsmod` equal to stock, the build ID of all 179 running modules that carry one equal to the build | works | local build `zha4674-bacon7` of branch `zha4674-src` (modules `1f11b6b`), 2026-11-04 |
| SELinux enforcing with `MBLU21_ENFORCING=true`: 3 reboots without a boot loop, 0 blocked accesses after each boot and after the smoke tests below | works | same build, 2026-11-04 |
| Smoke tests, one check each: Wi-Fi connected on 5 GHz (5765 MHz) with ping, hotspot up, Bluetooth on, LTE in service, GNSS HAL (UMW2652), accelerometer events, light and proximity sensors listed, three cameras listed, torch through the flash driver, touch (`currency_tp`), charging with the PSC2965 CV guard (`qzhu vbat is`), Mali-G57 r41p0 with no GPU fault | works | same build, 2026-11-04 |
| `cat /sys/class/input/*/name` after `rmmod spi_ilitek`, and `tinycap` with its default 1024-frame period: both used to panic the kernel | no panic: the touch input devices go away with the module, and the oversized capture buffer is refused with `EINVAL` | same build, 2026-11-04 |
| VoLTE, Telkomsel SIM | **network/SIM limitation, not tested**: the modem has IMS voice on (`AT+CAVIMS: 1`, IMS-preferred voice domain, IMS APN at cid 11) but the network reports IMS voice over PS not supported (`AT+CIREP: 1,0`, `mVopsSupport = 3`), so IMS never registers. The stock firmware never showed VoLTE with this SIM either. Retest with another operator's SIM. | r7, 2026-11-03 |

A build boots with SELinux permissive unless `MBLU21_ENFORCING=true` is set in the build environment; enforcing becomes the default once an enforcing build logs no blocked access through the full test matrix.

Battery deep sleep (≤ 1%/hour over 8 hours with the screen off) was not measured: the overnight run was skipped by Zhafron's decision on 2026-11-03, so there is no drain data.

Not tested with the source-built modules, because they need the phone unlocked with the owner's PIN: camera photo and video, microphone recording through the audio HAL, FBE unlock, calls, SMS, emergency call, MTP. Not tested yet on any build: Bluetooth pairing, speaker/earpiece/headset one by one, SD card, fingerprint enrollment (the sensor on the test phone is broken in hardware; the driver and HAL load).

## Layout

The kernel image is the stock Google GKI build; every kernel module the vendor ships is built from source:

| Image | Source |
|---|---|
| `boot` | stock, carrying the `Image` of Google GKI build `12096863` (`android13-5.15-2024-07`) byte for byte, re-signed |
| `vendor_boot` | built: DTB from `kernel/meizu/ums9230`, stock cmdline and bootconfig, first-stage modules built from source in the stock load order, stock fstabs and ueventd rules in the platform ramdisk, plus Lineage Recovery with fastbootd as a separate recovery ramdisk |
| `dtbo` | built from `kernel/meizu/ums9230`; its nine overlays are byte for byte the stock ones |
| `vendor` | stock image, unchanged |
| `odm` | the stock image rebuilt by `odm/build_odm.py` with three changes: `odm_sepolicy.cil` gets the rules in `odm/odm_sepolicy.cil` appended, the stale `precompiled_sepolicy` is removed, and `firmware/` gets the touch panel firmware (see below). Every other file keeps its stock content, owner, mode and SELinux label; the script checks this on the image it writes |
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
| `proprietary/vendor_dlkm/` | the stock Revo ODM modules, never installed: the stock `spi_ilitek.ko` and `focaltech_spi_v4_1.ko` carry the touch panel firmware built in, and `odm/build_odm.py` copies it out to `/odm/firmware/ILITEK_FW_DEF.ili` and `/odm/firmware/focaltech_ts_fw_.bin`, where the source-built drivers load it with `request_firmware()` |
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

`<dump_dir>` holds partition images named `<partition>_a.bin` or `<partition>_a.img` (an `spd_dump r all_lite` dump, or the assets of the [`mblu21-stock-U01005-20261031`](https://github.com/tickernelz/android_stock_meizu_mblu21/releases/tag/mblu21-stock-U01005-20261031) release), or `<partition>.img`, with `super.bin`/`super.img` in place of the logical partition images. extract-utils writes a file whose SHA-1 differs from its pin and goes on, so `extract-files.py` checks every pinned file in the vendor tree afterwards (against its fixup hash when it has one) and exits 1 with the list of files that are missing or do not match. Once the vendor repository is checked out, only `boot_a.bin` and `vendor_a.img` are needed: the other pinned files are kept from the checkout.

`./setup-makefiles.py` regenerates the vendor makefiles from the lists.

The files belong to Meizu, Unisoc and their licensors. They are extracted from a phone owned by the publisher, unmodified except for the removed AVB footers and the fstab fixup above, and are published only so that LineageOS can be built for the device. No license is granted for them. Rights holders who want a file removed can open an issue in the vendor repository.

## OTA

The A/B payload carries `init_boot`, `vendor_boot` and the dynamic partitions only. `boot`, `dtbo` and every `vbmeta*` are left out: the bootloader boots only the Meizu-signed `vbmeta`, and both slots already hold the stock `boot`, `dtbo` and `vbmeta` images. The LineageOS Updater reads `updater/mblu21.json` from [lineage_build_mblu21](https://github.com/tickernelz/lineage_build_mblu21) (`lineage.updater.uri` in `system.prop`).

An update replaces `init_boot` on the other slot, so root is lost unless it is patched again before the reboot, for SukiSU Ultra or KernelSU: `ksud boot-patch -b <init_boot of the other slot> --partition init_boot`, then write the result back to that slot.

## SELinux

The stock vendor policy is compiled for platform version 33.0, so rules for stock vendor domains cannot come from `BOARD_VENDOR_SEPOLICY_DIRS` (the vendor image is stock) or `BOARD_ODM_SEPOLICY_DIRS` (it versions against the current platform). `odm/odm_sepolicy.cil` holds them in CIL against the `_33_0` attributes, like the stock `odm_sepolicy.cil`; init compiles it with the rest of the split policy at boot. Rules and labels for platform domains live in `sepolicy/private` on `system_ext`.

Some denied accesses are hidden with `dontaudit` instead of allowed, because nothing needs them:

- `hal_audio_default` on `audio_prop`, `rild` on `system_prop` and `surfaceflinger` on `vendor_default_prop`: vendor code looks up the `persist.audio.*` debug switches, `persist.sys.c2k.autoswitch_enabled` and `persist.vendor.gpu.fbc`. Nothing sets these properties on this build, so a denied lookup returns the same default value. Allowing the reads would break the Treble property neverallows, and the stock enforcing policy denies them too.
- `hal_graphics_composer_default` searching `/data/data`: the Mali driver looks for `/data/data/com.mali.testjava/mali_debug.config`, a debug file that does not exist.
- `secure_element` writing in its cache, which has no app data label: ART tries to save a runtime app image in `/data/user_de/0/com.android.se/cache/oat_primary`. The app runs without it.
- `hal_wifi_hostapd_default` on `system_prop`: the stock hostapd looks up `sys.wifi.softap.hwmode`, which nothing sets on this build. The hotspot starts with the default mode.
- `isolated_app` and `sprd_logmanager_app` looking up `content_capture_service`: neither domain may use content capture in the platform or stock vendor policy, so the lookup fails and the app runs without the feature.
- `hal_power_default` raising the scheduling priority of `platform_app` threads: the stock policy denies it as well, and the power HAL keeps working without the boost.

The `misc` partition is labelled `misc_block_device` on `system_ext`, because the platform policy uses that type for `misc` (`init`, `misctrl`, `kcmdlinectrl`); `odm/odm_sepolicy.cil` gives the stock boot control HAL its access to the new label. `sysfs_mblu21_7sreset` is a public `system_ext` type with a 33.0 mapping, so the odm policy refers to it like any other platform type.

The `kernel` domain denials for `/metadata/ota/state` and `/sys/firmware/devicetree/base/firmware/android` happen while init finishes the snapuserd transition, after the policy is loaded and before enforcing is switched on, so they are always logged with `permissive=1` and block nothing.

## IMS

The stock IMS stack lives on `system_ext` and depends on Unisoc additions to the framework. `extract-files.py` extracts it with the other blobs (the `IMS` sections of `proprietary-files.txt`), and blob fixups rebuild the two apps:

- `ims.apk` (`com.spreadtrum.ims`) and `radio_interactor_service.apk` get the stock boot jars they need merged in as extra dex files, and their calls into Unisoc-only telephony APIs (`TelephonyMetrics`, `ServiceStateTracker.startUpdateState`) removed. The build signs both with the platform key so they keep `android.uid.phone`.
- `ims_bridged`, `srmi_proxyd` and their libraries are copied unchanged.

`sepolicy/private/compat/33.0/33.0.cil` maps `ims_bridged`, `srmi_proxyd` and `fwk_srmi_service` onto the `_33_0` attributes the stock vendor policy already grants, as the stock system_ext mapping does.

## Build

See [lineage_build_mblu21](https://github.com/tickernelz/lineage_build_mblu21) for the local manifest and build script.

## License

Apache-2.0.
