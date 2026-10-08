/*
 * ADTimePix3 - validated detector raster and chip-grid geometry
 *
 * Copyright (c) 2026 UT-Battelle, LLC, Oak Ridge National Laboratory
 *
 * SPDX-License-Identifier: MIT
 */

#include "detector_geometry.h"

#include <cstdint>

namespace ADTimePix3DetectorGeometry {

Status derive(int pixelCount, int rowLength, int numberOfChips,
              int numberOfRows, Geometry& geometry)
{
    geometry = Geometry{0, 0, 0, 0, 0, 0};
    if (pixelCount <= 0 || rowLength <= 0 || numberOfChips <= 0 ||
        numberOfRows <= 0) {
        return Status::InvalidArgument;
    }

    if (numberOfChips % rowLength != 0 || pixelCount % numberOfRows != 0) {
        return Status::PixelCountMismatch;
    }

    const int xChips = rowLength;
    const int yChips = numberOfChips / xChips;
    const int rows = numberOfRows;
    const int cols = pixelCount / rows;
    if (xChips <= 0 || yChips <= 0 || rows % yChips != 0 ||
        cols % xChips != 0) {
        return Status::NonIntegralChipGrid;
    }
    const int chipWidth = cols / xChips;
    const int chipHeight = rows / yChips;
    if (chipWidth <= 0 || chipHeight <= 0 ||
        static_cast<std::int64_t>(chipWidth) * chipHeight * numberOfChips != pixelCount ||
        static_cast<std::int64_t>(rows) * cols != pixelCount) {
        return Status::NonIntegralChipGrid;
    }

    geometry = Geometry{static_cast<int>(rows), static_cast<int>(cols),
                        xChips, yChips, chipWidth, chipHeight};
    return Status::Ok;
}

bool isTwoQuadLayout(const std::string& firstChipboardId,
                     const std::string& secondChipboardId)
{
    return firstChipboardId.size() >= 2 && secondChipboardId.size() >= 2 &&
           firstChipboardId.compare(0, 2, "41") == 0 &&
           secondChipboardId.compare(0, 2, "41") == 0 &&
           firstChipboardId != secondChipboardId;
}

const char* statusMessage(Status status)
{
    switch (status) {
    case Status::Ok:
        return "ok";
    case Status::InvalidArgument:
        return "invalid detector geometry argument";
    case Status::PixelCountMismatch:
        return "detector raster and pixel count disagree";
    case Status::NonIntegralChipGrid:
        return "detector raster does not form an integral rectangular chip grid";
    }
    return "unknown detector geometry error";
}

}  // namespace ADTimePix3DetectorGeometry
