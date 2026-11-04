#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/meizu/mblu21
VENDOR_PATH := vendor/meizu/mblu21

TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-2a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := cortex-a75

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-2a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_2ND_CPU_VARIANT_RUNTIME := cortex-a55

TARGET_BOARD_PLATFORM := ums9230
TARGET_BOOTLOADER_BOARD_NAME := ums9230_6h10
TARGET_NO_BOOTLOADER := true
TARGET_NO_RADIOIMAGE := true

AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    init_boot \
    odm \
    product \
    system \
    system_dlkm \
    system_ext \
    vendor \
    vendor_boot \
    vendor_dlkm

BOARD_BOOT_HEADER_VERSION := 4
BOARD_INIT_BOOT_HEADER_VERSION := 4
BOARD_KERNEL_PAGESIZE := 4096
BOARD_RAMDISK_USE_LZ4 := true
BOARD_KERNEL_IMAGE_NAME := Image
KERNEL_LTO := thin
TARGET_KERNEL_CLANG_VERSION := r547379
TARGET_KERNEL_CONFIG := gki_defconfig vendor/sprd_gki_sharkl6.config vendor/mblu21.config
TARGET_KERNEL_SOURCE := kernel/meizu/ums9230
TARGET_KERNEL_ADDITIONAL_FLAGS := \
    CONFIG_DTB_ORIGINAL=y \
    DTC_FLAGS=-@ \
    BSP_BOARD_ARCH=arm64 \
    BSP_BOARD_CAMERA_MODULE_CPP_VERSION=lite_r6p0 \
    BSP_BOARD_CAMERA_MODULE_CSI_VERSION=receiver_r3p1 \
    BSP_BOARD_CAMERA_MODULE_DVFS=qogirl6 \
    BSP_BOARD_CAMERA_MODULE_ISP_ADAPT_VERSION=qogirl6 \
    BSP_BOARD_CAMERA_MODULE_ISP_VERSION=isp2.6 \
    BSP_BOARD_NAME=ums9230_6h10 \
    BSP_BUILD_ANDROID_OS=y \
    BSP_BUILD_DT_OVERLAY=y \
    BSP_BUILD_FAMILY=qogirl6 \
    BSP_BUILD_VARIANT=user \
    BSP_KERNEL_BUILD_CONFIG=build.config.gki.aarch64.ums9230_ \
    BSP_KERNEL_VERSION=kernel5.15 \
    BSP_MODULE_DISP_VERSION=ums9230 \
    MALI_PLATFORM_NAME=qogirl6 \
    TARGET_BOARD_PLATFORM=ums9230 \
    TARGET_BUILD_VARIANT=user \
    'BSP_KERNEL_PATH=$$(KERNEL_SRC)' \
    'BSP_MODULES_OUT=$$(OUT_DIR)/bsp_modules'
TARGET_KERNEL_EXT_MODULE_ROOT := kernel/meizu/ums9230-modules
TARGET_KERNEL_EXT_MODULES := \
    kernel5.15/gpu/natt \
    kernel5.15/microarray \
    kernel5.15/npu/vdsp \
    common/camera/power \
    common/camera/flash/flash_drv \
    common/camera/sensor \
    kernel5.15/dmabufheap \
    common/camera/cam_sys \
    common/camera/cpp \
    common/camera/flash/ocp8137 \
    common/camera/flash/ocp81375 \
    common/camera/mmdvfs \
    kernel5.15/wcn/bsp/unisoc_wcn_bsp \
    kernel5.15/wcn/fm/driver \
    kernel5.15/wcn/bluetooth/driver \
    common/io/block \
    common/io/iowait \
    kernel5.15/wcn/gnss/unisoc_gnss/gnss_common_ctl \
    kernel5.15/wcn/gnss/unisoc_gnss/gnss_dbg \
    kernel5.15/wcn/gnss/unisoc_gnss/gnss_pmnotify_ctl \
    kernel5.15/wcn/wlan/wlan_combo \
    kernel5.15/display/gsp \
    kernel5.15/display/dispc \
    kernel5.15/video/sprd-vpu \
    kernel5.15/video/sprd-vsp-power \
    kernel5.15/video/sprd-jpg \
    kernel5.15/audio/sprd_audio/audiomem \
    kernel5.15/audio/sprd_audio/agdsp_pd \
    kernel5.15/audio/sprd_audio/audiosipc \
    kernel5.15/audio/sprd_audio/audiodvfs \
    kernel5.15/audio/sprd_audio/audio_pipe \
    kernel5.15/audio/sprd_audio/audiodspdump \
    kernel5.15/audio/sprd_audio/audiocpboot \
    kernel5.15/audio/sprd_audio/mcdt/mcdt_r2p0 \
    kernel5.15/audio/sprd_audio/audiopipe \
    kernel5.15/audio/sprd_audio/usb_offload \
    kernel5.15/audio/sprd/machine/sprd_card \
    kernel5.15/audio/sprd/platform/platform_routing \
    kernel5.15/audio/sprd/platform/dmaengine_pcm \
    kernel5.15/audio/sprd/platform/compr_2stage_dma \
    kernel5.15/audio/sprd/dai/vbc/v4/vbc_dai \
    kernel5.15/audio/sprd/dai/vbc/v4/fe_dai \
    kernel5.15/audio/sprd/codec/dummy-codec \
    kernel5.15/audio/sprd/codec/sprd/sc2730/codec \
    kernel5.15/audio/sprd/codec/sprd/sc2730/power \
    kernel5.15/audio/sprd/codec/sprd/sc2730/power_dev \
    kernel5.15/audio/sprd/codec/sprd/pdm_r2p0 \
    kernel5.15/audio/sprd/codec/sprd/ucp1301 \
    kernel5.15/input/fingerprint/silead \
    common/camera/flash/gpio \
    kernel5.15/power/psc2965 \
    kernel5.15/touchscreen/ilitek_v3 \
    kernel5.15/touchscreen/focaltech_ft8725_spi

BOARD_PREBUILT_BOOTIMAGE := $(VENDOR_PATH)/proprietary/images/boot.img
BOARD_KERNEL_SEPARATED_DTBO := true
BOARD_DTBO_CFG := $(DEVICE_PATH)/configs/dtbo.cfg

BOARD_KERNEL_CMDLINE := console=ttyS1,115200n8 bootconfig
BOARD_BOOTCONFIG := androidboot.hardware=ums9230_6h10
BOARD_DTB_CFG := $(DEVICE_PATH)/configs/dtb.cfg
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_KERNEL_BASE := 0x00000000
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --dtb_offset 0x01f00000 --kernel_offset 0x00008000 --ramdisk_offset 0x05400000 --tags_offset 0x00000100
BOARD_MKBOOTIMG_INIT_ARGS += --header_version $(BOARD_INIT_BOOT_HEADER_VERSION)

BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true
BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT := true
BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/rootdir/etc/recovery.fstab
TARGET_RECOVERY_UI_BRIGHTNESS_FILE := /sys/class/backlight/sprd_backlight/brightness
TARGET_RECOVERY_UI_MAX_BRIGHTNESS_FILE := /sys/class/backlight/sprd_backlight/max_brightness
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_USERIMAGES_USE_EXT4 := true

BOARD_VENDOR_KERNEL_MODULES_LOAD := $(strip $(shell cat $(DEVICE_PATH)/modules/modules.load.vendor_dlkm))
BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD := $(strip $(shell cat $(DEVICE_PATH)/modules/modules.load.vendor_boot))
BOARD_VENDOR_RAMDISK_RECOVERY_KERNEL_MODULES_LOAD := $(strip $(shell cat $(DEVICE_PATH)/modules/modules.load.recovery))
BOOT_KERNEL_MODULES := $(BOARD_VENDOR_RAMDISK_RECOVERY_KERNEL_MODULES_LOAD)
BOARD_SYSTEM_KERNEL_MODULES := \
    $(VENDOR_PATH)/proprietary/system_dlkm/lib/modules/kernel/mm/zsmalloc.ko \
    $(VENDOR_PATH)/proprietary/system_dlkm/lib/modules/kernel/drivers/block/zram/zram.ko
BOARD_SYSTEM_KERNEL_MODULES_LOAD := $(BOARD_SYSTEM_KERNEL_MODULES)

BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE := 8388608
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 104857600
BOARD_DTBOIMG_PARTITION_SIZE := 8388608

BOARD_SUPER_PARTITION_SIZE := 5557452800
BOARD_SUPER_PARTITION_GROUPS := group_unisoc
BOARD_GROUP_UNISOC_SIZE := 5553258496
BOARD_GROUP_UNISOC_PARTITION_LIST := \
    odm \
    product \
    system \
    system_dlkm \
    system_ext \
    vendor \
    vendor_dlkm

BOARD_PREBUILT_VENDORIMAGE := $(VENDOR_PATH)/proprietary/images/vendor.img
BOARD_PREBUILT_ODMIMAGE := $(PRODUCT_OUT)/obj/PACKAGING/mblu21_odm_intermediates/odm.img

BOARD_USES_VENDORIMAGE := true
BOARD_USES_ODMIMAGE := true
BOARD_USES_VENDOR_DLKMIMAGE := true
BOARD_USES_SYSTEM_DLKMIMAGE := true
BOARD_USES_METADATA_PARTITION := true

BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_VENDOR_DLKMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_SYSTEM_DLKMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_EROFS_COMPRESSOR := lz4
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := f2fs
TARGET_USERIMAGES_USE_F2FS := true

TARGET_COPY_OUT_SYSTEM_EXT := system_ext
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_ODM := odm
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm
TARGET_COPY_OUT_SYSTEM_DLKM := system_dlkm

BOARD_AVB_ENABLE := true
BOARD_AVB_ALGORITHM := SHA256_RSA4096
BOARD_AVB_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem

BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += \
    --chain_partition l_modem:11:$(VENDOR_PATH)/proprietary/avb/unisoc_modem.avbpubkey \
    --chain_partition l_ldsp:12:$(VENDOR_PATH)/proprietary/avb/unisoc_modem.avbpubkey \
    --chain_partition l_gdsp:13:$(VENDOR_PATH)/proprietary/avb/unisoc_modem.avbpubkey \
    --chain_partition pm_sys:14:$(VENDOR_PATH)/proprietary/avb/unisoc_modem.avbpubkey \
    --chain_partition l_agdsp:15:$(VENDOR_PATH)/proprietary/avb/unisoc_modem.avbpubkey

BOARD_AVB_BOOT_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_BOOT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_BOOT_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_BOOT_ROLLBACK_INDEX_LOCATION := 1

BOARD_AVB_INIT_BOOT_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_INIT_BOOT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_INIT_BOOT_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_INIT_BOOT_ROLLBACK_INDEX_LOCATION := 8

BOARD_AVB_DTBO_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_DTBO_ALGORITHM := SHA256_RSA4096
BOARD_AVB_DTBO_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_DTBO_ROLLBACK_INDEX_LOCATION := 6

BOARD_AVB_VENDOR_BOOT_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VENDOR_BOOT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VENDOR_BOOT_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VENDOR_BOOT_ROLLBACK_INDEX_LOCATION := 18

BOARD_AVB_VBMETA_SYSTEM := system system_ext
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2

BOARD_AVB_VBMETA_VENDOR := vendor
BOARD_AVB_VBMETA_VENDOR_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_VENDOR_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX_LOCATION := 4

BOARD_AVB_VBMETA_CUSTOM_PARTITIONS := system_ext product odm

BOARD_AVB_VBMETA_SYSTEM_EXT := system_dlkm vendor_dlkm
BOARD_AVB_VBMETA_SYSTEM_EXT_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_SYSTEM_EXT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_SYSTEM_EXT_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_SYSTEM_EXT_ROLLBACK_INDEX_LOCATION := 3

BOARD_AVB_VBMETA_PRODUCT := product
BOARD_AVB_VBMETA_PRODUCT_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_PRODUCT_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_PRODUCT_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_PRODUCT_ROLLBACK_INDEX_LOCATION := 5

BOARD_AVB_VBMETA_ODM := odm
BOARD_AVB_VBMETA_ODM_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_ODM_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_ODM_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_ODM_ROLLBACK_INDEX_LOCATION := 7

DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += $(DEVICE_PATH)/framework_compatibility_matrix.xml

TARGET_SYSTEM_PROP += $(DEVICE_PATH)/system.prop

SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/private
SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/public

SYSTEM_EXT_MANIFEST_FILES += $(DEVICE_PATH)/configs/vintf/manifest_srmi.xml

BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true

-include $(VENDOR_PATH)/BoardConfigVendor.mk
