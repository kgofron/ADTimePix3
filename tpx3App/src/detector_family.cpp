/*
 * ADTimePix3 - Serval detector-family identification and capabilities
 *
 * Copyright (c) 2022-2026 UT-Battelle, LLC, Oak Ridge National Laboratory
 *
 * SPDX-License-Identifier: MIT
 */

#include "detector_family.h"

#include <algorithm>
#include <cctype>

namespace {

std::string upperAscii(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

bool chipboardPrefixIs(const std::string& chipboardId, char digit) {
    return !chipboardId.empty() && chipboardId[0] == digit;
}

}  // namespace

DetectorFamily detectDetectorFamily(int mpxType, const std::string& chipType,
                                    const std::string& chipboardId) {
    const std::string chip = upperAscii(chipType);

    if (chip == "MPX3") return DetectorFamily::MPX3;
    if (chip == "TPX3") return DetectorFamily::TPX3;
    if (chip == "TPX4") return DetectorFamily::TPX4;

    if (mpxType == 5) return DetectorFamily::MPX3;
    if (mpxType == 6) return DetectorFamily::TPX3;
    if (mpxType == 7) return DetectorFamily::TPX4;

    if (chipboardPrefixIs(chipboardId, '5')) return DetectorFamily::MPX3;
    if (chipboardPrefixIs(chipboardId, '4')) return DetectorFamily::TPX3;

    return DetectorFamily::Unknown;
}

DetectorCapabilities capabilitiesForFamily(DetectorFamily family) {
    DetectorCapabilities caps;
    switch (family) {
    case DetectorFamily::MPX3:
        caps.supportsTdc = false;
        caps.supportsTofHistogram = false;
        caps.supportsDualPreview = true;
        caps.supportsImageThresholds = true;
        caps.supportsPixelConfig = true;
        caps.supportsCalibrationUpload = true;
        caps.previewLayerCount = 2;
        /* One big-endian 16-bit word per pixel: mask bit 0, th0 trim bits 1-5,
         * th1 trim bits 6-10. See PIXELCONFIG_BPC_DIFF.md. */
        caps.bpcBytesPerPel = 2;
        caps.bpcThresholdSlices = 1;
        break;
    case DetectorFamily::TPX3:
        caps.supportsTdc = true;
        caps.supportsTofHistogram = true;
        caps.supportsDualPreview = true;
        caps.supportsImageThresholds = false;
        caps.supportsPixelConfig = true;
        caps.supportsCalibrationUpload = true;
        caps.previewLayerCount = 2;
        caps.bpcBytesPerPel = 1;
        caps.bpcThresholdSlices = 1;
        break;
    case DetectorFamily::TPX4:
        /* Serval 4.1.6 reports a single 448x512 chip. One jsonimage preview
         * layer is configured for bring-up; TPX3/MPX3 PixelConfig, mask,
         * calibration, ToF, threshold and dual-preview semantics must not be
         * assumed. */
        caps.supportsTdc = false;
        caps.supportsTofHistogram = false;
        caps.supportsDualPreview = false;
        caps.supportsImageThresholds = false;
        caps.supportsPixelConfig = false;
        caps.supportsCalibrationUpload = false;
        caps.previewLayerCount = 1;
        caps.bpcBytesPerPel = 0;
        caps.bpcThresholdSlices = 0;
        break;
    default:
        break;
    }
    return caps;
}

const char* detectorFamilyName(DetectorFamily family) {
    switch (family) {
    case DetectorFamily::TPX3:
        return "TPX3";
    case DetectorFamily::MPX3:
        return "MPX3";
    case DetectorFamily::TPX4:
        return "TPX4";
    default:
        return "UNKNOWN";
    }
}
