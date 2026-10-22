# Deterministic protocol fixtures

This directory contains hardware-free C++ tests and reusable fake Serval
peers. The test product also compiles and exercises the production
`NetworkClient` implementation. Both peers bind only to the IPv4 loopback
address and allocate an ephemeral port, so tests cannot contact a real Serval
instance or detector.

Build and run the fixture tests with one command:

```sh
make -C test runtests
```

The fake TCP peer releases scripted chunks only when directed by the test. It
can close after the final chunk or remain silent until teardown. The fake HTTP
peer records one request and returns a configurable status, headers, and body;
its response can also be held until the test releases it. All fixture waits
take explicit deadlines, and fixture destruction stops and joins peer threads.

The test product exercises the production consume-once stream framer used by
PrvImg, Img, and PrvHst. Coverage includes every two-chunk split across two
messages, byte-at-a-time delivery, coalesced frames, binary newline/brace/NUL
bytes, short payloads, invalid and oversized headers, valid and invalid payload
terminators, bounded retained bytes, clean and truncated EOF, and
reconnect-buffer reset. The framer consumes one JSON header, exactly its
declared binary payload, and Serval's trailing newline while retaining only
bytes belonging to later messages. Image streams additionally accept Serval
4.3's exact space padding before the newline to align payload plus trailer to
eight bytes; histogram framing stays strict. Tests cover mixed legacy/aligned
messages at every split, bytewise trailers, all payload alignments and invalid
or truncated padding. Image fixtures also verify Serval `bitDepth` /
`dataSize` sizing for 8-, 16-, and 32-bit rasters, including MPX3 integrated
preview frames, and native-value decoding with both boolean `bigEndian`
settings (defaulting to big endian for legacy headers).

Worker-lifecycle coverage exercises the production atomic state protocol and
`NetworkClient` interruption path. Tests cover duplicate starts, stop and
failure transitions, a concurrent stop-versus-connect race, 100 repeated
start/stop cycles, idempotent teardown, and prompt wakeup of a receive blocked
on a silent loopback peer.

Acquisition-coordinator coverage exercises the production `Idle`, `Starting`,
`Running`, `Stopping`, and `Fault` transitions. Injected failures after every
startup resource verify complete rollback, truthful requested/observed state,
retry of unresolved remote cleanup, exactly one cleanup owner under concurrent
stop and fault requests, and bounded stream-readiness gates.

Reconnect-policy coverage drives the production read-only policy against fake
Serval HTTP peers. It verifies that automatic reconnect requests only
`GET /server/destination`, `GET /detector`, and `GET /measurement/config`, and
that a partial refresh is reported only after every required readback is tried.

The test product also exercises the production rectangular mask-geometry
helper. It verifies width-based row-major indexing, clipped rectangle/circle
drawing, non-mask-bit preservation, and rejection of undersized waveforms.
It also validates Serval raster geometry for 1x1, 2x2, and 4x2 detectors and
round-trips every pixel in a compact representation of the TPX3 two-quad
`2,1,4,7 / 3,0,5,6` mapping.

Verify that the checked-in synthetic 4x2 BPC and DACS files remain exact,
deterministic compositions of the existing 2x2 demo calibration:

```sh
python3 test/generate_tpx3_4x2_demo_calibration.py --check
```

## Image display intensity controls

Run the hardware-free Auto / Manual transition, range validation, per-view
state, scalar feedback, and BOB wiring checks with:

```sh
python3 test/test_image_intensity.py
```

The same file runs under Jython 2.7 (`jython test/test_image_intensity.py`).
Jython additionally exercises the script adapter with real Java array
statistics and mocked Phoebus scalar PVs. These checks do not render JavaFX;
verify the slider and color bar in Phoebus after reopening the Image tab.

Check square-pixel image fitting for portrait, landscape and square rasters,
different axis margins, and invalid dimensions with:

```sh
python3 test/test_image_geometry.py
```

These checks do not render JavaFX. Reopen the Image tab in Phoebus to verify
the native plot margins and view switches on the deployed client. The geometry
script travels with the BOB file and intensity script; no IOC restart is needed.

## TPX4 raw and histogram destination validation

The suite also validates TPX4 raw destination version/transport/queue/split
guards and independent applied JSON readbacks for both raw channels. Live
Serval/emulator captures and their limits are recorded under **Raw destinations
on Serval 4.3.0** in `documentation/timepix4/integration.md`.

Destination normalization fixtures also check native chooser paths, `/`,
trailing slashes and spaces, repeated normalization, unchanged file/HTTP/TCP
URIs, and continued allowlist rejection of traversal, sibling directories,
relative paths and malformed file URIs. The helper is shared by the raw,
image and preview image Base parameters across TPX3, MPX3 and TPX4; explicit
`file:` URIs supplied by existing scan clients pass through unchanged.
The integration guide records the earlier TPX4 isolated IOC checks of all six
existing path/readback pairs and applied raw channel JSON. Those checks do not
render the Phoebus chooser and have not been repeated for TPX3/MPX3 since
removing the detector-family restriction.

Compare saved Serval 4.3 single-chip raw file/TCP captures offline with:

```sh
python3 test/compare_tpx4_raw.py capture/raw_000000.tpx4 capture/tcp.bin > comparison.json
```

This standard-library diagnostic compares full pixel-word multisets and
unwrapped coarse ToA within matching completed shutter intervals. It retains
event counters in memory and is intended for small qualification captures.
Exit codes are 0 for equal selected events, 1 for differences, and 2 for invalid
or unsupported input. It does not qualify fine timing, throughput or hardware
completeness. See `documentation/timepix4/raw-file-tcp-20261022.md` for the two
saved-pair results.

For an explicit stop during a 100-ms frame, compare the full frames with:

```sh
python3 test/compare_tpx4_raw.py --frame-period-25ns 4000000 capture/raw_000000.tpx4 capture/tcp.bin > full-frames.json
```

This opt-in mode permits a shorter final interval per stream, records that
exclusion and both original interval sets, and still requires identical
selected full-frame intervals. Whole-capture differences remain visible.
Default mode continues to require identical completed shutter intervals.
The JSON v2 output includes `equivalent_within_selected_shutters` and the
selection scope; the earlier equality field remains as a compatibility alias.
See `documentation/timepix4/raw-lifecycle-20261022.md` for the strict interval
mismatches and explicit full-frame matches observed during manual stops.

The C++ fixture suite also checks that histogram destination readback preserves
Serval's actual applied channel, including its numeric settings, and rejects a
non-object channel before publication. These checks do not validate a TPX4
histogram payload or its time units. See `documentation/timepix4/integration.md`
for the emulator test results: the tested server accepts a TCP destination but
rejects acquisition start. The TPX4 channel and receiver remain blocked.

## Live IOC PixelConfig validation

After configuring Channel Access for the target IOC, validate all detected
chips with:

```sh
test/validate_pixel_config.sh TPX3-TEST:cam1:
# or
test/validate_pixel_config.sh MPX3-TEST:cam1:
```

The script reads `DetType_RBV` and `NChips_RBV`, triggers
`RefreshPixelConfig`, and validates the length, BPC match, mismatch count, and
status for every chip. TPX3 expects 65536 bytes per chip; dual-threshold MPX3
expects 131072. It exits nonzero if Channel Access fails or any chip does not
match the selected BPC file. Network-specific `EPICS_CA_*` values are
intentionally left to the caller's environment.

## Live Serval layout capture

Capture the complete detector `Info` and `Layout` objects for all eight
detector orientations with:

```sh
test/capture_mpx3_layouts.sh
test/capture_tpx3_layouts.sh
```

The scripts validate detector family and returned JSON, atomically write one
file per orientation under `.codex/layout-captures/`, and restore the original
orientation on exit. Optional positional arguments select the PV prefix,
Serval URL, and output directory. The captures are local evidence and are not
part of the normal test fixtures.

The script writes the orientation PV. Run it only against an emulator or an
idle detector. If multiple Channel Access servers publish the same prefix, set
`EPICS_CA_ADDR_LIST` and `EPICS_CA_AUTO_ADDR_LIST=NO` before starting so the PV
writes and the Serval HTTP endpoint refer to the intended system.

## ASI MPX3 reference fixture

`fixtures/mpx3/eq-02/` contains corresponding ASI-provided BPC and Serval chip
configuration examples. ASI permits their redistribution as example/test
configuration. They are detector-specific reference data, not a default
calibration; see the fixture README and license metadata.
