# keys

No signing key is stored here. Every AVB image this tree builds is signed with the **public AOSP test key** `external/avb/test/data/testkey_rsa4096.pem` from the LineageOS source checkout (see `BoardConfig.mk`). It is **not a release key**: anyone can sign with it, so the phone needs an unlocked bootloader.

This directory only holds the optional, gitignored `adb_keys` for `MBLU21_ADB_KEYS` (see [BRINGUP.md](../BRINGUP.md)). Do not commit a private key here.
