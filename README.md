# Device tree for Meizu mBlu 21 (M416H)

PixelOS 17 (Android 17) device tree for the Meizu mBlu 21, model M416H. The `lineage-24.0` branch holds the LineageOS 24.0 tree it was ported from; vendor, kernel and kernel modules are shared.

| | |
|---|---|
| SoC | Unisoc T606 (UMS9230), board `ums9230_6h10` |
| Storage | UFS, A/B, virtual A/B with dynamic partitions (`super` 5,557,452,800 bytes, group `group_unisoc`) |
| Stock firmware | system Android 14 (U01005), vendor Android 13 (board API 33, FCM level 7, VNDK 33) |
| Kernel | stock GKI `5.15.149-android13-8` (Google build `ab12096863`) |

## Status

Tested on one M416H. Every row names the build it was tested with; a component without a row has not been tested. Rows dated before 2026-11-05 were tested on LineageOS 24.0 builds of the `lineage-24.0` branch, which uses the same vendor, kernel and kernel modules.

| Component | Result | Build, date |
|---|---|---|
| PixelOS 17: boot, SELinux enforcing, display at 90 Hz (60 Hz with Smooth display off), touch, Wi-Fi 5 GHz, Telkomsel LTE data, MTP, 49 sensors, camera opens, KernelSU LKM with `susfs_guard_lkm` | works | release [`PixelOS-17.0-20261105-1507-UNOFFICIAL-mblu21`](https://github.com/tickernelz/pixelos_build_mblu21/releases/tag/PixelOS-17.0-20261105-1507-UNOFFICIAL-mblu21), this branch at `5fc7dc0`, 2026-11-05 |
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
| Every vendor kernel module built from source (181 in `vendor_dlkm` and `vendor_boot`, the five Revo ODM modules included): ABI check 181/181 against the stock kernel, `lsmod` equal to stock, the build ID of all 179 running modules that carry one equal to the build | works | local build `zha4674-bacon9` of branch `zha4674-src` (modules `d4134ef`), 2026-11-04 |
| SELinux enforcing with `MBLU21_ENFORCING=true`, installed as an OTA: 3 reboots without a boot loop, 0 blocked accesses in `dmesg` and `logcat` counted after the smoke tests below in the same boot | works | same build, 2026-11-04 |
| Smoke tests, one check each: Wi-Fi connected on 5 GHz (5765 MHz) with ping, hotspot up, Bluetooth on, LTE in service, GNSS HAL (UMW2652), accelerometer events, light and proximity sensors listed, three cameras listed, torch through the flash driver, touch (`currency_tp`), charging with the PSC2965 CV guard (`qzhu vbat is`), Mali-G57 r41p0 with no GPU fault | works | same build, 2026-11-04 |
| SELinux enforcing by default (no build flag, `androidboot.selinux` absent from `vendor_boot`), installed as an OTA to `_b`: 0 blocked accesses in `logcat -b all` and `dmesg` on the first boot, again after the adb smoke tests in the same boot (Wi-Fi 5 GHz, hotspot up, Bluetooth on, LTE data, GNSS enabled, three cameras listed, audio output, IMS daemons running), on each of 3 reboots, and after booting Lineage Recovery with `--just_exit` and back | works | local build `zha4650-bacon4` (`ro.build.date.utc` 1793763433), 2026-11-04 |
| `cat /sys/class/input/*/name` after `rmmod spi_ilitek`, and `tinycap` with its default 1024-frame period: both used to panic the kernel | no panic: the touch input devices go away with the module, and a capture buffer larger than the DMA buffer is refused with `EINVAL` | same build, 2026-11-04 |
| VoLTE, Telkomsel SIM | **network/SIM limitation, not tested**: the modem has IMS voice on (`AT+CAVIMS: 1`, IMS-preferred voice domain, IMS APN at cid 11) but the network reports IMS voice over PS not supported (`AT+CIREP: 1,0`, `mVopsSupport = 3`), so IMS never registers. The stock firmware never showed VoLTE with this SIM either. Retest with another operator's SIM. | r7, 2026-11-03 |

Every build boots with SELinux enforcing. Builds before this change booted permissive unless `MBLU21_ENFORCING=true` was set; the rows above that name the flag were tested that way.

The first screen-off after boot logs `unbalanced disables for regulator-dummy` from `sprd_panel_unprepare()`. The stock `sprd-drm.ko` does the same: its panel probe never enables the panel supply that the bootloader left on, and unprepare disables it.

Battery deep sleep (≤ 1%/hour over 8 hours with the screen off) was not measured: the overnight run was skipped by Zhafron's decision on 2026-11-03, so there is no drain data.

Not tested with the source-built modules, because they need the phone unlocked with the owner's PIN: camera photo and video, microphone recording through the audio HAL, FBE unlock, calls, SMS, emergency call, MTP. Not tested yet on any build: Bluetooth pairing, speaker/earpiece/headset one by one, SD card, fingerprint enrollment (the sensor on the test phone is broken in hardware; the driver and HAL load).

## Layout

The kernel image is the stock Google GKI build; every kernel module the vendor ships is built from source:

| Image | Source |
|---|---|
| `boot` | stock, carrying the `Image` of Google GKI build `12096863` (`android13-5.15-2024-07`) byte for byte, re-signed |
| `vendor_boot` | built: DTB from `kernel/meizu/ums9230`, stock cmdline and bootconfig, first-stage modules built from source in the stock load order, stock fstabs and ueventd rules in the platform ramdisk, plus the PixelOS recovery with fastbootd as a separate recovery ramdisk |
| `dtbo` | built from `kernel/meizu/ums9230`; its nine overlays are byte for byte the stock ones |
| `vendor` | stock image, unchanged |
| `odm` | the stock image rebuilt by `odm/build_odm.py`: `odm_sepolicy.cil` and `odm_property_contexts` get the entries in `odm/` appended, `odm_service_contexts`, `etc/init/uniber.rc` and the [hidden camera provider](#hidden-cameras) are added, `precompiled_sepolicy` is replaced by the split policy compiled with the arguments init uses from this build's `system`, `system_ext` and `product` images, the stock vendor image and the new `odm_sepolicy.cil`, next to the `system`, `system_ext` and `product` policy hashes init compares before loading it, and `firmware/` gets the touch panel firmware (see below). Every other file keeps its stock content, owner, mode and SELinux label; the script checks this on the image it writes |
| `vendor_dlkm` | built: modules from `kernel/meizu/ums9230` and `kernel/meizu/ums9230-modules` in the stock load order |
| `system_dlkm` | built from the `zram` and `zsmalloc` modules of GKI build `12096863`, signed by Google |
| `init_boot`, `system`, `system_ext`, `product` | built from PixelOS source; `system`, `system_ext` and `product` are erofs, as on stock, because the Google apps PixelOS ships (about 2.5 GB) would not fit `group_unisoc` as ext4 |
| `vbmeta*` | built; same chain layout and rollback index locations as stock, including the stock Unisoc key for `l_modem`, `l_ldsp`, `l_gdsp`, `pm_sys`, `l_agdsp` |

All rebuilt and re-signed images use the public AOSP test key (`external/avb/test/data/testkey_rsa4096.pem`), so the device must have an unlocked bootloader to boot them. Meizu offers no unlock for this phone; the test phone was unlocked with the CVE-2022-38694 BootROM method ([hardware notes](https://github.com/tickernelz/android_kernel_meizu_mblu21/blob/main/docs/HARDWARE-2026-11-02.md#what-the-bootloader-enforces)). Its `/proc/bootconfig` reads `androidboot.flash.locked = "0"`, `androidboot.vbmeta.device_state = "unlocked"` and `androidboot.verifiedbootstate = "orange"` (2026-11-06). Read the state there: `getprop ro.boot.flash.locked` and `ro.boot.verifiedbootstate` show `1` and `green` while a root module spoofs them.

### Why `boot` keeps the stock kernel

Even unlocked, the bootloader boots only the Meizu-signed top-level `vbmeta`: a `vbmeta` with verification disabled and one signed with the AOSP test key both stopped at the logo ([table](https://github.com/tickernelz/android_kernel_meizu_mblu21/blob/main/docs/HARDWARE-2026-11-02.md#what-the-bootloader-enforces)). The stock `vbmeta` is the same on both slots (sha256 `83789a72…`, key sha1 `5cec5a31…`); it has 14 chain descriptors and no hash descriptor, and it chains `boot` and `dtbo` to Meizu's key `d46eb3be8ba9641586d7a3628c7375ebe5b7ffb6`. The stock `boot` on both slots (sha256 `3a78e139…`) is signed with that key. Measured on 2026-11-06 from a root shell:

    for p in vbmeta_a vbmeta_b boot_a boot_b; do dd if=/dev/block/by-name/$p of=/data/local/tmp/$p.img bs=1M; done
    avbtool info_image --image vbmeta_b.img
    avbtool info_image --image boot_b.img

Chain descriptors are not enforced for every partition: `vendor_boot` and `init_boot` are chained to other Meizu keys (`4fce36c7…`, `f1553ffc…`), and the test-key `vendor_boot` of this tree and a modified `init_boot` both boot ([hardware notes](https://github.com/tickernelz/android_kernel_meizu_mblu21/blob/main/docs/HARDWARE-2026-11-02.md#known-gaps)).

A `boot` built from source was tried once, on 2026-11-03: a kernel from `kernel/meizu/ums9230` with SukiSU-Ultra built in (`boot-sukisu-ultra.img`, sha256 `61d6e77d…`) in `boot_a`, every other partition stock. The phone stopped at a striped logo, did not enumerate on USB and left an empty pstore; writing the stock `boot_a` back from download mode recovered it ([hardware notes](https://github.com/tickernelz/android_kernel_meizu_mblu21/blob/main/docs/HARDWARE-2026-11-02.md#known-gaps)). Whether the bootloader refused the foreign signature on `boot` or that kernel failed before pstore was not isolated. The test that separates the two, the stock `Image` re-signed with the AOSP test key in `boot_a`, has not been run: `fastboot flash` and `fastboot boot` do not write on this unit, so every attempt and every recovery goes through `spd_dump` in download mode with the phone in hand ([write path](https://github.com/tickernelz/android_kernel_meizu_mblu21/blob/main/docs/HARDWARE-2026-11-02.md#write-path)).

The device has no `recovery` partition: recovery and fastbootd live in `vendor_boot`.

## Hidden cameras

The stock camera provider (HIDL `android.hardware.camera.provider@2.4::ICameraProvider/legacy/0`) lists cameras 0, 1 and 2 and serves 13 ids it does not list: 20, 21, 24, 30, 31, 32, 37, 38, 39, 42, 46, 47 and 55. The stock face HAL opens 30 to enroll and 31 to unlock through `libcamera2ndk_vendor`; on stock, Meizu's cameraserver adds the unlisted ids.

`camera/` builds `android.hardware.camera.provider@2.4-service.mblu21`, which `odm/build_odm.py` adds to `odm` with its init script and VINTF fragment. It registers `ICameraProvider/hidden/0`, lists the ids from 17 to 58 that `legacy/0` serves but does not list, and forwards every call to `legacy/0`. The characteristics it returns carry `SECURE_IMAGE_DATA` as their only capability, which cameraservice treats as a hidden secure camera: apps do not see these cameras, only vendor clients list them, and only clients running as the system user can open them. The provider runs in the stock `hal_camera_default` domain and exits when `legacy/0` dies, so init restarts it with the stock provider. It links against the VNDK 33 libraries of the stock vendor, whose `libc++` has no `__libcpp_verbose_abort`, so libc++ aborts are built as plain aborts.

Measured on 2026-11-06 on a PixelOS build of this tree, before the provider was part of `odm`: `ro.camera.unlisted_hidden_ids` removed with `resetprop`, the provider and the VINTF fragment bind-mounted over `/odm/bin` and `/odm/etc/vintf`, `hwservicemanager` restarted, the provider started in `hal_camera_default` with the `binder` rule from `odm/odm_sepolicy.cil` loaded. The client is a vendor NDK program running as the system user that opens each camera with a private and a YUV 960x720 stream and streams for 3 seconds:

| Setup | Ids the client lists | Cameras 30 and 31 | Cameras apps see |
|---|---|---|---|
| no hidden provider | 0, 1, 2 | open fails (`ACAMERA_ERROR_INVALID_PARAMETER`) | 3 |
| hidden provider | 0, 1, 2 and the 13 unlisted ids | open, session configured, 6 frames each | 3 |
| earlier cameraservice patch, for comparison | the same 16 | open, session configured, 6 frames each | 3 |

Face enrollment and unlock through the provider have not been tested yet: they need a build that carries it in `odm`.

## Firmware

The ROM needs stock firmware `U01005` (`meizu/meizu_mblu/MEIZU_mblu:14/U01005/1745906188:user/release-keys`, security patch 2025-04-05) on both slots. The OTA does not carry firmware: `AB_OTA_PARTITIONS` has no modem, DSP or bootloader partition, so update_engine never writes `uboot`, `sml`, `trustos`, `teecfg`, `l_modem`, `l_ldsp`, `l_gdsp`, `l_agdsp` or `pm_sys`. Before the first install, flash `U01005` and copy the active slot to the inactive one (for example with LineageOS `copy-partitions`), so a slot switch never boots older or empty firmware.

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

From a phone running a build of this tree, with root over adb (`adb root` on LineageOS, KernelSU with shell granted on PixelOS):

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

The files belong to Meizu, Unisoc and their licensors. They are extracted from a phone owned by the publisher, unmodified except for the removed AVB footers and the fstab fixup above, and are published only so that custom ROMs (PixelOS, LineageOS) can be built for the device. No license is granted for them. Rights holders who want a file removed can open an issue in the vendor repository.

## OTA

The A/B payload carries `init_boot`, `vendor_boot` and the dynamic partitions only. `boot`, `dtbo` and every `vbmeta*` are left out: the bootloader boots only the Meizu-signed `vbmeta`, and both slots already hold the stock `boot`, `dtbo` and `vbmeta` images. PixelOS ships no updater for unofficial devices: install a newer build from the PixelOS recovery with `adb sideload`, or apply it from Android with `update_engine`, keeping data. Gesture navigation is the default overlay through `androidboot.vendor.overlay.theme`; the overlay manager applies it on every boot to users who have not picked a navigation mode, and an explicit three-button choice is kept.

An update replaces `init_boot` on the other slot, so root is lost unless it is patched again before the reboot, for SukiSU Ultra or KernelSU: `ksud boot-patch -b <init_boot of the other slot> --partition init_boot`, then write the result back to that slot.

## SELinux

The stock vendor policy is compiled for platform version 33.0, so rules for stock vendor domains cannot come from `BOARD_VENDOR_SEPOLICY_DIRS` (the vendor image is stock) or `BOARD_ODM_SEPOLICY_DIRS` (it versions against the current platform). `odm/odm_sepolicy.cil` holds them in CIL against the `_33_0` attributes, like the stock `odm_sepolicy.cil`; `odm/build_odm.py` compiles it with the rest of the split policy into `/odm/etc/selinux/precompiled_sepolicy`, so init loads that file instead of running `secilc` at boot. Rules and labels for platform domains live in `sepolicy/private` on `system_ext`.

Some denied accesses are hidden with `dontaudit` instead of allowed, because nothing needs them:

- `hal_audio_default` on `audio_prop`, `rild` on `system_prop` and `surfaceflinger` on `vendor_default_prop`: vendor code looks up the `persist.audio.*` debug switches, `persist.sys.c2k.autoswitch_enabled` and `persist.vendor.gpu.fbc`. Nothing sets these properties on this build, so a denied lookup returns the same default value. Allowing the reads would break the Treble property neverallows, and the stock enforcing policy denies them too.
- `hal_graphics_composer_default` searching `/data/data`: the Mali driver looks for `/data/data/com.mali.testjava/mali_debug.config`, a debug file that does not exist.
- `hal_codec2_unisoc` searching `/data/data`: the stock H.264 decoder looks for `/data/data/com.sprd.test.videoplayer/app_decode/flag`, a switch for Unisoc's test player that is not installed. The stock policy allows the search, but `/data/data` now carries the user's MLS categories, and the platform keeps `mlsvendorcompat` empty. Video playback works with the lookup denied.
- `surfaceflinger` and apps reading the attributes of the dmabuf filesystem: the Mali driver, loaded by RenderEngine and by every app that draws camera frames with GL (Aperture through CameraX), calls `fstatfs` on buffer handles during camera preview. The kernel's dmabuf filesystem has no label in the platform or stock policy, so the stock enforcing policy denies this too; preview, photo and video work with it denied.
- `hal_face_server` reading `camera_config_prop`: `libcamera2ndk_vendor`, which the stock face HAL uses to open the hidden face camera, reads the camera configuration properties when enrollment starts. The stock enforcing policy denies the read too, and enrollment and unlock work with it denied.
- `secure_element` writing in its cache, which has no app data label: ART tries to save a runtime app image in `/data/user_de/0/com.android.se/cache/oat_primary`. The app runs without it.
- `hal_wifi_hostapd_default` on `system_prop`: the stock hostapd looks up `sys.wifi.softap.hwmode`, which nothing sets on this build. The hotspot starts with the default mode.
- `isolated_app` and `sprd_logmanager_app` looking up `content_capture_service`: neither domain may use content capture in the platform or stock vendor policy, so the lookup fails and the app runs without the feature.
- `hal_power_default` raising the scheduling priority of `platform_app` threads: the stock policy denies it as well, and the power HAL keeps working without the boost.
- `e2fs` formatting the `cache` partition: the stock vendor fstab still lists `/cache` as formattable, but this tree has no cache image and `/cache` links to `/data/cache`, so init tries to format the empty partition on every boot. The partition is labelled `cache_block_device` and the format stays denied.
- `pcc_component` (Android System Intelligence) reading `/proc/version`: the platform denies it to every app domain, and hides the same read for `gmscore_app` and `priv_app`.

`system_server` may read `custom_version_prop` and `pih_disable_prop`: PixelOS reads `net.pixelos.version` and `persist.sys.pihooks.disable.` in `system_server`, while its policy grants them only to apps and the shell.

The `misc` partition is labelled `misc_block_device` on `system_ext`, because the platform policy uses that type for `misc` (`init`, `misctrl`, `kcmdlinectrl`); `odm/odm_sepolicy.cil` gives the stock boot control HAL its access to the new label. `sysfs_mblu21_7sreset` is a public `system_ext` type with a 33.0 mapping, so the odm policy refers to it like any other platform type.

`hal_camera_default` may make binder calls to itself: the [hidden camera provider](#hidden-cameras) runs in that stock domain and forwards every call to `legacy/0`, which runs in it too.

The `kernel` domain denials for `/metadata/ota/state` and `/sys/firmware/devicetree/base/firmware/android` happen while init finishes the snapuserd transition, after the policy is loaded and before enforcing is switched on, so they are always logged with `permissive=1` and block nothing.

`artd` reading a symlink in the data directory of an app installed by the user (seen with the Google app's `core_annotator.fb` during background dexopt) stays logged: the platform policy lets `artd` follow symlinks only in GMS data on purpose, so this is AOSP behaviour on every device, not something this tree adds or should hide.

## IMS

The stock IMS stack lives on `system_ext` and depends on Unisoc additions to the framework. `extract-files.py` extracts it with the other blobs (the `IMS` sections of `proprietary-files.txt`), and blob fixups rebuild the two apps:

- `ims.apk` (`com.spreadtrum.ims`) and `radio_interactor_service.apk` get the stock boot jars they need merged in as extra dex files, and their calls into Unisoc-only telephony APIs (`TelephonyMetrics`, `ServiceStateTracker.startUpdateState`) removed. The build signs both with the platform key so they keep `android.uid.phone`.
- `ims_bridged`, `srmi_proxyd` and their libraries are copied unchanged.

`sepolicy/private/compat/33.0/33.0.cil` maps `ims_bridged`, `srmi_proxyd` and `fwk_srmi_service` onto the `_33_0` attributes the stock vendor policy already grants, as the stock system_ext mapping does.

## Build

See [pixelos_build_mblu21](https://github.com/tickernelz/pixelos_build_mblu21) for the local manifest, build script and install steps. The build runs `breakfast mblu21` (product `custom_mblu21`) and `m pixelos`.

## Credits

- [LineageOS](https://github.com/LineageOS): the tree layout, `extract-files.py` (extract-utils) and the SPDX headers follow LineageOS device trees; their headers are kept.
- [arriRgb31/device_realme_rmx3760](https://github.com/arriRgb31/device_realme_rmx3760) by Ari Lukman Yusuf, the LineageOS tree for the realme C53 on the same UMS9230: read as a reference for the board layout during the first bring-up. No file was copied. The lines both trees share are standard `BoardConfig.mk` flags such as `BOARD_BOOT_HEADER_VERSION := 4` set from the stock images, one `PRODUCT_SOONG_NAMESPACES` line in `device.mk`, the `metadata`, `misc` and `userdata` entries both trees take from the stock Unisoc fstab, and generic init lines such as `class main`.
- Kernel and kernel modules: Motorola's GPL releases ([kernel-sprd](https://github.com/MotorolaMobilityLLC/kernel-sprd) and the `sprd-kernel-modules-*` repositories), [realme-kernel-opensource](https://github.com/realme-kernel-opensource) and [mer-hybris/s19mps-kernel](https://github.com/mer-hybris/s19mps-kernel). Each import commit in the kernel repositories names the source commit it came from.
- Proprietary files: the Meizu stock firmware U01005, extracted by `extract-files.py`.

## History and AI assistance

The bring-up history is on `lineage-24.0`; `seventeen` continues it with the PixelOS port. Most commits in this tree and in [pixelos_build_mblu21](https://github.com/tickernelz/pixelos_build_mblu21), and the mblu21 commits on top of the imported kernel sources (8 in `android_kernel_meizu_ums9230`, the import and fix commits in `android_kernel_meizu_ums9230-modules`), were written with AI coding assistants (LLM agents) at Zhafron's direction and tested on his phone as listed under [Status](#status). The rest of the kernel repositories is Linux, Google, Motorola, realme and mer-hybris code. Commits without an `Assisted-by: LLM` trailer are not human-only: before 2026-11-06 only 30 of the 74 commits on `lineage-24.0` and none of the 7 PixelOS commits on `seventeen` carry it.

## License

Apache-2.0.
