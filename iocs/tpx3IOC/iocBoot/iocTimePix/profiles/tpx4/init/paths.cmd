# Timepix4 image-channel defaults. These update local PV state only; hw.cmd
# performs the explicit push to Serval after detector discovery.
#
# The qualified minimum is one Preview.ImageChannels[0] jsonimage stream on
# TCP 8089. Image[0] is configured locally for experimental validation but
# remains disabled at startup. Secondary channels, raw and histogram remain
# blocked by the TPX4 destination guard.

# Clear all unqualified destination flags, including values restored by
# autosave, before the TPX4 destination is applied.
dbpf("$(PREFIX)cam1:WriteRaw", "0")
dbpf("$(PREFIX)cam1:WriteRaw1", "0")
dbpf("$(PREFIX)cam1:WriteImg1", "0")
dbpf("$(PREFIX)cam1:WritePrvImg1", "0")
dbpf("$(PREFIX)cam1:WritePrvHst", "0")

dbpf("$(PREFIX)cam1:ImgFilePath", "tcp://listen@localhost:8087")
dbpf("$(PREFIX)cam1:ImgFileTemplate", "f%MdHms_")
dbpf("$(PREFIX)cam1:ImgFileFmt", "3")
dbpf("$(PREFIX)cam1:ImgFileMode", "1")
dbpf("$(PREFIX)cam1:ImgIntgSize", "1")
dbpf("$(PREFIX)cam1:ImgIntgMode", "0")
dbpf("$(PREFIX)cam1:ImgStpOnDskLim", "0")
dbpf("$(PREFIX)cam1:ImgQueueSize", "160")
dbpf("$(PREFIX)cam1:ImgAccumulationEnable", "1")
dbpf("$(PREFIX)cam1:WriteImg", "0")

dbpf("$(PREFIX)cam1:PrvImgFilePath", "tcp://listen@localhost:8089")
dbpf("$(PREFIX)cam1:PrvImgFileTemplate", "f%MdHms_")
dbpf("$(PREFIX)cam1:PrvImgFileFmt", "3")
dbpf("$(PREFIX)cam1:PrvImgFileMode", "1")
dbpf("$(PREFIX)cam1:PrvImgIntgSize", "1")
dbpf("$(PREFIX)cam1:PrvImgIntgMode", "0")
dbpf("$(PREFIX)cam1:PrvStpOnDskLim", "0")
dbpf("$(PREFIX)cam1:PrvImgQueueSize", "160")
dbpf("$(PREFIX)cam1:PrvPeriod", "1.0")
dbpf("$(PREFIX)cam1:WritePrvImg", "1")
