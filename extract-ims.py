#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

MY_DIR = os.path.dirname(os.path.abspath(__file__))
ANDROID_ROOT = os.environ.get("ANDROID_ROOT", os.path.join(MY_DIR, "..", "..", ".."))
VENDOR_DIR = os.path.join(ANDROID_ROOT, "vendor", "meizu", "mblu21", "proprietary")
APKTOOL = os.environ.get("APKTOOL", "apktool")

IMS_APK = "system_ext/priv-app/ims/ims.apk"
RADIO_INTERACTOR_COMMON = "system/system/framework/radio_interactor_common.jar"
APPS = {
    IMS_APK: {
        "smali_classes2": ("system/system/framework/unisoc_ims_common.jar", None),
        "smali_classes3": (RADIO_INTERACTOR_COMMON, None),
        "smali_classes4": ("system_ext/framework/unisoc-framework.jar", "com/android/ims/internal/ImsCallForwardInfoEx"),
    },
    "system_ext/priv-app/radio_interactor_service/radio_interactor_service.apk": {
        "smali_classes2": (RADIO_INTERACTOR_COMMON, None),
    },
}
COPIES = [
    "system_ext/bin/ims_bridged",
    "system_ext/bin/srmi_proxyd",
    "system_ext/etc/init/ims_bridged.rc",
    "system_ext/etc/init/srmi_proxyd.rc",
    "system_ext/etc/permissions/com.spreadtrum.ims.xml",
    "system_ext/lib/libimsbrd.so",
    "system_ext/lib/libsrmi.so",
    "system_ext/lib/libsrmiservice.so",
    "system_ext/lib/vendor.unisoc.frameworks.srmi-V1-ndk.so",
    "system_ext/lib64/libimsbrd.so",
    "system_ext/lib64/libsrmi.so",
    "system_ext/lib64/libsrmiservice.so",
    "system_ext/lib64/vendor.unisoc.frameworks.srmi-V1-ndk.so",
]

DROPPED_CALLS = {
    "system_ext/priv-app/radio_interactor_service/radio_interactor_service.apk": [
        (
            "com/android/unisoc/telephony/server/ExtRadioNetworkIndication.smali",
            "Lcom/android/internal/telephony/ServiceStateTracker;->startUpdateState(IIII)V",
        ),
    ],
}

METRICS = "Lcom/android/internal/telephony/metrics/TelephonyMetrics;"
HIDDENAPI_FLAG = re.compile(
    r"^(whitelist|blacklist|greylist(-max-\w+)?|test-api|core-platform-api|max-target-\w+|sdk|unsupported|blocked|conditional)$"
)


def verify_inputs(dump):
    with open(os.path.join(MY_DIR, "ims-inputs.sha256")) as f:
        for line in f:
            digest, path = line.split()
            with open(os.path.join(dump, path), "rb") as blob:
                if hashlib.sha256(blob.read()).hexdigest() != digest:
                    sys.exit(f"{path}: checksum mismatch")


def apktool_decode(src, dst):
    subprocess.run([APKTOOL, "d", "-r", "-f", src, "-o", dst], check=True, stdout=subprocess.DEVNULL)


def drop_telephony_metrics(smali_dir):
    for name in ("ImsRadioInterface.smali", "ImsRadioInterface$RilHandler.smali"):
        path = os.path.join(smali_dir, "com", "spreadtrum", "ims", name)
        with open(path) as f:
            text = f.read()
        text = re.sub(
            r"invoke-static \{\}, " + re.escape(METRICS) + r"->getInstance\(\)" + re.escape(METRICS) + r"\n\n    move-result-object (v\d+)",
            r"const/4 \1, 0x0",
            text,
        )
        text = re.sub(r"\n    invoke-virtual(/range)? \{[^}]*\}, " + re.escape(METRICS) + r"->writeOn\w+\([^)]*\)V\n", "\n", text)
        if re.search(r"invoke-[\w/]+ \{[^}]*\}, " + re.escape(METRICS) + "->", text):
            sys.exit(f"{name}: TelephonyMetrics call left")
        text = text.replace(METRICS, "Ljava/lang/Object;")
        with open(path, "w") as f:
            f.write(text)
    for root, _, files in os.walk(smali_dir):
        for name in files:
            with open(os.path.join(root, name)) as f:
                if METRICS in f.read():
                    sys.exit(f"{name}: TelephonyMetrics reference left")


def drop_calls(smali_dir, calls):
    for path, method in calls:
        path = os.path.join(smali_dir, path)
        with open(path) as f:
            text = f.read()
        text, count = re.subn(r"\n    invoke-virtual(/range)? \{[^}]*\}, " + re.escape(method) + r"\n", "\n", text)
        if count != 1:
            sys.exit(f"{path}: expected one call to {method}, found {count}")
        with open(path, "w") as f:
            f.write(text)


def strip_hiddenapi_flags(smali_dir):
    for root, _, files in os.walk(smali_dir):
        for name in files:
            path = os.path.join(root, name)
            with open(path) as f:
                lines = f.read().split("\n")
            for i, line in enumerate(lines):
                if line.startswith((".method ", ".field ")):
                    tokens = line.split(" ")
                    member = next(j for j, t in enumerate(tokens) if "(" in t or ":" in t)
                    kept = [t for t in tokens[1:member] if not HIDDENAPI_FLAG.match(t)]
                    lines[i] = " ".join([tokens[0]] + kept + tokens[member:])
            with open(path, "w") as f:
                f.write("\n".join(lines))


def main():
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <extracted_partitions_dir>")
    dump = sys.argv[1]
    verify_inputs(dump)
    for apk, jars in APPS.items():
        with tempfile.TemporaryDirectory() as work:
            app = os.path.join(work, "app")
            apktool_decode(os.path.join(dump, apk), app)
            if apk == IMS_APK:
                drop_telephony_metrics(os.path.join(app, "smali"))
            drop_calls(os.path.join(app, "smali"), DROPPED_CALLS.get(apk, []))
            for dex_dir, (jar, only) in jars.items():
                jar_dir = os.path.join(work, dex_dir)
                apktool_decode(os.path.join(dump, jar), jar_dir)
                src = os.path.join(jar_dir, "smali")
                dst = os.path.join(app, dex_dir)
                if only is None:
                    shutil.copytree(src, dst)
                else:
                    os.makedirs(os.path.join(dst, os.path.dirname(only)))
                    for name in os.listdir(os.path.join(src, os.path.dirname(only))):
                        if re.fullmatch(re.escape(os.path.basename(only)) + r"(\$\w+)?\.smali", name):
                            shutil.copy(os.path.join(src, os.path.dirname(only), name), os.path.join(dst, os.path.dirname(only)))
                strip_hiddenapi_flags(dst)
            out_apk = os.path.join(VENDOR_DIR, apk)
            os.makedirs(os.path.dirname(out_apk), exist_ok=True)
            subprocess.run([APKTOOL, "b", app, "-o", out_apk], check=True, stdout=subprocess.DEVNULL)
    for path in COPIES:
        dst = os.path.join(VENDOR_DIR, path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(dump, path), dst)


if __name__ == "__main__":
    main()
