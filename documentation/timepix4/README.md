# Timepix4 experimental integration

Timepix4 support is being introduced as a separate ADServal detector family,
not as a TPX3 configuration variant. The tested setup is one TPX4 emulator
4.3.0 chip, tested with Serval 4.1.6-EXPERIMENTAL (build 1760) and
4.3.0-EXPERIMENTAL (build 1966). The initial emulator setup disabled TDC
generation (`-Dtdc=0`); histogram timing remains unqualified.

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
- one preview jsonimage destination and PVA publication path;
- shared Preview/Image decoding for legacy and Serval 4.3 aligned framing,
  including explicit byte-order metadata;
- experimental Image 0 output and a monitor with frame, Last-N and accumulated views;
- a Histogram destination compatibility screen with read-only settings and applied readback;
- deterministic family and 448×512 geometry tests.

The following remain disabled or absent until separately qualified:

- PixelConfig comparison and difference mapping;
- operator mask editing/export;
- BPC and DACS upload;
- raw-event channels and TPX4 histogram decoding/timing;
- qualification of full-rate image performance, dual-preview and MPX3 threshold behavior;
- orientations other than the captured `UP` layout;
- multi-chip TPX4 layouts;
- physical-detector qualification.

Both tested Serval versions accept a TPX4 TCP `jsonhisto` / `tof`
destination, then reject measurement start with
`Histopars can only be defined for TPX.` Histogram output remains blocked in
the driver and screen until a working Serval path is qualified. This was a
startup rejection test, not completed histogram acquisition validation.

See [integration.md](integration.md) for startup and evidence collection.
