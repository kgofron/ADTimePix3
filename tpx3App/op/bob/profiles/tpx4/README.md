# Timepix4 Phoebus profile

`main.bob` is the conservative single-chip TPX4 shell used by the root
`TimePix4.bob` launcher. `Tpx4Status.bob` reports captured geometry and the
current qualification boundary. Its **Destinations** button opens
`Acquire/Tpx4ServerFileWriter.bob`, a TPX4-specific destination screen with
Preview.ImageChannels[0] and experimental Image[0] settings, setpoints and
readbacks, PVA delivery, and response status. Preview remains the qualified
startup path. Image[0] starts disabled. An emulator acquisition with Serval
4.1.6 demonstrated decoded Image arrays at the IOC; a complete requested run
still needs validation before operational use. `ArrayCounter_RBV` is cumulative
across acquisitions, so compare its values before and after each run rather
than comparing its absolute value with Serval's per-run frame count. The IOC
image TCP worker also requires `ImgAccumulationEnable=1`; the TPX4 startup
profile sets this while leaving `WriteImg=0`. The driver rejects a TPX4
destination push if raw, secondary
image or preview, or histogram flags are enabled. It also rejects a push
without either Preview[0] or Image[0], since an empty destination is not yet
a qualified way to clear the active Serval destination.

The profile intentionally omits PixelConfig, mask, BPC/DACS, secondary preview,
raw-event, histogram, MPX3 threshold, and emulator-control
panels. Do not copy those panels from TPX3 or MPX3 until their TPX4 behavior has
been captured and tested.

See `tpx3App/op/bob/README.md` and `iocBoot/iocTimePix/profiles/README.md`.
