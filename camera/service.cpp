/*
 * SPDX-FileCopyrightText: 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

#define LOG_TAG "android.hardware.camera.provider@2.4-service.mblu21"

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

#include <android/hardware/camera/device/3.5/ICameraDevice.h>
#include <android/hardware/camera/provider/2.4/ICameraProvider.h>
#include <hidl/HidlTransportSupport.h>
#include <log/log.h>
#include <system/camera_metadata.h>

using android::sp;
using android::wp;
using android::hardware::configureRpcThreadpool;
using android::hardware::hidl_death_recipient;
using android::hardware::hidl_handle;
using android::hardware::hidl_string;
using android::hardware::hidl_vec;
using android::hardware::joinRpcThreadpool;
using android::hardware::Return;
using android::hardware::Void;
using android::hardware::camera::common::V1_0::Status;
using android::hardware::camera::common::V1_0::TorchMode;
using android::hardware::camera::device::V3_2::CameraMetadata;
using android::hardware::camera::device::V3_2::ICameraDeviceCallback;
using android::hardware::camera::device::V3_4::StreamConfiguration;
using android::hardware::camera::provider::V2_4::ICameraProvider;
using android::hardware::camera::provider::V2_4::ICameraProviderCallback;
using android::hidl::base::V1_0::IBase;

namespace V3_2 = android::hardware::camera::device::V3_2;
namespace V3_5 = android::hardware::camera::device::V3_5;

namespace {

constexpr char kStockInstance[] = "legacy/0";
constexpr char kStockType[] = "legacy";
constexpr char kInstance[] = "hidden/0";
constexpr char kType[] = "hidden";
constexpr int kFirstHiddenId = 17;
constexpr int kLastHiddenId = 58;

std::string deviceName(const std::string& version, const char* type, const std::string& id) {
    return "device@" + version + "/" + type + "/" + id;
}

CameraMetadata secureOnly(const CameraMetadata& characteristics) {
    const auto* source = reinterpret_cast<const camera_metadata_t*>(characteristics.data());
    size_t size = characteristics.size();
    if (size == 0 || validate_camera_metadata_structure(source, &size) != android::OK) {
        return {};
    }
    std::unique_ptr<camera_metadata_t, decltype(&free_camera_metadata)> copy(
            allocate_camera_metadata(get_camera_metadata_entry_count(source) + 1,
                                     get_camera_metadata_data_count(source)),
            free_camera_metadata);
    if (copy == nullptr || append_camera_metadata(copy.get(), source) != android::OK) {
        return {};
    }
    const uint8_t capability = ANDROID_REQUEST_AVAILABLE_CAPABILITIES_SECURE_IMAGE_DATA;
    camera_metadata_entry_t entry;
    int res = find_camera_metadata_entry(copy.get(), ANDROID_REQUEST_AVAILABLE_CAPABILITIES, &entry);
    if (res == android::OK) {
        res = update_camera_metadata_entry(copy.get(), entry.index, &capability, 1, nullptr);
    } else {
        res = add_camera_metadata_entry(copy.get(), ANDROID_REQUEST_AVAILABLE_CAPABILITIES,
                                        &capability, 1);
    }
    if (res != android::OK) {
        return {};
    }
    CameraMetadata result;
    result.resize(get_camera_metadata_size(copy.get()));
    memcpy(result.data(), copy.get(), result.size());
    return result;
}

sp<V3_5::ICameraDevice> stockDevice(const sp<ICameraProvider>& stock, const std::string& name) {
    sp<V3_2::ICameraDevice> device;
    Return<void> ret = stock->getCameraDeviceInterface_V3_x(
            name, [&](Status status, const sp<V3_2::ICameraDevice>& result) {
                if (status == Status::OK) device = result;
            });
    if (!ret.isOk() || device == nullptr) {
        return nullptr;
    }
    Return<sp<V3_5::ICameraDevice>> cast = V3_5::ICameraDevice::castFrom(device);
    return cast.isOk() ? static_cast<sp<V3_5::ICameraDevice>>(cast) : nullptr;
}

class HiddenSecureDevice : public V3_5::ICameraDevice {
  public:
    explicit HiddenSecureDevice(sp<V3_5::ICameraDevice> device) : mDevice(std::move(device)) {}

    Return<void> getResourceCost(getResourceCost_cb cb) override {
        return mDevice->getResourceCost(cb);
    }

    Return<void> getCameraCharacteristics(getCameraCharacteristics_cb cb) override {
        return mDevice->getCameraCharacteristics(
                [&](Status status, const CameraMetadata& characteristics) {
                    if (status != Status::OK) {
                        cb(status, characteristics);
                        return;
                    }
                    CameraMetadata hidden = secureOnly(characteristics);
                    cb(hidden.size() == 0 ? Status::INTERNAL_ERROR : Status::OK, hidden);
                });
    }

    Return<Status> setTorchMode(TorchMode mode) override { return mDevice->setTorchMode(mode); }

    Return<void> open(const sp<ICameraDeviceCallback>& callback, open_cb cb) override {
        return mDevice->open(callback, cb);
    }

    Return<void> dumpState(const hidl_handle& fd) override { return mDevice->dumpState(fd); }

    Return<void> getPhysicalCameraCharacteristics(
            const hidl_string& physicalCameraId,
            getPhysicalCameraCharacteristics_cb cb) override {
        return mDevice->getPhysicalCameraCharacteristics(physicalCameraId, cb);
    }

    Return<void> isStreamCombinationSupported(const StreamConfiguration& streams,
                                              isStreamCombinationSupported_cb cb) override {
        return mDevice->isStreamCombinationSupported(streams, cb);
    }

  private:
    const sp<V3_5::ICameraDevice> mDevice;
};

class HiddenCameraProvider : public ICameraProvider {
  public:
    HiddenCameraProvider(sp<ICameraProvider> stock, std::string version,
                         std::vector<std::string> ids)
        : mStock(std::move(stock)), mVersion(std::move(version)), mIds(std::move(ids)) {}

    Return<Status> setCallback(const sp<ICameraProviderCallback>&) override { return Status::OK; }

    Return<void> getVendorTags(getVendorTags_cb cb) override { return mStock->getVendorTags(cb); }

    Return<void> getCameraIdList(getCameraIdList_cb cb) override {
        std::vector<hidl_string> names;
        for (const std::string& id : mIds) {
            names.push_back(deviceName(mVersion, kType, id));
        }
        cb(Status::OK, names);
        return Void();
    }

    Return<void> isSetTorchModeSupported(isSetTorchModeSupported_cb cb) override {
        cb(Status::OK, false);
        return Void();
    }

    Return<void> getCameraDeviceInterface_V1_x(const hidl_string&,
                                               getCameraDeviceInterface_V1_x_cb cb) override {
        cb(Status::OPERATION_NOT_SUPPORTED, nullptr);
        return Void();
    }

    Return<void> getCameraDeviceInterface_V3_x(const hidl_string& name,
                                               getCameraDeviceInterface_V3_x_cb cb) override {
        for (const std::string& id : mIds) {
            if (name != deviceName(mVersion, kType, id)) continue;
            sp<V3_5::ICameraDevice> device = stockDevice(mStock, deviceName(mVersion, kStockType, id));
            if (device == nullptr) {
                cb(Status::INTERNAL_ERROR, nullptr);
            } else {
                cb(Status::OK, new HiddenSecureDevice(device));
            }
            return Void();
        }
        cb(Status::ILLEGAL_ARGUMENT, nullptr);
        return Void();
    }

  private:
    const sp<ICameraProvider> mStock;
    const std::string mVersion;
    const std::vector<std::string> mIds;
};

struct StockProviderDeath : hidl_death_recipient {
    void serviceDied(uint64_t, const wp<IBase>&) override {
        ALOGE("%s died", kStockInstance);
        std::_Exit(EXIT_FAILURE);
    }
};

}

int main() {
    configureRpcThreadpool(1, true);

    sp<ICameraProvider> stock = ICameraProvider::getService(kStockInstance);
    if (stock == nullptr) {
        LOG_ALWAYS_FATAL("no %s camera provider", kStockInstance);
    }

    std::string version;
    std::vector<std::string> listed;
    const std::string prefix = "device@";
    Return<void> ret = stock->getCameraIdList([&](Status status, const hidl_vec<hidl_string>& names) {
        if (status != Status::OK) return;
        for (const hidl_string& name : names) {
            const std::string device = name;
            const size_t typeStart = device.find('/');
            const size_t idStart = device.rfind('/');
            if (device.rfind(prefix, 0) != 0 || typeStart == idStart) continue;
            version = device.substr(prefix.size(), typeStart - prefix.size());
            listed.push_back(device.substr(idStart + 1));
        }
    });
    if (!ret.isOk() || version.empty()) {
        LOG_ALWAYS_FATAL("cannot list the cameras of %s", kStockInstance);
    }

    std::vector<std::string> hidden;
    for (int i = kFirstHiddenId; i <= kLastHiddenId; i++) {
        const std::string id = std::to_string(i);
        if (std::find(listed.begin(), listed.end(), id) != listed.end()) continue;
        if (stockDevice(stock, deviceName(version, kStockType, id)) != nullptr) {
            hidden.push_back(id);
        }
    }
    if (hidden.empty()) {
        LOG_ALWAYS_FATAL("%s serves no unlisted camera", kStockInstance);
    }

    sp<StockProviderDeath> death = new StockProviderDeath();
    if (!stock->linkToDeath(death, 0).withDefault(false)) {
        LOG_ALWAYS_FATAL("cannot watch %s", kStockInstance);
    }

    sp<ICameraProvider> provider = new HiddenCameraProvider(stock, version, hidden);
    if (provider->registerAsService(kInstance) != android::OK) {
        LOG_ALWAYS_FATAL("cannot register %s", kInstance);
    }
    ALOGI("serving %zu unlisted cameras of %s", hidden.size(), kStockInstance);
    joinRpcThreadpool();
    return EXIT_FAILURE;
}
