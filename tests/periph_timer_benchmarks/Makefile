include ../Makefile.tests_common
include ../common/periph_timer_benchmarks/Makefile

USEMODULE += periph_timer
ifneq (,$(filter $(FEATURES_PROVIDED),"periph_timer_periodic"))
    USEMODULE += periph_timer_periodic
endif

include $(RIOTBASE)/Makefile.include
