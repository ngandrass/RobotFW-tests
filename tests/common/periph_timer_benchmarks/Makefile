INCLUDES += -I$(TESTBASE)/tests/common/periph_timer_benchmarks/include

# Benchmark / RobotFramework configuration
HIL_CMD_TIMEOUT   = 3   # seconds
HIL_RESET_WAIT    = 0.1 # seconds
HIL_CONNECT_WAIT ?= 0.5 # seconds

BENCH_ADDITIONAL_TIMER_FREQUENCIES ?= 0  	# If set to 1, additional timer frequencies besides TIMER_SPEED will be benchmarked
TESTCASE_REPEATS ?= 2     					# Number of times every test case is repeated
SPIN_TIMEOUT_ACCEPTANCE_FACTOR = 1.0  		# Scales the acceptance window for board timing parameter verification

# Generic modules and features
USEMODULE += shell
FEATURES_REQUIRED += periph_gpio
FEATURES_REQUIRED += HIL_DUT_IC_PORT
FEATURES_REQUIRED += HIL_DUT_IC_PIN

# Board based selection of timer base frequency
BOARDS_TIMER_250kHz := \
    arduino-mega2560 \
    #

BOARDS_TIMER_32kHz := \
    #

ifneq (,$(filter $(BOARDS_TIMER_250kHz),$(BOARD)))
    TIMER_SPEED             ?= 250000
    TICKS_TIMER_SPEED_1ms   ?= 250
else ifneq (,$(filter $(BOARDS_TIMER_32kHz),$(BOARD)))
    TIMER_SPEED             ?= 32768
    TICKS_TIMER_SPEED_1ms   ?= 33    # Rounded value. Actual: 32,768
else
    TIMER_SPEED             ?= 1000000
    TICKS_TIMER_SPEED_1ms   ?= 1000
endif

# Compiler flags
CFLAGS += -DTIMER_SPEED=$(TIMER_SPEED)
CFLAGS += -DHIL_DUT_IC_PORT=$(HIL_DUT_IC_PORT) -DHIL_DUT_IC_PIN=$(HIL_DUT_IC_PIN)
#CFLAGS_OPT = -O3  # -flto
#CFLAGS += -DUTIM_BENCH_MAKE_READ_NOP -DUTIM_BENCH_MAKE_WRITE_NOP

# Misc
USE_JSON_SHELL_PARSER ?= 1

# Exports (keep at the bottom!)
export BENCH_ADDITIONAL_TIMER_FREQUENCIES
export HIL_DUT_IC_PIN
export HIL_DUT_IC_PORT
export SPIN_TIMEOUT_ACCEPTANCE_FACTOR
export TESTCASE_REPEATS
export TICKS_TIMER_SPEED_1ms
export TIMER_SPEED
