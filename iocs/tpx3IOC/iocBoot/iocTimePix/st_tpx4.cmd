#!/bin/bash
# Experimental Timepix4 IOC launcher — runs the conservative single-chip profile.
cd "$(dirname "$0")"
mkdir -p autosave/tpx3 autosave/mpx3 autosave/tpx4
exec ../../bin/linux-x86_64/tpx3App profiles/tpx4/st.cmd "$@"
