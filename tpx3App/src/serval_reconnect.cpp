/*
 * ADTimePix3 - read-only Serval reconnect policy
 *
 * Copyright (c) 2026 UT-Battelle, LLC, Oak Ridge National Laboratory
 *
 * SPDX-License-Identifier: MIT
 */

#include "serval_reconnect.h"

namespace ADTimePix3ServalReconnect {

bool Result::complete() const
{
    return destination && detector && measurementConfig;
}

Result refresh(const ReadbackFunction& readback)
{
    Result result;
    result.destination = readback(Readback::Destination);
    result.detector = readback(Readback::Detector);
    result.measurementConfig = readback(Readback::MeasurementConfig);
    return result;
}

const char* path(Readback readback)
{
    switch (readback) {
    case Readback::Destination:
        return "/server/destination";
    case Readback::Detector:
        return "/detector";
    case Readback::MeasurementConfig:
        return "/measurement/config";
    }
    return "";
}

}  // namespace ADTimePix3ServalReconnect
