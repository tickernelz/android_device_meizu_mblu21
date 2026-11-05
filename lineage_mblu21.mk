#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

$(call inherit-product, device/meizu/mblu21/device.mk)

$(call inherit-product, vendor/custom/config/common_full_phone.mk)

TARGET_SCREEN_WIDTH := 720
TARGET_PROVIDES_FACE_UNLOCK_HAL := true

PRODUCT_NAME := lineage_mblu21
PRODUCT_DEVICE := mblu21
PRODUCT_BRAND := meizu
PRODUCT_MODEL := Mblu 21
PRODUCT_MANUFACTURER := MEIZU

PRODUCT_GMS_CLIENTID_BASE := android-meizu
