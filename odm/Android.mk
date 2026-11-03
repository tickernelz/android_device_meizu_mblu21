#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),mblu21)

MBLU21_STOCK_ODMIMAGE := $(VENDOR_PATH)/proprietary/images/odm.img
MBLU21_STOCK_MODULES := $(VENDOR_PATH)/proprietary/vendor_dlkm/lib/modules

$(BOARD_PREBUILT_ODMIMAGE): PRIVATE_DIR := $(LOCAL_PATH)
$(BOARD_PREBUILT_ODMIMAGE): \
		$(MBLU21_STOCK_ODMIMAGE) \
		$(LOCAL_PATH)/build_odm.py \
		$(LOCAL_PATH)/odm_sepolicy.cil \
		$(LOCAL_PATH)/odm_service_contexts \
		$(MBLU21_STOCK_MODULES)/spi_ilitek.ko \
		$(MBLU21_STOCK_MODULES)/focaltech_spi_v4_1.ko \
		$(HOST_OUT_EXECUTABLES)/dump.erofs \
		$(HOST_OUT_EXECUTABLES)/fsck.erofs \
		$(HOST_OUT_EXECUTABLES)/mkfs.erofs \
		$(AVBTOOL)
	@mkdir -p $(dir $@)
	python3 $(PRIVATE_DIR)/build_odm.py \
		--stock $(MBLU21_STOCK_ODMIMAGE) \
		--sepolicy $(PRIVATE_DIR)/odm_sepolicy.cil \
		--service-contexts $(PRIVATE_DIR)/odm_service_contexts \
		--modules $(MBLU21_STOCK_MODULES) \
		--host-bin $(HOST_OUT_EXECUTABLES) \
		--avbtool $(AVBTOOL) \
		--out $@

endif
