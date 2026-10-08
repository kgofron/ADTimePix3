# Timepix4 Phoebus profile

`main.bob` is the conservative single-chip TPX4 shell used by the root
`TimePix4.bob` launcher. `Tpx4Status.bob` reports captured geometry and the
current qualification boundary. Its **Preview Destination** button opens
`Acquire/Tpx4ServerFileWriter.bob`, a TPX4-specific screen limited to the one
qualified preview channel and its PVA callback.

The profile intentionally omits PixelConfig, mask, BPC/DACS, full-rate image,
secondary preview, raw-event, histogram, MPX3 threshold, and emulator-control
panels. Do not copy those panels from TPX3 or MPX3 until their TPX4 behavior has
been captured and tested.

See `tpx3App/op/bob/README.md` and `iocBoot/iocTimePix/profiles/README.md`.
