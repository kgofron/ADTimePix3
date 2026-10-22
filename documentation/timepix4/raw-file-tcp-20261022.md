# TPX4 simultaneous raw file/TCP comparison, 2026-10-22

## Result

The pixel events in the **three completed shutter intervals match exactly**
between file and TCP output in both saved Serval/emulator 4.3.0 capture pairs.
Each output contains 300,000 selected events, including identical full 64-bit
pixel words and multiplicities. There are no file-only or TCP-only events
inside those intervals. Each frame contains 100,000 events: 50,000 per half.

| Capture pair | File events, entire capture | TCP events, entire capture | Selected events, each output | File-only trailing events |
|---|---:|---:|---:|---:|
| Raw file + TCP | 306,696 | 300,000 | 300,000 | 6,696 |
| Raw file + TCP + Image/Preview | 315,626 | 300,000 | 300,000 | 15,626 |

Every TCP pixel event is present in its paired file capture. All extra file
pixel events have coarse ToA at or after **0.3 s**, the final requested shutter
close. The files also contain a shutter rise at 0.3 s on each half without a
subsequent fall. TCP contains three complete intervals per half and no trailing
events. The file tails extend to approximately **0.306695 s** and **0.315625 s**.
The exact reason for their different tail lengths has not been established.

The byte-count differences reconcile as follows:

| Pair | File bytes | TCP bytes | Difference | Extra pixel bytes | Net extra headers/control/metadata bytes |
|---|---:|---:|---:|---:|---:|
| Raw file + TCP | 2,470,720 | 2,416,768 | 53,952 | 53,568 | 384 |
| With Image/Preview | 2,542,656 | 2,416,768 | 125,888 | 125,008 | 880 |

The first file has six more chunks than TCP, with 16 additional heartbeats,
two additional shutter rises and 24 additional metadata words. The second
has 14 more chunks, 38 additional heartbeats, two additional rises and 56
additional metadata words. Chunk headers are eight bytes and payload words
are eight bytes. Thus the size differences do not indicate missing in-frame
TCP events in these two captures.

## Method and reproducibility

The read-only Python standard-library diagnostic
[`test/compare_tpx4_raw.py`](../../test/compare_tpx4_raw.py) checks container
framing, chip-half mapping and the observed PID/PTS/MIN/MAX packet structure.
It unwraps **stored binary coarse ToA** against status timestamps and checks
the resulting values against each packet's coarse bounds. It pairs shutter
rise/fall markers independently for the two halves, requires identical
completed intervals between inputs, and selects each half-open interval
`[rise, fall)`. Both pairs have intervals [0, 0.1), [0.1, 0.2), [0.2, 0.3) s.

Event identity is `(stream, unwrapped coarse ToA, full 64-bit pixel word)`.
Multiset comparison preserves duplicates and includes encoded coordinate,
ToA, ToT, fine-time and flag bits. Chunk order, packet metadata and control
words are not used as pixel-event identities. Identical encoded fine-time
bits do not establish calibrated fine timing.

Run from the repository root:

```sh
python3 test/compare_tpx4_raw.py capture/raw_000000.tpx4 capture/tcp.bin > comparison.json
```

Exit status is 0 for equal selected events, 1 for event differences, and 2
for malformed, unsupported or incompatible input. The tool never connects
to Serval or writes the source captures. It retains event counters in memory
and is intended for small qualification captures, not sustained-rate replay.
Unsupported status types, including timestamp resets, are rejected.

The two commands on the saved pairs both returned **0**. Local JSON reports:

- `/tmp/tpx4-file-tcp-both.json`
- `/tmp/tpx4-file-tcp-coexist.json`

Source capture directories:

- `/tmp/tpx4-raw43-019jxc_m/both/`
- `/tmp/tpx4-raw43-9sz9lgkh/coexist/`

| Pair/input | SHA-256 |
|---|---|
| Raw file + TCP: file | `09d5c22bb98240bb03b9edff94525488d7f0d36a207a9130d9ea0212096eb5ef` |
| Raw file + TCP: TCP | `2ec7558d4c57ebe55fbdac5382afb5513c9765eb9c47c56808029df262de17c2` |
| With Image/Preview: file | `40fbda9a7d6423439e02ade8226ee3637748b8e7ece3cca8303b425666e491b3` |
| With Image/Preview: TCP | `808ab38e242e74e6982c3c10c6e75510bc24818792019b46758238b3fa01d170` |

Source hashes match those recorded before comparison. No new acquisition or
server/IOC configuration change was needed.

## Scope and next step

This resolves event equivalence for these **two short emulator captures**.
It does not establish physical hardware completeness, high-rate throughput,
long-run timestamp behavior, stop/restart behavior or precision timing. Both
outputs could share losses earlier in the pipeline. Stored packet IDs are
consecutive in each stream, but do not replace firmware sequence checking.

Raw output remains a reasonable development path on Serval 4.3. Consumers
must decide whether to retain all raw events or only completed shutter
intervals. Before a production decoder is accepted, resolve the fine-timestamp
edge cases from the [operator sample analysis](raw-sample-20261022.md).
The subsequent [lifecycle qualification](raw-lifecycle-20261022.md) covers
repeated starts/stops and finite runs up to five seconds. It found matching
full-frame events, with the interrupted frame retained only by the file when
explicitly stopping mid-frame. Higher rates still need independent accounting.
