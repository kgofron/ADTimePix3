# Timepix4 single-chip integration

## Components

| Component | Entry point |
|---|---|
| IOC launcher | `iocs/tpx3IOC/iocBoot/iocTimePix/st_tpx4.cmd` |
| IOC profile | `iocs/tpx3IOC/iocBoot/iocTimePix/profiles/tpx4/` |
| Phoebus launcher | `tpx3App/op/bob/TimePix4.bob` |
| Phoebus profile | `tpx3App/op/bob/profiles/tpx4/` |
| Local API evidence | `.codex/tpx4/` (gitignored) |
| Calibration boundary | `vendor/tpx4/README.md` |

The profile defaults to `SERVER_URL=http://localhost:8081` and
`PREFIX=TPX4-TEST:`. Override those values in a site wrapper when necessary.

## Conservative startup

Run from the IOC boot directory after starting the matching emulator and
Serval instance:

```bash
./st_tpx4.cmd
```

Startup loads shared records and plugins, sets 448×512 waveform capacities,
requests a detector connection refresh, and configures one preview-only
destination:

```text
Preview.ImageChannels[0].Base = tcp://listen@localhost:8089
Preview.ImageChannels[0].Format = jsonimage
Preview.ImageChannels[0].Mode = tot
Preview.Period = 1.0
```

The IOC then enables `Pva1` callbacks, publishing decoded arrays as
`pva://TPX4-TEST:Pva1:Image`. It does not apply detector setpoints, upload
calibration, or enable full-rate image, secondary preview, raw or histogram
channels.

Expected discovery readbacks include:

```text
DetectorFamily_RBV = TPX4
ChipType_RBV       = TPX4
MpxType_RBV        = 7
PixCount_RBV       = 229376
RowLen_RBV         = 1
NChips_RBV         = 1
NRows_RBV          = 512
MaxSizeX_RBV       = 448
MaxSizeY_RBV       = 512
```

## API evidence

Capture both native OpenAPI representations from the same Serval process:

```bash
SERVAL_URL=http://localhost:8081
mkdir -p .codex/tpx4
wget --quiet --timeout=20 --tries=2 \
  --output-document=.codex/tpx4/openapi.json \
  "${SERVAL_URL}/openapi.json"
wget --quiet --timeout=20 --tries=2 \
  --output-document=.codex/tpx4/openapi.yaml \
  "${SERVAL_URL}/openapi.yaml"
```

Keep full generated API and detector snapshots as local evidence. Commit only
small derived fixtures and facts needed for deterministic tests.

## Preview destination control

The TPX4 status panel opens `Acquire/Tpx4ServerFileWriter.bob`. This restricted
screen can edit and reapply the single preview destination without exposing
unqualified TPX3/MPX3 channels. After changing a preview field, use **Apply
Destination** to send the complete destination to Serval and refresh the
readbacks.

## Next qualification evidence

Capture the preview's complete Serval destination readback, JSON header,
payload size, pixel format and one asymmetric raster whose orientation can be
verified. Before enabling full-rate image, PixelConfig or calibration
operations, establish their encoding, local raster order, read/write round
trips and coordinate placement independently.
