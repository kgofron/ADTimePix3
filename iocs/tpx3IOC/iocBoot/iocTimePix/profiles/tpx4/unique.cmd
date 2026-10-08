# Experimental Timepix4 single-chip profile parameters.

epicsEnvSet("SUPPORT_DIR",               "../../../../..")
epicsEnvSet("ENGINEER",                  "K. Gofron")

epicsEnvSet("PORT",                      "TPX4")
epicsEnvSet("IOC",                       "iocADTimePix")
epicsEnvSet("IOCNAME",                   "tpx4")
epicsEnvSet("HOSTNAME",                  "localhost")

epicsEnvSet("EPICS_CA_AUTO_ADDR_LIST",   "NO")
epicsEnvSet("EPICS_CA_ADDR_LIST",        "255.255.255.0")
epicsEnvSet("EPICS_CA_MAX_ARRAY_BYTES",  "6000000")

epicsEnvSet("QSIZE",                     "30")
epicsEnvSet("NCHANS",                    "2048")
epicsEnvSet("HIST_SIZE",                 "4096")

# Captured Serval 4.1.6 experimental single-chip geometry.
epicsEnvSet("XSIZE",                     "448")
epicsEnvSet("YSIZE",                     "512")
epicsEnvSet("MASK_BPC_NELEMENTS",        "229376")

epicsEnvSet("NDTYPE",                    "Int16")
epicsEnvSet("NDFTVL",                    "SHORT")
epicsEnvSet("CBUFFS",                    "500")

epicsEnvSet("SERVER_URL",                "http://localhost:8081")
epicsEnvSet("PREFIX",                    "TPX4-TEST:")

# PixelConfig/BPC/DACS operations are blocked by the driver for TPX4 until
# their encoding and coordinate contracts are qualified. Keep the shared
# containment variables defined because common/st_core.cmd loads shared DBs.
epicsEnvSet("ADTIMEPIX_CALIBRATION_ROOT", "/")
epicsEnvSet("ADTIMEPIX_DESTINATION_ALLOWLIST", "file:/*,tcp://*,http://*")
