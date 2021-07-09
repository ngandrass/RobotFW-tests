include ../Makefile.tests_common

HIL_CMD_TIMEOUT = 5	# seconds
HIL_RESET_WAIT = 0.5  	# seconds

USEMODULE += shell
USEMODULE += periph_utimer
FEATURES_REQUIRED += periph_gpio
FEATURES_REQUIRED += HIL_DUT_IC_PORT
FEATURES_REQUIRED += HIL_DUT_IC_PIN

export HIL_DUT_IC_PORT
export HIL_DUT_IC_PIN

#CFLAGS_OPT = -O3  # -flto
CFLAGS += -DHIL_DUT_IC_PORT=$(HIL_DUT_IC_PORT) -DHIL_DUT_IC_PIN=$(HIL_DUT_IC_PIN)

USE_JSON_SHELL_PARSER ?= 1

include $(RIOTBASE)/Makefile.include
