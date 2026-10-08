#!../../bin/linux-x86_64/tpx3App

< envPaths

< profiles/tpx4/unique.cmd
< common/st_core.cmd

< $(ADCORE)/iocBoot/commonPlugins.cmd
< profiles/tpx4/autosave.cmd
< $(ADCORE)/iocBoot/stats_profiles.cmd

set_requestfile_path("$(ADTIMEPIX)/tpx3App/Db")

iocInit()

# Conservative initialization: detector discovery plus one preview destination.
# No detector setpoint, PixelConfig, BPC, DACS, full-rate image, secondary
# preview, raw or histogram push occurs.
< profiles/tpx4/init/detector.cmd

set_requestfile_path("profiles/tpx4")
create_monitor_set("auto_settings.req", 30, "P=$(PREFIX)")
