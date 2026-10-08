# Experimental Timepix4 initialization.
# Refresh detector readbacks first, then push only the qualified single
# preview destination. Detector setpoint writes, BPC/DACS uploads, PixelConfig,
# full-rate image, secondary preview, raw and histogram streams remain outside
# startup.

< profiles/tpx4/init/paths.cmd
dbpf("$(PREFIX)cam1:RefreshConnection", "1")
< profiles/tpx4/init/hw.cmd
