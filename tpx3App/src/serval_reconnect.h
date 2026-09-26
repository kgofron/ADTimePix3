/*
 * ADTimePix3 - read-only Serval reconnect policy
 *
 * Copyright (c) 2026 UT-Battelle, LLC, Oak Ridge National Laboratory
 *
 * SPDX-License-Identifier: MIT
 */

#ifndef ADTIMEPIX_SERVAL_RECONNECT_H
#define ADTIMEPIX_SERVAL_RECONNECT_H

#include <functional>

namespace ADTimePix3ServalReconnect {

enum class Readback {
    Destination,
    Detector,
    MeasurementConfig
};

struct Result {
    bool destination = false;
    bool detector = false;
    bool measurementConfig = false;

    bool complete() const;
};

using ReadbackFunction = std::function<bool(Readback)>;

/** Run every read-only reconciliation step and retain each result. */
Result refresh(const ReadbackFunction& readback);

/** Serval REST resource used by a readback step. */
const char* path(Readback readback);

}  // namespace ADTimePix3ServalReconnect

#endif
