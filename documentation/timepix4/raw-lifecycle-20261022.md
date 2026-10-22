# TPX4 raw start/stop and longer-run qualification, 2026-10-22

## Results

Serval **4.3.0-EXPERIMENTAL** with the running TPX4 4.3 emulator completed
**15 acquisitions** through its HTTP API without restarting Serval or the
emulator. All returned to `DA_IDLE`, all raw TCP receivers reached EOF, and
all Serval-reported DroppedFrames counters were zero.

The file and TCP captures contain **10,900,000 identical pixel events per
output within 74 full frames**, across all runs. Full 64-bit pixel words,
unwrapped coarse ToA and duplicate counts match. These counts also agree
with the nominal emulator rate of one million pixel events per second.

| Cases | Acquisition | Full frames per run | Matching full-frame events per output/run | Comparison |
|---|---|---:|---:|---|
| `finite-01`–`finite-10` | Ten repetitions, 3 × 100 ms | 3 | 300,000 | Strict interval sets and events match |
| `manual-stop-01`–`manual-stop-03` | Request 100 × 100 ms; stop while recording after frame 3 | 3 | 300,000 | Full frames match; file also retains an interrupted frame |
| `finite-2s` | 10 × 200 ms | 10 | 2,000,000 | Strict interval sets and events match |
| `finite-5s` | 25 × 200 ms | 25 | 5,000,000 | Strict interval sets and events match |

The twelve finite captures passed the comparator's default strict mode.
Additional file events occurred after the final requested frame: 2,232–6,696
events for the short runs, 5,580 for the 2-second run and 4,464 for the
5-second run. Every TCP pixel event is present in its paired file capture.

## Explicit stop retains a partial frame only in the file

Each explicit stop was issued after observing `DA_RECORDING` and FrameCount=3.
The stop requests returned in approximately 0.403, 0.410 and 0.403 seconds.
These are HTTP request timings, not IOC stop latency measurements.

All three TCP captures end at the third full frame's shutter close, **0.3 s**.
Each file capture also contains a fourth shutter interval closed by the stop:

| Case | File-only interrupted interval | File-only pixel events |
|---|---|---:|
| `manual-stop-01` | [0.3, 0.329021 s) | 29,021 |
| `manual-stop-02` | [0.3, 0.331253 s) | 31,253 |
| `manual-stop-03` | [0.3, 0.320091 s) | 20,091 |

Thus whole-capture event equivalence fails for these explicit stops. The
default comparator correctly returns **2** because the completed shutter
interval sets differ. This is a difference in retained acquisition data;
it is not evidence of malformed file framing.

To inspect the full frames explicitly, the comparator now supports:

```sh
python3 test/compare_tpx4_raw.py --frame-period-25ns 4000000 capture/raw_000000.tpx4 capture/tcp.bin > full-frames.json
```

The value 4,000,000 specifies a 100-ms full frame in coarse 25-ns units. This
mode requires full intervals of that duration and permits one shorter final
interval per stream. Selected interval sets must still match between inputs.
Original intervals, excluded final partial intervals and whole-capture event
differences remain in the JSON. All three explicit-stop captures returned
**0** in this mode with 300,000 identical full-frame events per output.

Consumers requiring interrupted-frame events should use the raw file capture
on this tested setup. TCP consumers must account for its observed end at the
last full frame. The file and TCP outputs have different stop semantics here.

## Procedure and evidence

All runs used Continuous triggering, equal exposure/trigger periods, two Raw
destinations, `SINGLE_FILE` file splitting and QueueSize=16384. A TCP listener
was ready before each start. Each run used a separate directory and a fresh
TCP listener port, with destinations reapplied while idle. This exercises
repeated acquisitions and connection teardown in one Serval process; a
retained TCP listener/destination across runs was not exercised.

The harness verified a changed measurement StartDateTime, the expected finite
frame count or an explicit stop during recording, idle completion, TCP EOF
and a stable nonempty raw file. Two redundant stop requests were also issued
after each run and left Serval idle. Offline comparison then verified frame
counts against the shutter intervals and exact selected pixel-event multisets.

Local evidence is under `/tmp/tpx4-raw-lifecycle-n9bc7ggu/`:

- `baseline.json`, `plan.json` and `results.json`: saved settings, cases and
  acquisition/restoration results.
- Each case directory: file/TCP captures, applied destinations, measurement
  samples and strict comparison output/error.
- The explicit-stop directories also contain `comparison-full-frames.json`.
- `analysis-results.json`: twelve strict passes and three strict interval
  mismatches. The initial all-strict analysis harness exited with an assertion
  for those three mismatches; they are preserved as evidence.
- `manual-full-frame-results.json`: the three subsequent full-frame matches.
- `qualification-summary.json`: consolidated results.

The bounded acquisition and analysis harnesses are local temporary files
`/tmp/tpx4_raw_lifecycle.py`, `/tmp/analyze_tpx4_raw_lifecycle.py` and
`/tmp/analyze_tpx4_manual_frames.py`. The reusable offline comparator is in
[`test/compare_tpx4_raw.py`](../../test/compare_tpx4_raw.py).

[The derived result manifest](raw-lifecycle-20261022.json) records counts,
file sizes, comparison scope and SHA-256 hashes for all 30 source captures.
Every source hash was recomputed and matched after analysis.

## Restoration and qualification boundary

The original detector configuration and complete destination configuration
were restored. All four saved GET responses—detector configuration,
destination, measurement configuration and TDC configuration—matched after
restoration, with the final measurement idle. Measurement and TDC settings
were unchanged throughout. The operator IOC was not restarted or reconfigured.

This establishes bounded API-level behavior at approximately 1 million
emulated pixel events/s, with nominal acquisition durations up to five seconds.
It does not qualify IOC acquisition-worker lifecycle, sustained/high-rate
throughput, physical hardware loss accounting, precision timing, calibration
or ToF. Both outputs can share losses earlier in the pipeline. The known
[fine-timestamp edge cases](raw-sample-20261022.md) still require resolution
before accepting a production event decoder.
