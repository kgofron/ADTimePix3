# TPX4 raw sample check, 2026-10-22

## Sample and method

Checked `rawCgs000000.tpx4` read-only after the operator's three-frame
acquisition with Serval/emulator 4.3.0. The source file was not changed.

- Size: **4,869,392 bytes**.
- SHA-256: `c90bf2dd9ca244f6db81951dcbe1b0f88bbd32e278c61d12555c4aab1490d4d9`.
- Parsed little-endian `TPX4` chunk headers and 64-bit payload words.
- Cross-checked pixel classification, coordinates, ToT and timestamp fields
  using `Tpx4PixelData` and `TPX4.EOC` from the locally supplied Serval 4.3.0
  JAR. No acquisition or server configuration was changed.

Local diagnostic source, decoded CSVs and summary are in
`/tmp/tpx4-sample-check/` (`InspectTpx4.java`, `hits.csv`, `status.csv`,
`summary.json`). They are temporary analysis artifacts, not production decoder
code or repository fixtures.

## Results

| Check | Result |
|---|---|
| Container | 544 chunks; exact EOF; no partial header or payload |
| Streams | 272 chunks each for IDs 0 and 1 |
| Stream mapping | Every word's top/bottom bit matches its stream ID |
| Packet IDs | Consecutive 0–271 independently in each stream |
| Payload | 608,130 words: 604,464 pixels and 3,666 status/metadata words |
| Pixels | 302,232 per half; no invalid coordinates |
| Coordinate extent | x=0–447, y=0–511; all 229,376 pixels visited |
| Pixel occupancy | 83,664 pixels have two hits; 145,712 have three |
| Coarse ToT field | 0–2041; not a calibrated pulse-width result |
| Timing markers | 1,476 heartbeats, eight shutter rises, six shutter falls |

The two streams represent the two chip halves in this sample. They are not
evidence of two configured Raw destinations. Consecutive stored packet IDs do
not establish complete hardware UDP delivery: Serval can generate these IDs,
and the run explicitly lacked firmware sequence completeness checking.

### Acquisition intervals and trailing events

Both halves contain shutter rises at 0, 0.2, 0.4 and 0.6 seconds, and falls at
0.2, 0.4 and 0.6 seconds. Thus the three completed intervals agree with the
requested three 200-ms frames. An additional rise occurs at the final fall.

Unwrapping the stored binary coarse ToA against the status timestamps gives:

| Half-open interval | Pixel words |
|---|---:|
| [0, 0.2 s) | 200,000 |
| [0.2, 0.4 s) | 200,000 |
| [0.4, 0.6 s) | 200,000 |
| At or after 0.6 s | 4,464 |

The last hit is approximately 0.604463 s. Raw `SINGLE_FILE` therefore includes
a short tail after the final requested frame. Counting the entire file as
three frames would overcount this sample by 4,464 hits. These counts use coarse
25-ns timestamps; fine timing can move boundary hits between adjacent bins.
The tail's exact cause has not been established.

### Timestamp and decoder limitations

Serval's `Tpx4Timestamper` converts pixel ToA from Gray code to binary and adds
`SPIDR_PTS`, `SPIDR_MIN` and `SPIDR_MAX` metadata. The stored sample agrees with
that representation. Applying Gray decoding again is incorrect for this file.
TPX3's raw decoder and time constants cannot be reused unchanged.

For the diagnostic coarse unwrapping, all pixels fit their packet's coarse
time envelope after allowing the encoded fine-rise subtraction of up to 31
ticks of 1.5625 ns. A direct comparison with Serval's fine timestamp helper
found five boundary cases: four differed by one coarse-counter wrap at the
half-range boundary, and one returned its `-1` sentinel. These are recorded
decoder edge cases; this check does not qualify fine timing, ultra-fine timing,
calibration, ToF or a production event decoder.

ASI Luna **0.3.2** `tpx4dump`, in ASI input mode, failed in both raw-only and
sorting-without-clustering modes. It logged a timestamp underflow for the first
zero-valued pixel word, then panicked in its time-bin cache. Neither attempt
produced a usable HDF5 conversion. This establishes a compatibility problem
with that tool/sample combination, not that the intact container is corrupt.

## Next work

Raw channels are a reasonable development path on the current 4.3 pair. The
next useful step is an offline replay/accounting check that selects shutter
intervals explicitly and compares **events** between simultaneous file and TCP
captures. The previously observed file/TCP size difference remains unexplained;
this sample alone cannot establish equivalence or lossless delivery. Resolve
the timestamp edge cases before accepting a decoder for precision timing.
