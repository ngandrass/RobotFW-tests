include ../Makefile.tests_common
include ../common/periph_timer_benchmarks/Makefile

HIL_CMD_TIMEOUT   = 3   # seconds
HIL_RESET_WAIT    = 0.1 # seconds
HIL_CONNECT_WAIT ?= 0.5 # seconds
BENCH_ADDITIONAL_TIMER_FREQUENCIES ?= 0  # If set to 1, additional timer frequencies besides TIMER_SPEED will be benchmarked

USEMODULE += shell
USEMODULE += periph_utimer
FEATURES_REQUIRED += periph_gpio
FEATURES_REQUIRED += HIL_DUT_IC_PORT
FEATURES_REQUIRED += HIL_DUT_IC_PIN

export HIL_DUT_IC_PORT
export HIL_DUT_IC_PIN

#CFLAGS_OPT = -O3  # -flto
CFLAGS += -DHIL_DUT_IC_PORT=$(HIL_DUT_IC_PORT) -DHIL_DUT_IC_PIN=$(HIL_DUT_IC_PIN)
#CFLAGS += -DUTIM_BENCH_MAKE_READ_NOP -DUTIM_BENCH_MAKE_WRITE_NOP

BOARDS_TIMER_250kHz := \
    arduino-mega2560 \
    #

ifneq (,$(filter $(BOARDS_TIMER_250kHz),$(BOARD)))
	TIMER_SPEED ?= 250000
else
	TIMER_SPEED ?= 1000000
endif

export TIMER_SPEED
export BENCH_ADDITIONAL_TIMER_FREQUENCIES

SPIN_TIMEOUT_ACCEPTANCE_FACTOR = 1.0
export SPIN_TIMEOUT_ACCEPTANCE_FACTOR

USE_JSON_SHELL_PARSER ?= 1

include $(RIOTBASE)/Makefile.include
