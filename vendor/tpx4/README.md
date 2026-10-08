# Timepix4 calibration boundary

No TPX4 calibration files are shipped. The captured Serval 4.1.6 experimental
PixelConfig response is 229376 bytes for one 448×512 chip, but that byte count
does not establish bit meanings, local raster order, writable representation,
or a distributable BPC/DACS file format.

The driver therefore blocks TPX4 PixelConfig comparison, operator masks and
BPC/DACS uploads. When those contracts are qualified, place reviewed fixtures
under a geometry-specific directory such as:

```
vendor/tpx4/
  1x1/
```

Do not adapt TPX3/MPX3 calibration files by size alone.
