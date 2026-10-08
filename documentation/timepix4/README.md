# Timepix4 experimental integration

Timepix4 support is being introduced as a separate ADServal detector family,
not as a TPX3 configuration variant. The first scope is one TPX4 emulator chip
served by Serval 4.1.6-EXPERIMENTAL.

## Captured detector contract

The local Serval detector snapshot reports:

| Field | Value |
|---|---|
| `ChipType` | `TPX4` |
| `MpxType` | `7` |
| `PixCount` | `229376` |
| `RowLen` | `1` chip across |
| `NumberOfChips` | `1` |
| `NumberOfRows` | `512` |
| Original/rotated raster | `448×512` |
| Chip placement | chip 0 at `(0,0)`, `LtRBtT` |

The captured PixelConfig response decodes to 229376 bytes. Its bit meanings,
local coordinate order and writable file representation are not yet qualified.

## Current implementation boundary

The feature branch provides:

- explicit `DetectorFamily::TPX4` detection from `ChipType` or `MpxType=7`;
- independent rectangular chip width and height derivation;
- conservative TPX4 capabilities;
- a separate experimental IOC profile and Phoebus launcher;
- one preview-only jsonimage destination and PVA publication path;
- deterministic family and 448×512 geometry tests.

The following remain disabled or absent until separately qualified:

- PixelConfig comparison and difference mapping;
- operator mask editing/export;
- BPC and DACS upload;
- raw-event and histogram channels;
- full-rate image, dual-preview and MPX3 threshold behavior;
- orientations other than the captured `UP` layout;
- multi-chip TPX4 layouts;
- physical-detector qualification.

See [integration.md](integration.md) for startup and evidence collection.
