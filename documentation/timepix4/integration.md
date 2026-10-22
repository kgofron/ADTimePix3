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

## Emulator command port and connection workaround

On 2026-10-21, the operator reported that TPX4 emulator 4.3.0 and Serval 4.3.0
sometimes failed to establish a usable detector connection. The emulator was
suspected to be listening on 50051. Enabling an explicit command-port override
of **50001**, then restarting the emulator, allowed Serval to connect. The
operator's emulator control screen showed **Cmd port (-DcmdPort)** set to
`50001`, its **Enable** toggle on, and the generated command:

```bash
java -DhitRate=1 -Dtdc=0 -DcmdPort=50001 -jar /path/to/tpx4Emulator-4.3.0.jar
```

Replace the JAR path with the installed emulator. The `-DcmdPort=50001` option
is a JVM property and belongs **before** `-jar`. Setting the numeric field in
the control screen without enabling its override does not establish that the
option is present; inspect the generated command and restart the emulator to
apply it. The example preserves the reported hit-rate and disabled TDC
settings; it does not qualify a ToF reference source.

This is an operator-confirmed workaround for the reported 4.3/4.3 setup,
not a demonstrated requirement for every version combination. Earlier logs
with emulator 4.3.0 and Serval 4.1.6 showed connection attempts on 50000,
50001 and 50051, including successful TCP connections on
50051. Some attempts were followed by `Request to spidr failed. Closing
connection to spidr.` A successful TCP connection alone therefore does not
prove a usable detector session. Port 50051 is not established here as an
always-failing port or the universal emulator default; the cause and frequency
of the intermittent failures remain unqualified.

Keep the emulator control port separate from the other endpoints:

| Endpoint | Port in this setup | Purpose |
|---|---|---|
| Emulator command interface | 50001 with explicit override | Serval-to-emulator detector control |
| Serval HTTP | 8081 | REST API and `/docs/` |
| Preview 0 TCP | 8089 initially | Sampled `jsonimage` delivery to the IOC |
| Image 0 TCP | 8087 initially | Full Image `jsonimage` delivery to the IOC |

The IOC may rotate occupied image-stream ports; use the applied destination
readback for their actual values. Changing an Image/Preview Base or Serval's
HTTP port does not change the emulator command port.

For an affected emulator setup:

1. Stop acquisition and stop the emulator before changing its command port.
2. Enable the 50001 override, verify `-DcmdPort=50001` in the generated
   command, and start the emulator. Ensure no other local emulator owns that
   port. A local `ss -ltn 'sport = :50001'` check can confirm a TCP listener,
   but cannot validate its detector protocol.
3. Start or reconnect Serval after the emulator is ready. Check for a usable
   TPX4 detector session, not just a successful socket connection: detector
   discovery should report TPX4, one chip and 448×512 geometry without repeated
   SPIDR request failures.
4. Start the TPX4 IOC to configure Preview. If Serval was restarted while the
   IOC remained running, explicitly apply the destination while idle; automatic
   reconnect refreshes readbacks without recreating the destination. A fresh
   Serval can legitimately report `Destination is not set.` until configured.
5. Verify a short Preview acquisition, then Image 0 if enabled. Record both
   JAR versions, the effective emulator command port and relevant connection
   logs when comparing runs. Other version combinations still need validation.

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

## Destination control

The TPX4 status panel opens `Acquire/Tpx4ServerFileWriter.bob`. This restricted
screen can edit and reapply Preview 0 and experimental Image 0. **Raw destinations**
opens the experimental Raw[0]/Raw[1] controls described below. After changing a field, use **Apply
Destination** to send the complete destination to Serval and refresh the
readbacks.

### Raw destinations on Serval 4.3.0

Open **Raw destinations** from Destinations. Raw output is disabled at IOC
startup and can be enabled manually with Serval **4.3.0**, including the tested
`4.3.0-EXPERIMENTAL` build **1966**, and TPX4 emulator **4.3.0**. Other Serval
versions remain blocked for TPX4 raw output until separately qualified.

Each channel exposes **File path / destination URI**, **File prefix / pattern**,
file split strategy and queue size. These retain the TPX3 PV mapping:

| Channel | File path / destination URI (`Base`) | File prefix / pattern (`FilePattern`) |
|---|---|---|
| Raw[0] | `RawFilePath` | `RawFileTemplate` |
| Raw[1] | `Raw1FilePath` | `Raw1FileTemplate` |

The prefix may be a literal run name such as `scan_0042_`, or include a time
pattern such as `raw%Hms`. Serval appends a counter and the `.tpx4` extension;
omitting the time pattern does not suppress the counter. An acquisition client
can update the prefix for each run while retaining the configured directory.
There is no separate raw `FileName` PV, and writing a file plugin's `FileName`
does not update Serval's raw destination. The Serval pattern is not the
areaDetector file plugin's printf-style `FileTemplate`.

Configure while idle and use **Apply destination**. This sends
all enabled Raw, Image and Preview channels together. Enable Raw[0] before
Raw[1]; disabling Raw[0] requires disabling Raw[1] too. Raw-only destinations
are permitted. The separate applied JSON readbacks, `RawDestination_RBV` and
`Raw1Destination_RBV`, come from `GET /server/destination`; `{}` means absent.
The individual path and pattern readbacks reflect requested parameters stored
by the IOC; path values include URI normalization. The raw screen shows the
existing `_RBV` PVs in blue above each path and prefix field, together with
**Exists (IOC)** beside the path readback. These are not final generated
filenames. Existence is checked on the IOC computer;
TCP/HTTP values do not imply a successful connection. The applied JSON remains
the readback of what Serval accepted.

Each raw channel has one native Phoebus **File Selector** button beside
**File path / destination URI**, configured to select a directory. It writes the
selected absolute path to that channel's existing `RawFilePath` or
`Raw1FilePath` PV. The shared driver handling adds `file:` before path
validation and destination allowlist checks for TPX3, MPX3 and TPX4;
explicit file and TCP URIs retain their existing validation. Existing scan
clients that already prepend `file:` retain the same URI without a second
prefix. No script or extra PV is used. **File prefix / pattern** remains a text
field for literal run prefixes and time patterns; it has no chooser. Cancelling leaves the path
unchanged; use **Apply destination** after accepting the selection.
The editable field can retain the chooser's plain path; the blue readback
shows the `file:/...` value used by the driver. The same conversion is
available for Image 0/1 and Preview Image 0/1 Base parameters across the three
detector families. Their existing channel qualification and enable guards
continue to apply.
These choosers browse the **Phoebus computer**, so the selected directory must
also exist at the same path on the Serval computer. For remote-only directories
or TCP destinations, enter the Base URI directly. Rebuild and restart the IOC
to load the path conversion, then reopen Raw destinations for the new buttons.

The earlier TPX4-only directory normalization implementation passed the
application and IOC builds and all **407** protocol fixture checks. An isolated
IOC against a local fake Serval verified all six Base parameters with plain
directories, repeated selections, explicit `file:` URIs, `/`, HTTP and TCP URLs.
Both raw channels independently applied
the expected normalized Base values and retained their file patterns. TCP
values passed through unchanged; raw HTTP was still rejected before PUT.
The existing root-directory check was fixed to preserve `/` before `stat`.
Earlier native-selector/path-readback BOB wiring checks passed for both raw
channels. The updated labels, prefix readbacks and chooser interaction still
need a visual Phoebus check. No automated tests were rerun for the screen
text/layout update or the extension of normalization to TPX3 and MPX3. The
shared driver library rebuilt successfully after removing the detector-family
restriction. The acquisition client's handling of directories versus complete
filenames remains a separate integration check; adding URI normalization does
not change that contract.
Local evidence is under `/tmp/tpx4-directory-ioc-n_v8o0jw/`; this test used no
running operator IOC, Serval, emulator or detector.

- `file:/absolute/directory` writes `.tpx4` files on the **Serval computer**.
  The directory must exist and be writable there. The split choices are
  `single_file` and `frame`.
- `tcp://connect@localhost:PORT` sends binary events to an external receiver
  that must already be listening before acquisition starts. A raw TCP receiver
  is not provided by this IOC. The IOC's image TCP receivers do not consume raw
  channels. TCP output uses Base and QueueSize; file pattern and splitting are
  omitted from the request.
- HTTP raw output is rejected. Queue size must be positive, and the destination
  must also pass the configured destination allowlist.

Do not point a raw consumer at the Preview/Image `jsonimage` decoder. Raw data
has a separate binary format. The captures begin with `TPX4`, but no production
event decoder, time units, heartbeat reconstruction or event accounting were
qualified here. The existing TPX3 raw appendix and clock constants cannot
establish TPX4 decoding.

#### Operator file-writing check, 2026-10-22

After the shared destination-path normalization (`0725ee1`) and TPX4 raw
screen changes (`ecdce46`), the operator reported testing TPX4 Image, Preview
and Raw file writing and finding that they worked. This records an
operator-reported functional check of the updated implementation.

The report did not include acquisition settings, durations, saved-file
inspection results or confirmation of each channel's chooser interaction.
It does not extend the earlier throughput, timing or data-completeness
qualification. TPX3 and MPX3 acquisition compatibility, including the scan-server
workflow that already supplies `file:/`, remains to be checked.

#### Qualification, 2026-10-22

The locally installed `20251202_ASIServer_TPX3_manual_V4.1.3.pdf`, supplied with
the **4.1.7** package, was checked alongside its Python acquisition example and
release notes. The manual documents Raw destination controls and a **TPX3** raw
format appendix (section 6.1); it does not document a TPX4 packet contract. The
vendor's separate TPX4 Python acquisition example in the 4.1.6 TPX4 package
also explicitly configures a Raw file destination. These examples include
detector and calibration writes, so they were read as documentation rather
than executed unchanged.

Five direct API captures used three 0.1-second Continuous frames each on the
running 4.3 pair, at an observed emulator pixel rate of about 1 million/s:

| Destination | Result |
|---|---|
| Raw file, `SINGLE_FILE` | One nonempty `.tpx4` file, 2,470,720 bytes |
| Raw file, `FRAME` | Three nonempty `.tpx4` files, 805,600 / 805,584 / 805,584 bytes |
| Raw TCP connect | 2,416,768 bytes, receiver reached EOF |
| Raw file + raw TCP | Both nonempty; file 2,470,720 bytes, TCP 2,416,768 bytes |
| Raw file + TCP + Image/Preview TIFF files | Both raw outputs nonempty; three Image and three Preview TIFF files |

All five runs completed with FrameCount=3, DroppedFrames=0 and final
`DA_IDLE`. These are Serval-reported counters, not proof of complete raw event
delivery. Simultaneous file and TCP output was **not byte-identical**. The
release notes say `SINGLE_FILE` output is written before sorting. A subsequent
[offline comparison](raw-file-tcp-20261022.md) found exact pixel-event
equivalence within the three completed shutter intervals in both simultaneous
captures: 300,000 events per output. Extra file events were all after the final
shutter close; additional event/framing/control bytes reconcile the size
differences. Neither output is accepted as a reference for complete hardware
delivery. Original detector configuration, destination, measurement
configuration and TDC configuration were restored and compared after probing.

Local capture evidence is under `/tmp/tpx4-raw43-019jxc_m/` and
`/tmp/tpx4-raw43-9sz9lgkh/`; these temporary files are not repository fixtures.
The C++ fixture suite covers independent applied raw readbacks, removed/sparse
channels, version gating, unsupported HTTP, invalid queue sizes and splitting.

The rebuilt driver and IOC were also exercised in an isolated IOC instance.
Applying a raw-only file destination and acquiring three frames passed;
`NumImagesCounter_RBV` reached 3 without Preview enabled. The monitor now
publishes measurement progress independently of Preview. Attempts to apply
Raw[1] without Raw[0], HTTP raw output, or a histogram destination were rejected
without changing the applied destination. Applied Raw[0] JSON was read through
the database record. Local final smoke evidence is under
`/tmp/tpx4-raw-ioc-jecy4w1i/`. The validation IOC exited and all four original
configuration snapshots were restored and compared; the final state was idle.

The application and IOC build, all **391** protocol fixture checks, and the
Phoebus XML and prefix/macro checks passed. The new screen has not been
visually checked in Phoebus. Restart the operator's IOC to load the rebuilt
driver/database, then reopen Destinations to access **Raw destinations**.

#### Operator acquisition, 2026-10-22

The operator subsequently reported a successful acquisition through the
operator IOC with Raw[0] file output and Preview 0 TCP `jsonimage` enabled.
The file listing showed `rawCgs000000.tpx4`, **4,869,392 bytes**. Applied
destination readback confirmed `SINGLE_FILE`, queue size 16384 and file pattern
`raw%Hms`. The run used three 200-ms Continuous frames at 5 Hz, reported
FrameCount=3 and DroppedFrames=0, and finished in `DA_IDLE`. This was
operator-provided file/log evidence. A subsequent read-only check of the sample
found intact framing, 604,464 pixel words, valid coordinates and the expected
three shutter intervals, plus 4,464 hits after the final shutter close. See the
[sample analysis](raw-sample-20261022.md) for decoder limitations and evidence.

An earlier `file://...` entry was rejected by the IOC; the applied destination
used the required `file:/...` form. The Preview peer-close message is consistent
with the end of a finite acquisition and does not by itself establish a stream
failure. Serval explicitly warned that the reported firmware does not support
sequence headers and that data completeness checking is unavailable. Zero
reported dropped frames therefore does not establish lossless raw event
delivery. Its log also reported two raw writers despite the applied JSON
containing one Raw destination; that internal writer count has not been
explained and is not evidence of a second configured Raw channel.

Serval **4.1.7 has not been run in this qualification**. Its release notes list
SPIDR4 discovery and TPX4 equalization improvements and a stop/finite-run
deadlock fix, without a listed TPX4 raw or histogram fix. It remains a separate
compatibility check; the running 4.3 service was preserved.

#### Repeated start/stop and longer runs, 2026-10-22

The subsequent [lifecycle qualification](raw-lifecycle-20261022.md) completed
ten short finite runs, three explicit stops while recording, and 2-/5-second
finite runs on the same 4.3 pair. File and TCP output matched across all 74
full frames: 10.9 million selected events per output. Explicit stops exposed
a further distinction: the file retains a closed interrupted frame while TCP
ends after the last full frame. Whole-capture equivalence therefore does not
hold for those stops. The original settings were restored and compared after
all 15 API runs; the final state was idle. IOC acquisition-worker lifecycle,
precision timing, hardware completeness and sustained throughput remain
unqualified.

### Histogram destination compatibility

Open **Histogram destination** from Destinations. The separate
`Acquire/Tpx4HistogramDestination.bob` screen preserves the main screen's size
and displays Base, file pattern, format, mode, bin count, bin width, offset,
integration, queue size and disk-limit settings in the same style as Image.
Settings and Apply are read-only because the tested Serval 4.1.6-EXPERIMENTAL
and 4.3.0-EXPERIMENTAL TPX4 paths fail at histogram acquisition start. The driver rejects histogram
enable before a destination PUT, so it cannot replace working Image/Preview
outputs with a configuration known to fail. `CapTofHist_RBV` remains false.

Requested settings are distinct from `PrvHstDestination_RBV`, which contains
the first histogram channel actually returned by `GET /server/destination`,
or `{}` when absent. The Applied indicator means that a destination exists;
it does not establish that acquisition can start. Preview image and histogram
channels share the Preview period and sampling mode.

The TPX4 profile starts with `WritePrvHst=0` and
`PrvHstAccumulationEnable=0`, including after autosave restoration. Unapplied
candidate defaults are TCP listen on localhost:8085, `jsonhisto` (existing enum
value 4), `tof`, 1000 bins, bin width `0.000001`, offset 0, integration 1 and
queue size 160. No enum values are renumbered. The screen does not label bin
width/offset in ms or apply the TPX3 clock constant. The TPX4 acquisition path
also excludes the legacy TPX3 histogram receiver.

#### Emulator qualification, 2026-10-21

The tested pair was TPX4 emulator **4.3.0** and Serval
**4.1.6-EXPERIMENTAL, build 1760**. The emulator was launched with
`-DhitRate=1 -Dtdc=0`; simulated TDC generation was disabled. These results do
not establish the behavior of Serval 4.3. Disabled TDC generation also means
that a meaningful ToF test would need a qualified reference source; it does
not explain away the destination validation errors or startup exception below.

The running OpenAPI schema advertises `Preview.HistogramChannels[]`, mode
`tof`, preferred format `histogram`, and TPX4 `/detector/tdc` controls. It
calls `jsonhisto` deprecated and still labels `MeasurementTOFConfig` as TPX3.
Short, explicitly authorized tests on the TPX4 emulator found:

| Request | Result |
|---|---|
| Histogram destination, `Format=histogram` | PUT 400: `Format may not be histogram for a histogram channel. Supported formats: 'jsonhisto'.` |
| `jsonhisto` / `tof`, HTTP base | PUT 400: `Unsupported format 'jsonhisto' for scheme http. Supported formats: 'tiff', 'pgm', 'png'.` |
| `jsonhisto` / `tof`, TCP connect base | PUT 200; GET readback confirms the requested histogram settings |
| Start measurement with that accepted TCP destination | GET 500: `Histopars can only be defined for TPX.` |
| `jsonhisto` / `count`, TCP base | PUT 400: `Mode 'count' is currently not supported for histograms. Supported: 'tof'.` |

The bounded startup test requested three triggers, with continuous exposure
and trigger period both 0.1 s. Serval requires those periods to be equal in
Continuous mode. No histogram frame was produced. The probe stopped the
attempted measurement and restored the original detector configuration and
complete destination configuration; subsequent GETs matched both originals.
The original timing was 1000 triggers with exposure/period both 0.2 s.
TDC and measurement-processing settings were read but not changed. Full raw
responses remain local evidence; only these derived facts belong in Git.

The supplied server log and saved HTTP responses establish this sequence
(local log times):

- At 17:16:53, histogram start returned HTTP 500 with an
  `IllegalStateException` in `DataMeasurement.createChannels`. Stop and both
  configuration restorations then returned HTTP 200, and GET readbacks matched
  the saved detector and destination configurations.
- At 17:18:27, the same server handled the `count` destination request and
  returned HTTP 400. Its restorations also completed and matched the snapshots.
- At 17:23:24, `tpx3servalDriver:stopProcess` logged SIGTERM and then SIGKILL;
  `startProcess` launched Serval again. The log does not identify the restart
  trigger or establish a spontaneous JVM crash.

A read-only check after that restart found Serval responding, but dashboard
`Measurement` and measurement `Info` were null, and `GET /server/destination`
returned HTTP 409, `Destination is not set.` This is a later server state,
distinct from the verified restoration before the restart. No configuration
was reapplied during that check. Successful image acquisition after the failed
histogram start was not tested in that initial sequence.

After the operator restarted the emulator, Serval and IOC and confirmed normal
Preview acquisition, the histogram test was repeated at 17:34:06. The fresh
baseline was Continuous mode, 1000 triggers and exposure/period both 0.02 s,
with the configured Preview 0 `jsonimage` destination. The same TCP
`jsonhisto` / `tof` destination was accepted, and the three-trigger start again
returned HTTP 500, `Histopars can only be defined for TPX.` Detector and
destination settings were restored and verified by GET readbacks.

A subsequent Preview recovery test used the saved Preview settings with only
its Base changed to a temporary local TCP connect receiver. It requested at
most 20 triggers with exposure/period both 0.1 s, started successfully, and
received one complete, nonzero 448×512 `jsonimage` frame: `bitDepth=16`,
`dataSize=458752`. The test stopped after receiving that frame, restored the
original detector configuration and complete destination, and verified exact
equality for those plus the unchanged measurement-processing and TDC settings.
The final dashboard status was `DA_IDLE`. This establishes raw Preview delivery
after the histogram startup failure; IOC/PVA delivery was not tested because
Channel Access queries from the test session timed out. No histogram payload,
bin timing or event accounting was validated.

The operator subsequently confirmed that the IOC could acquire after the
retest. The supplied screen showed Connected, Idle and 90 server images
complete, while areaDetector Images Acquired remained 0. This adds operator
confirmation of IOC acquisition recovery; it does not independently establish
image callbacks or PVA display delivery.

A Serval build that successfully starts TPX4 histogram acquisition is needed
before enabling this channel. Then capture the supported wire format, payload,
matching TDC/reference, bin units, event accounting and bin centers from one
run. That evidence is required before implementing the receiver and a ToF
plot. The planned plot can offer latest, Last-N and accumulated views with
linear/log axes and retained results after Stop, following the Image screen.

#### Serval 4.3 qualification, 2026-10-21

The operator next upgraded to Serval **4.3.0-EXPERIMENTAL, build 1966** with
the 4.3.0 emulator. The IOC rejected Preview with `invalid or missing frame
payload terminator`; Serval then logged a broken pipe after the receiver
disconnected. This was a framing incompatibility, not evidence that the
detector acquisition pipeline stopped processing frames.

Bounded captures of Preview and full Image each returned a nonzero 448×512
ToT raster with `bitDepth=16`, `dataSize=458752` and `bigEndian=true`. Serval
4.3 pads its JSON header with spaces before the closing brace, then LF, to an
eight-byte boundary. After the declared binary payload it writes
`7 - (dataSize % 8)` spaces, followed by LF. Both captured rasters therefore
had trailer bytes `20 20 20 20 20 20 20 0a`. The payload size excludes padding.
Inspection of the installed writer confirmed this alignment rule; Serval
4.1.6 instead writes LF immediately after the payload.

The shared Preview/Image decoder now accepts either the legacy LF or exactly
the aligned space padding plus LF after the declared payload. It never scans
binary pixels for delimiters, still enforces metadata and buffer limits, and
rejects malformed or excessive padding. The histogram framer retains its
strict LF policy. Preview and Image decoding honor boolean `bigEndian`
metadata and default to big endian when absent, preserving legacy behavior.

All 384 protocol fixture tests passed, including every TCP split and bytewise
delivery across mixed legacy/aligned messages, all eight payload alignments,
malformed/truncated padding, and native-value decoding for both byte orders.
Captured Preview and Image payloads were replayed through the production
framer/decoder in 137-byte chunks, using their padded headers/trailers and two
successive frames. Decoded pixel sums and maxima matched an independent
Python reference. Driver and IOC builds passed. After restarting the IOC,
the operator confirmed Preview display with Serval 4.3 and supplied a screen
showing the received image and 83 server images complete. This confirms the
live Preview display path with the rebuilt decoder. The shared Images Acquired
counter was still 0 in that screen, so it is not a reliable indicator of
Preview display delivery in this setup.

The operator subsequently enabled Image 0 alongside Preview and confirmed
display in all three Image monitor views: latest frame, Last-N sum and
accumulated sum. Both destinations used TCP listen `jsonimage` / `tot` with
integration size 1. The supplied Image screen showed 448×512 geometry, 99
received and accumulated messages, a rolling occupancy of 10 and a last-message
rate of 52.08 Hz. These observations establish functional display of both
channels with Serval 4.3; they do not qualify sustained throughput, packet-level
completeness or retained results after Stop. Connection-close messages in the
supplied log do not alone identify an error or establish the acquisition state
at each close.

A separate three-trigger TPX4 histogram test against Serval 4.3 again accepted
TCP `jsonhisto` / `tof` but rejected measurement start with HTTP 500,
`Histopars can only be defined for TPX.` The captured 4.3 OpenAPI schema still
labels `MeasurementTOFConfig` as TPX3. Histogram output remains blocked.
Each live probe restored the detector configuration and original Preview
destination and verified their GET readbacks. Image capture after the failed
histogram attempt succeeded; its final check also verified unchanged
measurement-processing/TDC settings and `DA_IDLE`.

#### Remaining upgrade qualification

For subsequent upgrades, record both emulator and Serval versions and capture
the new OpenAPI schema.
For Preview and full Image separately, capture `jsonimage` headers and payloads
and verify framing, payload length, numeric types, byte order, dimensions and
orientation against the decoder. Recheck destinations, acquisition start/stop,
and retained image results rather than assuming compatibility from the format
name. For histograms, qualify the accepted format and transport, successful
startup, payload decoding, matching TDC/reference generation, bin units and
centers, and event accounting. Include a normal image acquisition after any
failed histogram attempt to verify recovery. Keep the TPX4 histogram capability
disabled until these checks establish a working path.

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
