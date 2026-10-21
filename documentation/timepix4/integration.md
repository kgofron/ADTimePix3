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

## Image monitor

Open **Image** from the Timepix4 status panel or **Open Image** from
Destinations. The display is
`tpx3App/op/bob/profiles/tpx4/Acquire/Tpx4Image.bob` and inherits the caller's
`P` and camera `R` macros.

Configure Image 0 as a TCP `jsonimage` destination in Destinations, enable
the IOC receiver / frame processing, apply the destination while idle, then
acquire. Opening the monitor does not enable a destination or start a run.
Use Image integration size **1** for one detector frame per received message.
Preview remains independent and can continue publishing through `Pva1`.

The view selector offers:

| View | Data | Meaning |
|---|---|---|
| Latest frame | `$(P)$(R)ImgImageFrame` | Latest processed Image message |
| Last N — sum | `$(P)$(R)ImgImageSumNFrames` | Bounded rolling sum of received Image messages |
| Accumulated — sum | `$(P)$(R)ImgImageData` | Sum since acquisition start or Clear |

The monitor uses Image-only `ImgSizeX_RBV` and `ImgSizeY_RBV`, including
448×512 and rotated 512×448 rasters. Preview cannot change these dimensions.
`ImgFramesReceived_RBV` counts complete Image messages since acquisition
start (clamped at 2147483647), independently of the shared areaDetector array
counter. `ImgAccumulatedFrames_RBV` counts processed messages since acquisition
start or Clear. These counters do not establish packet-level completeness.

**Clear sums** resets both sums and their contribution counts; the received
count is preserved. Old plots are hidden until another processed frame arrives.
Both sums also reset automatically after the next remote acquisition starts
successfully, before its Image receiver starts. Stop preserves the latest frame,
both sums, the received-message count and contribution counts for inspection.
The Image rate readback returns to zero when stopped. Processing must be enabled
before acquisition; disabling it hides the plots.

Requested N may exceed the effective rolling capacity when the retention budget
is too small. Check effective capacity, actual rolling occupancy, retention
status and numeric range status. The publication interval throttles Last-N
updates in units of received messages; every processed message still enters
the sums. The first rolling frame after a reset is published immediately.
Stop also publishes any remaining rolling-window update skipped by the interval,
so the retained Last-N image includes the final processed frames.
Latest-frame and accumulated waveforms continue publishing on every processed
message, so qualify the monitor's load before use at high rates.

All three views fit inside the plot's allocated space with equal horizontal and
vertical scales per image pixel (within integer screen-pixel rounding). The
adjacent `image_geometry.py` Jython script measures the native plot's axes and
color-bar margins, then fits the raster to its reported width / height. It
rechecks after dimensions, data or selected view change, allowing delayed
JavaFX layout to settle. A 448-by-512 raster therefore has a 7:8 aspect ratio;
a rotated 512-by-448 raster uses 8:7 and leaves space below the plot. The
Intensity and acquisition panels stay beside the allocated plot area. This
fits the full image; independent X/Y zooms in the native plot can alter the
visible spatial scale. It does not compensate for physical detector gaps.

The **Intensity** panel sits to the right of the plot, with Auto at the top,
Max above the vertical slider and Min below it, matching the color bar's
high-to-low direction. Each view has independent intensity settings.
The panel is 110 pixels wide with 90-pixel Min / Max fields. Positive limits
below one billion display as whole numbers; larger limits use scientific
notation with four significant digits (for example, `1.845E+19`). Negative
limits switch at a magnitude of 100 million to leave room for the minus sign.
This formatting changes only the displayed text, preserving the applied limits.
**Auto** follows the minimum and
maximum of the full image, including zeros; the numeric fields show the applied
limits. Switch to **Manual** to freeze that range, then edit Min / Max or drag
the vertical **Max** slider beside the color bar. Typing a larger Max extends
the slider's range. Invalid or reversed limits restore the last valid range.
Switching views preserves each view's settings while the display is open.

Intensity controls require Phoebus Jython scripting and the adjacent
`image_intensity.py` file. The script computes limits with Java array statistics
and applies them with native plot autoscale disabled, because native autoscale
does not expose its effective limits. Use the screen's Auto / Manual button.
Autoscale covers the full waveform even when zoomed in; it performs one Java
array pass per changed waveform in Auto and none in Manual. Qualify this client
load at high publication rates. Reopen the Image tab to load display or script
changes; these intensity controls need no IOC restart.

Color limits affect only the display. Pixel values follow the selected Image
mode, such as ToT, and sums retain those native units; the display does not
convert them into photon counts or averages. Image widgets
use Channel Access waveforms, so the client must allow arrays large enough for
the 64-bit sum (at least 1835008 payload bytes for 448×512; allow overhead).

Rebuild the driver and database and restart the IOC during an approved idle
window to load the new readbacks before using this display. No live IOC
restart or detector qualification is implied by the local build checks.

## Next qualification evidence

Capture the preview's complete Serval destination readback, JSON header,
payload size, pixel format and one asymmetric raster whose orientation can be
verified. Before enabling full-rate image, PixelConfig or calibration
operations, establish their encoding, local raster order, read/write round
trips and coordinate placement independently.
