#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

PREBUILT_MODULES := $(wildcard $(KERNEL_SRC)/../../../vendor/meizu/mblu21/proprietary/vendor_dlkm/lib/modules/*.ko)
KERNELRELEASE := $(shell cat $(OUT_DIR)/include/config/kernel.release)

.PHONY: modules modules_install

modules:
	@test -n "$(PREBUILT_MODULES)"

modules_install:
	mkdir -p $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)/extra
	cp $(PREBUILT_MODULES) $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)/extra
