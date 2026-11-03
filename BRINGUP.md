# Bring-up status: LineageOS 24.0 (Android 17)

Verified on the device on 2026-11-02. Numbers below come from the running
system, not from a build log.

## What boots

| Element | Source | Note |
|---|---|---|
| `boot` | stock Meizu | GKI 5.15.149-android13, never replaced |
| `init_boot` | built | Android 17 generic ramdisk |
| `vendor_boot` | built | stock DTB, stock vendor ramdisk, Lineage Recovery |
| `dtbo`, `vbmeta` | stock Meizu | never replaced |
| `super` | built | system, system_ext, product built; vendor, odm, vendor_dlkm, system_dlkm byte-identical to stock |

Runtime evidence:

```
ro.build.version.release = 17
ro.lineage.build.version = 24.0
ro.boot.mode             = normal
sys.boot_completed       = 1
init.svc.surfaceflinger  = running
ro.crypto.state          = encrypted
```

## Why verification is off

The stock vbmeta chain partitions carry no slot suffix (`vbmeta_system`,
`vbmeta_vendor`, ...), but init resolves them as `vbmeta_system_a` when
`slotselect` is set. Any `avb=` entry therefore fails:

```
init: [libfs_avb] Device path not found: /dev/block/by-name/vbmeta_system_a
init: [libfs_avb] avb_slot_verify failed, result: 2
init: Failed to mount required partitions early ...
init: InitFatalReboot: signal 6
```

The fatal path reboots to the bootloader, which looks like a boot loop. Every
`avb=` flag is removed from the first-stage fstab and from
`rootdir/etc/recovery.fstab`. That drops dm-verity for every logical
partition, `vendor`/`odm`/`vendor_dlkm`/`system_dlkm` included; their images
stay byte-identical to stock, so only verification, not content, changed.

The Meizu vbmeta cannot be replaced: a test-key vbmeta, with or without a valid
signature, stops at the logo. That is why verification is disabled instead of
re-keyed.

## Bring-up opt-in

A distribution build uses the stock cmdline. Two make variables switch the
debug behaviour on:

- `MBLU21_BRINGUP=1` adds `ignore_loglevel` to `BOARD_KERNEL_CMDLINE` and
  `androidboot.init_fatal_reboot_target=recovery` to `BOARD_BOOTCONFIG`, so
  every kernel and init message reaches the ttyS1 console and a fatal init
  error lands in recovery instead of the bootloader.
- `MBLU21_ADB_KEYS=device/meizu/mblu21/keys/adb_keys` copies that public key
  into the recovery ramdisk. Soong only accepts a path inside the source tree;
  `keys/adb_keys` is gitignored. Nothing is copied when the variable is empty,
  which is the default.

`androidboot.selinux=permissive` is still unconditional: SELinux stays
permissive until enforcing can cover the vendor domains this platform touches.
A fresh enforcing boot blocks 162 accesses (vendor_init property sets from the
stock vendor/build.prop, audio_prop reads, composer graphics props, power HAL
sys_nice, rild system_prop, system_suspend wakeup sysfs), and those denials come
from vendor/ODM domains. `vendor.img` and `odm.img` are the stock prebuilt
images here, so `BOARD_VENDOR_SEPOLICY_DIRS` is staged but never packaged: the
policy has to live in the system_ext private directory to reach Android.

Measured cost of `ignore_loglevel` here: the console takes 29 KB/s during the
20-30 s boot bucket (634 KB between 8 s and 50 s) against 249-282 B/s idle,
because the UART FIFO drains one character per spinlock iteration. Shipping
builds must not carry it.

## Flashing the boot chain

- `fastboot flash` works for `misc` only; `vendor_boot` is refused
  (`Write img fail!`).
- `vendor_boot`, `init_boot` and `super` are written from a running
  recovery with `dd` to `/dev/block/by-name/<partition>`, or over Unisoc
  download mode with `spd_dump`.
- Writing `super` from a running Android kills the system mid-write; write it
  from recovery or download mode.

## Recovery adb

`MBLU21_ADB_KEYS=<file>` puts that public key at
`/product/etc/security/adb_keys`, the target of the `/adb_keys` symlink, so
`adb` in recovery is authorized without the on-screen prompt. The variable is
empty by default, so a distribution build carries no key. `keys/.gitignore`
covers `adb_keys` and `*_adb_keys` inside `keys/`; `git check-ignore -v
keys/adb_keys` exits 0.

Before uploading a release, confirm the images carry no key:

```
python3 system/tools/mkbootimg/unpack_bootimg.py --boot_img vendor_boot.img --out d
for f in d/vendor_ramdisk*; do lz4 -dc "$f" | cpio -t; done | grep -c '^product/etc/security/adb_keys$'
```

The count must be 0. The `adb_keys -> /product/etc/security/adb_keys`
symlink at the ramdisk root is always present and holds no key.
