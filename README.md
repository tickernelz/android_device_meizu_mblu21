# Device tree for Meizu mBlu 21 (M416H)

LineageOS 24.0 (Android 17) device tree for the Meizu mBlu 21, model M416H.

| | |
|---|---|
| SoC | Unisoc T606 (UMS9230), board `ums9230_6h10` |
| Storage | UFS, A/B, virtual A/B with dynamic partitions (`super` 5,557,452,800 bytes, group `group_unisoc`) |
| Stock firmware | system Android 14 (U01005), vendor Android 13 (board API 33, FCM level 7, VNDK 33) |
| Kernel | stock GKI `5.15.149-android13-8` (Google build `ab12096863`) |

## Status

**Untested on hardware.** Nothing in this tree has been booted on a phone yet. Builds are published as pre-releases labelled `UNTESTED`.

## Layout

The first bring-up keeps everything the vendor owns exactly as shipped and builds only the generic side:

| Image | Source |
|---|---|
| `boot` | stock GKI kernel, re-signed |
| `vendor_boot` | stock (vendor ramdisk, first-stage modules, DTB, stock recovery), re-signed |
| `dtbo` | stock, re-signed |
| `vendor`, `odm`, `vendor_dlkm`, `system_dlkm` | stock images, unchanged |
| `init_boot`, `system`, `system_ext`, `product` | built from LineageOS source |
| `vbmeta*` | built; same chain layout and rollback index locations as stock, including the stock Unisoc key for `l_modem`, `l_ldsp`, `l_gdsp`, `pm_sys`, `l_agdsp` |

The stock images live in [android_vendor_meizu_mblu21](https://github.com/tickernelz/android_vendor_meizu_mblu21).

## Build

See [lineage_build_mblu21](https://github.com/tickernelz/lineage_build_mblu21) for the local manifest and build script.

To regenerate the prebuilt images from your own stock dump (partition dump plus `lpunpack` of `super`):

```
./extract-prebuilts.sh <partition_dump_dir> <lpunpack_super_dir>
```

The script checks every image against `vendor/meizu/mblu21/images.sha256`.

## License

Apache-2.0.
