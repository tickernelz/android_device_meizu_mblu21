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

## SELinux

SELinux is enforcing on every build; `vendor_boot` carries no
`androidboot.selinux`. Rules for the stock vendor domains are appended to the
stock `odm_sepolicy.cil` by `odm/build_odm.py`, and rules for platform domains
live in `sepolicy/private` on `system_ext`; README.md describes both and lists
each `dontaudit` with the reason the access is not needed.

## Flashing the boot chain

- `fastboot flash` works for `misc` only; `vendor_boot` is refused
  (`Write img fail!`).
- `vendor_boot`, `init_boot` and `super` are written from a running
  recovery with `dd` to `/dev/block/by-name/<partition>`, or over Unisoc
  download mode with `spd_dump`.
- Writing `super` from a running Android kills the system mid-write; write it
  from recovery or download mode.
