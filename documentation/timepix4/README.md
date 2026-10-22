# Timepix4 experimental integration

Timepix4 support is being introduced as a separate ADServal detector family,
not as a TPX3 configuration variant. The tested setup is one TPX4 emulator
4.3.0 chip, tested with Serval 4.1.6-EXPERIMENTAL (build 1760) and
4.3.0-EXPERIMENTAL (build 1966). The initial emulator setup disabled TDC
generation (`-Dtdc=0`); histogram timing remains unqualified.

## Findings, 2026-10-21

| Area | Finding |
|---|---|
| Preview and Image | With the decoder fix, the operator confirmed Preview and latest-frame, Last-N sum and accumulated-sum Image display with emulator/Serval 4.3. |
| Serval 4.3 framing | Image payloads have alignment spaces before the terminating newline. The decoder supports this and legacy framing, and honors `bigEndian`. |
| Histogram | Both tested Serval versions accept TCP `jsonhisto` / `tof` settings but reject TPX4 acquisition start with `Histopars can only be defined for TPX.` The setup screen remains read-only. |
| Raw output (2026-10-22) | Serval 4.3.0 build 1966 / emulator 4.3.0 passed short raw-only file, per-frame file, TCP connect, simultaneous file/TCP, and coexistence with Image/Preview file captures. Experimental destination controls are available; event decoding and sustained throughput remain unqualified. |
| Raw file/TCP comparison (2026-10-22) | Two saved simultaneous pairs contain identical full pixel-word multisets within three completed shutter intervals: 300,000 selected events per output. Extra file events occur after the final close. See the [comparison report](raw-file-tcp-20261022.md); hardware completeness and precision timing remain unqualified. |
| Raw start/stop and longer runs (2026-10-22) | Fifteen API acquisitions completed, including explicit stops and 2-/5-second finite runs. File/TCP full-frame events match across 74 frames (10.9 million events per output). Explicit stops retain the interrupted frame only in the file. See the [lifecycle report](raw-lifecycle-20261022.md). |
| File writing after URI/chooser updates (2026-10-22) | The operator reported working TPX4 Image, Preview and Raw file writing after the shared path-normalization and TPX4 screen changes. See the [operator check](integration.md#operator-file-writing-check-2026-10-22). TPX3/MPX3 acquisition compatibility remains to be checked. |
| Emulator connection | The operator reported intermittent connection failures with emulator/Serval 4.3. Explicitly setting emulator `-DcmdPort=50001` restored connection. Earlier logs also showed successful connections on 50051; a universal default-port or discovery failure has not been established. |

For the launch command and recovery steps, see
[Emulator command port and connection workaround](integration.md#emulator-command-port-and-connection-workaround).
The detailed qualification record distinguishes automated captures, operator
display checks and work that remains unqualified.

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
- experimental Raw[0]/Raw[1] file and external TCP destination controls on Serval 4.3.0, with actual applied JSON readbacks;
- deterministic family and 448×512 geometry tests.

The following remain disabled or absent until separately qualified:

- PixelConfig comparison and difference mapping;
- operator mask editing/export;
- BPC and DACS upload;
- raw-event decoding, event completeness, sustained raw throughput and TPX4 histogram decoding/timing;
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
