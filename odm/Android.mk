#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),mblu21)

MBLU21_STOCK_ODMIMAGE := $(VENDOR_PATH)/proprietary/images/odm.img
MBLU21_STOCK_MODULES := $(VENDOR_PATH)/proprietary/vendor_dlkm/lib/modules
MBLU21_CAMERA_PROVIDER := android.hardware.camera.provider@2.4-service.mblu21
MBLU21_CAMERA_DIR := $(LOCAL_PATH)/../camera

$(BOARD_PREBUILT_ODMIMAGE): PRIVATE_DIR := $(LOCAL_PATH)
$(BOARD_PREBUILT_ODMIMAGE): \
		$(MBLU21_STOCK_ODMIMAGE) \
		$(LOCAL_PATH)/build_odm.py \
		$(LOCAL_PATH)/odm_sepolicy.cil \
		$(LOCAL_PATH)/odm_service_contexts \
		$(LOCAL_PATH)/odm_property_contexts \
		$(LOCAL_PATH)/uniber.rc \
		$(TARGET_OUT_ODM_EXECUTABLES)/hw/$(MBLU21_CAMERA_PROVIDER) \
		$(MBLU21_CAMERA_DIR)/$(MBLU21_CAMERA_PROVIDER).rc \
		$(MBLU21_CAMERA_DIR)/$(MBLU21_CAMERA_PROVIDER).xml \
		$(MBLU21_STOCK_MODULES)/spi_ilitek.ko \
		$(MBLU21_STOCK_MODULES)/focaltech_spi_v4_1.ko \
		$(PRODUCT_OUT)/system.img \
		$(PRODUCT_OUT)/system_ext.img \
		$(PRODUCT_OUT)/product.img \
		$(BOARD_PREBUILT_VENDORIMAGE) \
		$(HOST_OUT_EXECUTABLES)/secilc \
		$(HOST_OUT_EXECUTABLES)/dump.erofs \
		$(HOST_OUT_EXECUTABLES)/fsck.erofs \
		$(HOST_OUT_EXECUTABLES)/mkfs.erofs \
		$(HOST_OUT_EXECUTABLES)/debugfs \
		$(HOST_OUT_EXECUTABLES)/simg2img \
		$(AVBTOOL)
	@mkdir -p $(dir $@)
	python3 $(PRIVATE_DIR)/build_odm.py \
		--stock $(MBLU21_STOCK_ODMIMAGE) \
		--sepolicy $(PRIVATE_DIR)/odm_sepolicy.cil \
		--service-contexts $(PRIVATE_DIR)/odm_service_contexts \
		--property-contexts $(PRIVATE_DIR)/odm_property_contexts \
		--init-rc $(PRIVATE_DIR)/uniber.rc \
		--modules $(MBLU21_STOCK_MODULES) \
		--file bin/hw/$(MBLU21_CAMERA_PROVIDER) $(TARGET_OUT_ODM_EXECUTABLES)/hw/$(MBLU21_CAMERA_PROVIDER) u:object_r:hal_camera_default_exec:s0 \
		--file etc/init/$(MBLU21_CAMERA_PROVIDER).rc $(MBLU21_CAMERA_DIR)/$(MBLU21_CAMERA_PROVIDER).rc u:object_r:vendor_configs_file:s0 \
		--file etc/vintf/manifest/$(MBLU21_CAMERA_PROVIDER).xml $(MBLU21_CAMERA_DIR)/$(MBLU21_CAMERA_PROVIDER).xml u:object_r:vendor_configs_file:s0 \
		--system $(PRODUCT_OUT)/system.img \
		--system-ext $(PRODUCT_OUT)/system_ext.img \
		--product $(PRODUCT_OUT)/product.img \
		--vendor $(BOARD_PREBUILT_VENDORIMAGE) \
		--host-bin $(HOST_OUT_EXECUTABLES) \
		--avbtool $(AVBTOOL) \
		--out $@

endif
