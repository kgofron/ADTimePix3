# Detector family profiles (Option C layout)

One IOC app (`iocTimePix`) shares driver code; each **profile** is a self-contained startup package.

## Layout

```
iocBoot/iocTimePix/
  st.cmd                 → profiles/tpx3/st.cmd
  st_mpx3.cmd            → profiles/mpx3/st.cmd
  st_tpx4.cmd            → profiles/tpx4/st.cmd (experimental single chip)
  envPaths, load_chips.cmd
  common/
    st_core.cmd          # driver + cam1 DB + Image1 (all families)
  templates/
    hdf5/                # NDFileHDF5 hdf5_layout XML
    nexus/               # NDFileNexus NXroot templates (legacy; see templates/README.md)
  profiles/
    tpx3/                # Timepix3
    mpx3/                # Medipix3
    tpx4/                # experimental 448×512 single-chip readback profile
  autosave/
    tpx3/  mpx3/  tpx4/
```

Calibration files: `vendor/tpx3/`, `vendor/mpx3/`, `vendor/tpx4/` (see `vendor/README.md`).

Phoebus screens mirror this layout under `tpx3App/op/bob/` (see `tpx3App/op/bob/README.md`).

## Profile contract

Each `profiles/<family>/st.cmd` follows the same sequence:

1. `< envPaths`
2. `< profiles/<family>/unique.cmd` — PORT, PREFIX, SERVER_URL, mosaic, MASK_BPC_NELEMENTS
3. `< common/st_core.cmd`
4. `< profiles/<family>/plugins_*.cmd` — optional (MPX3 only today)
5. `< commonPlugins.cmd`, `< autosave.cmd`, `< stats_profiles.cmd`
6. `iocInit()`
7. `< init/detector.cmd`, then `set_requestfile_path("profiles/<family>")` and `create_monitor_set("auto_settings.req", …)` — **basename only** for the req file so `.sav` lands in `./autosave/<family>/`, not a nested `profiles/…` path.

## Init scripts (re-runnable from iocsh)

| File | Purpose |
|------|---------|
| `init/paths.cmd` | TCP paths, templates, BPC/DACS file paths (no SERVAL push) |
| `init/hw.cmd` | WriteData, BPC/DACS upload, TriggerMode, plugins |
| `init/detector.cmd` | paths + hw + RefreshConnection |

MPX3 optional: `init/img.cmd`, `init/hdf5_img.cmd`, `init/hdf5_img_arm.cmd`, `init/hw_equalize.cmd`.

## Experimental TPX4 profile

`st_tpx4.cmd` starts a deliberately conservative single-chip profile for the
captured Serval 4.1.6 experimental geometry (`448×512`, one chip). It loads the
shared IOC core, performs detector discovery, and configures one
`Preview.ImageChannels[0]` jsonimage stream on TCP port 8089. `Pva1` callbacks
are enabled for `pva://TPX4-TEST:Pva1:Image`.

It does not restore detector setpoints, upload BPC/DACS, refresh PixelConfig,
or configure full-rate image, secondary preview, raw or histogram channels.
Those paths remain fail-closed until their TPX4 contracts are qualified. Do
not construct another TPX4 profile by copying the TPX3 tree wholesale.

## Site overlays

Keep beamline-specific edits in gitignored files, e.g. `profiles/tpx3/init/paths_site.cmd`, and source them from a local wrapper — do not fork the whole profile in git.
