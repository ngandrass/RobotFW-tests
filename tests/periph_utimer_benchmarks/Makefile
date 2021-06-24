include ../Makefile.tests_common

USEMODULE += shell
FEATURES_REQUIRED += periph_timer
FEATURES_REQUIRED += periph_gpio
FEATURES_REQUIRED += HIL_DUT_IC_PORT
FEATURES_REQUIRED += HIL_DUT_IC_PIN

export HIL_DUT_IC_PORT
export HIL_DUT_IC_PIN

USE_JSON_SHELL_PARSER ?= 1

include $(RIOTBASE)/Makefile.include
