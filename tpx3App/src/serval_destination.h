/*
 * ADTimePix3 - Serval destination response validation
 *
 * Copyright (c) 2026 UT-Battelle, LLC, Oak Ridge National Laboratory
 *
 * SPDX-License-Identifier: MIT
 */

#ifndef ADTIMEPIX_SERVAL_DESTINATION_H
#define ADTIMEPIX_SERVAL_DESTINATION_H

#include <cstddef>
#include <string>

namespace ADTimePix3ServalDestination {

enum class ResponseError {
    None,
    NotConfigured,
    HttpFailure,
    EmptyBody,
    MalformedJson,
    InvalidRoot,
    InvalidDestination,
    InvalidRawChannels,
    InvalidImageChannels,
    InvalidPreview,
    InvalidPreviewImageChannels,
    InvalidPreviewHistogramChannels
};

struct Snapshot {
    std::size_t rawChannels = 0;
    std::string rawDestinations[2] = {"{}", "{}"};
    std::size_t imageChannels = 0;
    std::size_t previewImageChannels = 0;
    std::size_t previewHistogramChannels = 0;
    std::string histogramDestination = "{}";
};

/** Validate GET /server/destination and count each supported channel family. */
ResponseError parseResponse(long httpStatus, const std::string& body,
                            Snapshot& snapshot);

const char* responseErrorMessage(ResponseError error);

/** Experimental TPX4 raw output is qualified only on Serval 4.3.0.
 * Returns nullptr when allowed; payload decoding is outside this contract. */
const char* tpx4RawOutputError(const std::string& version, const std::string& base,
                              int splitStrategy, int queueSize);

}  // namespace ADTimePix3ServalDestination

#endif  // ADTIMEPIX_SERVAL_DESTINATION_H
