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
| A/B OTA through the LineageOS Updater, data kept, root re-patched with `ksud boot-patch` before the reboot | works: r3 to `_b`, r4 to `_a`, r5 to `_b`, r6 to `_a` | pre-releases r3-r6 (branch `zha4555-volte`), 2026-11-03 |
| Unisoc IMS stack (`com.spreadtrum.ims` bound as MMTEL, `ims_bridged`, `srmi_proxyd`, RadioInteractor `irit`) under SELinux enforcing, no denials, no crashes | runs | pre-release r6, 2026-11-03 |
| VoLTE registration, Telkomsel | **not registered**: the network reports IMS voice over PS not supported (`LteVopsSupportInfo mVopsSupport = 3`), on the stock firmware as well | r6 and stock U01005, 2026-11-03 |

`79d312d` and `0d92969` are not on `lineage-24.0` yet, so a build of this branch still boots with SELinux permissive and Volume Down can reset the phone.

Not tested yet: Bluetooth pairing, battery deep sleep, speaker/earpiece/headset one by one, camera flash, fingerprint (the sensor on the test phone is broken in hardware).

## Layout

The first bring-up keeps everything the vendor owns exactly as shipped and builds only the generic side:

| Image | Source |
|---|---|
| `boot` | stock GKI kernel, re-signed |
| `vendor_boot` | built: stock DTB, cmdline and bootconfig, stock first-stage modules, fstabs and ueventd rules in the platform ramdisk, plus Lineage Recovery with fastbootd as a separate recovery ramdisk |
| `dtbo` | stock, re-signed |
| `vendor`, `odm`, `vendor_dlkm`, `system_dlkm` | stock images, unchanged |
| `init_boot`, `system`, `system_ext`, `product` | built from LineageOS source |
| `vbmeta*` | built; same chain layout and rollback index locations as stock, including the stock Unisoc key for `l_modem`, `l_ldsp`, `l_gdsp`, `pm_sys`, `l_agdsp` |

All rebuilt and re-signed images use the public AOSP test key (`external/avb/test/data/testkey_rsa4096.pem`), so the device must have an unlocked bootloader to boot them.

The device has no `recovery` partition: recovery and fastbootd live in `vendor_boot`.

The stock images live in [android_vendor_meizu_mblu21](https://github.com/tickernelz/android_vendor_meizu_mblu21).

## OTA

The A/B payload carries `init_boot`, `vendor_boot` and the dynamic partitions only. `boot`, `dtbo` and every `vbmeta*` are left out: the bootloader boots only the Meizu-signed `vbmeta`, and both slots already hold the stock `boot`, `dtbo` and `vbmeta` images. The LineageOS Updater reads `updater/mblu21.json` from [lineage_build_mblu21](https://github.com/tickernelz/lineage_build_mblu21) (`lineage.updater.uri` in `system.prop`).

An update replaces `init_boot` on the other slot, so root is lost unless it is patched again before the reboot, for SukiSU Ultra or KernelSU: `ksud boot-patch -b <init_boot of the other slot> --partition init_boot`, then write the result back to that slot.

## IMS

The stock IMS stack lives on `system_ext` and depends on Unisoc additions to the framework. `extract-ims.py <extracted_partitions_dir>` regenerates it into the vendor tree from the stock U01005 partitions, checked against `ims-inputs.sha256`:

- `ims.apk` (`com.spreadtrum.ims`) and `radio_interactor_service.apk` get the stock boot jars they need merged in as extra dex files, and their calls into Unisoc-only telephony APIs (`TelephonyMetrics`, `ServiceStateTracker.startUpdateState`) removed. The build signs both with the platform key so they keep `android.uid.phone`.
- `ims_bridged`, `srmi_proxyd` and their libraries are copied unchanged.

`sepolicy/private/compat/33.0/33.0.cil` maps `ims_bridged`, `srmi_proxyd` and `fwk_srmi_service` onto the `_33_0` attributes the stock vendor policy already grants, as the stock system_ext mapping does.

## Build

See [lineage_build_mblu21](https://github.com/tickernelz/lineage_build_mblu21) for the local manifest and build script.

To regenerate the prebuilt images from your own stock dump (partition dump plus `lpunpack` of `super`):

```
./extract-prebuilts.sh <partition_dump_dir> <lpunpack_super_dir>
```

The script checks every image against `vendor/meizu/mblu21/images.sha256`, and the vendor ramdisk files and DTB taken from the stock `vendor_boot` against `vendor_ramdisk.sha256` and `dtb.sha256`.

## License

Apache-2.0.
