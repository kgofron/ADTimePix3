# Push the minimum qualified Timepix4 destination to Serval.
#
# paths.cmd enables only Preview.ImageChannels[0]. WriteData builds and sends
# Server.Destination, then refreshes the destination readbacks. The PVA plugin
# receives the driver's decoded preview NDArrays on address 0.

epicsThreadSleep(1)
dbpf("$(PREFIX)cam1:WriteData", "1")
dbpf("$(PREFIX)Pva1:EnableCallbacks", "1")
