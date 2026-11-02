#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

PRODUCT_VIRTUAL_AB_COMPRESSION_METHOD := lz4
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/vabc_features.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/emulated_storage.mk)

PRODUCT_SHIPPING_API_LEVEL := 34

PRODUCT_SOURCE_ROOT_DIRS += \
    -device/google/atv \
    -device/google/sdv \
    -device/google/trout \
    -hardware/qcom \
    -hardware/qcom-caf \
    -vendor/qcom
PRODUCT_EXTRA_VNDK_VERSIONS := 33
PRODUCT_USE_DYNAMIC_PARTITIONS := true
PRODUCT_BUILD_INIT_BOOT_IMAGE := true

PRODUCT_PACKAGES += \
    e2fsck.vendor_ramdisk \
    fsck.f2fs.vendor_ramdisk \
    linker.vendor_ramdisk \
    snapuserd.vendor_ramdisk

PRODUCT_PACKAGES += \
    android.hardware.boot-service.default_recovery \
    android.hardware.fastboot-service.example_recovery \
    android.hardware.health-service.example_recovery \
    fastbootd

PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/rootdir/etc/init.recovery.ums9230_6h10.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.ums9230_6h10.rc

AB_OTA_POSTINSTALL_CONFIG += \
    RUN_POSTINSTALL_system=true \
    POSTINSTALL_PATH_system=system/bin/otapreopt_script \
    FILESYSTEM_TYPE_system=erofs \
    POSTINSTALL_OPTIONAL_system=true

PRODUCT_PACKAGES += \
    FrameworksResMblu21

PRODUCT_PACKAGES += \
    checkpoint_gc \
    otapreopt_script \
    update_engine \
    update_engine_sideload \
    update_verifier

PRODUCT_CHARACTERISTICS := default
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := xhdpi

PRODUCT_SOONG_NAMESPACES += \
    $(LOCAL_PATH)

$(call inherit-product, vendor/meizu/mblu21/mblu21-vendor.mk)
