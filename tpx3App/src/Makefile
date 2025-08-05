TOP=../..
include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE

ifeq (windows-x64, $(findstring windows-x64, $(T_A)))
USR_CPPFLAGS += -D__X64
endif

# Performance optimizations
USR_CPPFLAGS += -std=c++11 -DNDEBUG
USR_CXXFLAGS += -O3 -march=native -mtune=native -flto -ffast-math
USR_CXXFLAGS += -funroll-loops -finline-functions -fomit-frame-pointer
USR_CXXFLAGS += -DPREFIX_MAGICK_SYMBOLS

# Memory optimizations
USR_CXXFLAGS += -fno-rtti -fvisibility=hidden -fvisibility-inlines-hidden

# Link-time optimizations
USR_LDFLAGS += -flto -Wl,--gc-sections

INC += ADTimePix.h

USR_INCLUDES += $(addprefix -I, $(GRAPHICSMAGICK_INCLUDE))

LIBRARY_IOC = ADTimePix
LIB_SRCS += ADTimePix.cpp
LIB_SRCS += mask_io.cpp

LIB_SYS_LIBS += cpr curl-d z

DBD += tpx3Support.dbd

#=============================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
