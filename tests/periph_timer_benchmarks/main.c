/*
 * Copyright (C) 2021 HAW Hamburg
 *
 * This file is subject to the terms and conditions of the GNU Lesser
 * General Public License v2.1. See the file LICENSE in the top level
 * directory for more details.
 */

/**
 * @ingroup tests
 * @{
 *
 * @file
 * @brief       Benchmarking application for periph timer API
 *
 * @author      Niels Gandraß <niels@gandrass.de>
 *
 * @}
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <stdbool.h>

#include "irq.h"
#include "shell.h"
#include "test_helpers.h"
#include "macros/units.h"
#include "periph/gpio.h"
#include "periph/timer.h"

#include "sc_args.h"

#define ENABLE_DEBUG (0)

#ifndef PARSER_DEV_NUM
#define PARSER_DEV_NUM (0)
#endif

#ifndef BENCH_TIMER_DEV
#define BENCH_TIMER_DEV (0)
#endif

/**
 * @brief   Default amount of times a single benchmark is repeated
 *
 * The PHiLIP buffer only supports capturing 128 events. Therefore 50 duration
 * measurements, requiring two edges each, are the default. This leaves room
 * for 28 additional samples.
 */
#define DEFAULT_BENCH_REPEAT_COUNT  (50)

/**
 * @brief   Repeats a single operation 10 times
 *
 * PHiLIP requires some backoff-time between recorded events. Single operation
 * micro-benchmarks therefore need to be repeated in order to safely capture
 * the elapsed time period. Very short durations can't be measured reliably!
 */
#define REPEAT_10(X) X; X; X; X; X; X; X; X; X; X;

#ifdef CONFIG_BOARD_NUCLEO_L476RG
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   4
#endif

#ifdef CONFIG_BOARD_NUCLEO_F070RB
#define F_CPU                   MHZ(48)
#define INSTRUCTIONS_PER_SPIN   7
#endif

#ifdef CONFIG_BOARD_ESP32_WROOM_32
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   5
#endif

#if (!defined(F_CPU) || !defined(INSTRUCTIONS_PER_SPIN))
#error Board clock parameters not specified!
#endif

#define CYCLES_PER_SEC          (F_CPU / INSTRUCTIONS_PER_SPIN)
#define CYCLES_PER_MSEC         (CYCLES_PER_SEC / 1000)
#define CYCLES_PER_USEC         (CYCLES_PER_MSEC / 1000)

#define GPIO_IC GPIO_PIN(HIL_DUT_IC_PORT, HIL_DUT_IC_PIN)

#define DISABLE_IRQs    false
#define ENABLE_IRQs     true

/* Helper functions */

/**
 * @brief   Busy wait (spin) for the given number of loop iterations
 */
static inline void spin(uint32_t n) {
    while (n--) {
        __asm__ volatile ("");
    }
}

/**
 * @brief   Common setup procedure for all benchmarks
 *
 * @param   irqs Whether IRQs get disabled for the following benchmark
 */
static inline void _bench_setup(bool irqs) {
    // Disable IRQs during test
    if (irqs == DISABLE_IRQs) {
        irq_disable();
    }

    // Start with GPIO_IC set to low
    gpio_clear(GPIO_IC);
    spin(10 * CYCLES_PER_MSEC);
}

/**
 * @brief   Common teardown procedure for all benchmarks
 */
static inline void _bench_teardown(void) {
    // End with GPIO_IC set to low
    gpio_clear(GPIO_IC);
    irq_enable();
}

/* Benchmarks */

/**
 * @brief   Benchmarks latency of the GPIO_IC pin
 *
 * The GPIO_IC pin is toggled repeatedly to measure the amount of time consumed
 * by the gpio_set() and gpio_clear() calls. An extra microsecond is added due
 * to PHiLIP backoff-time requirements.
 */
int cmd_bench_gpio_latency(int argc, char **argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Generate consecutive rising edges
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        spin(1 * CYCLES_PER_MSEC);
        gpio_clear(GPIO_IC);
        spin(1 * CYCLES_PER_MSEC);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 timer read operations
 *
 * During timer read the GPIO_IC pin is pulled high and gets released
 * immediately after the last utimer_read() returns.
 */
int cmd_bench_timer_read(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Perform benchmark (timer read)
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(timer_read(BENCH_TIMER_DEV));
        gpio_clear(GPIO_IC);

        spin(1 * CYCLES_PER_MSEC);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

void _bench_absolute_timeouts_cb(void *arg, int channel) {
    gpio_clear(GPIO_IC);

    (void) arg;
    (void) channel;

    return;
}

/**
 * @brief   Benchmarks a single absolute timeout
 *
 * The timer is initialized and set to zero before arming it to the desired
 * timout. Once prepared the timer is started. GPIO_IC is held high until the
 * time elapsed and the associated user callback is executed.
 *
 * @param argv[1]   Frequency used for the timer
 * @param argv[2]   Timeout in ticks (absolute counter value)
 */
int cmd_bench_absolute_timeouts(int argc, char** argv) {
    // Parse arguments
    if (sc_args_check(argc, argv, 2, 2, "FREQ TIMEOUT") != ARGS_OK) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return ARGS_ERROR;
    }

    unsigned long freq = 0;
    if (sc_arg2ulong(argv[1], &freq) != ARGS_OK) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return ARGS_ERROR;
    }

    unsigned long timeout = 0;
    if (sc_arg2ulong(argv[2], &timeout) != ARGS_OK) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return ARGS_ERROR;
    }

    _bench_setup(ENABLE_IRQs);

    // Initialize timer and callback
    timer_init(BENCH_TIMER_DEV, freq, &_bench_absolute_timeouts_cb, NULL);
    timer_stop(BENCH_TIMER_DEV);
    timer_set(BENCH_TIMER_DEV, 0, timeout);

    // Execute timeout by starting timer and setting GPIO_IC
    timer_start(BENCH_TIMER_DEV);
    gpio_set(GPIO_IC);

    // Wait for GPIO_IC to be cleard by attached callback function
    while(gpio_read(GPIO_IC));
    timer_stop(BENCH_TIMER_DEV);

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/* Helper calls */

int cmd_get_metadata(int argc, char **argv) {
    (void) argv;
    (void) argc;

    print_data_str(PARSER_DEV_NUM, RIOT_BOARD);
    print_data_str(PARSER_DEV_NUM, RIOT_VERSION);
    print_data_str(PARSER_DEV_NUM, RIOT_APPLICATION);
    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    return 0;
}

/* Initialization and shell setup */

static const shell_command_t shell_commands[] = {
    {"bench_gpio_latency", "Benchmarks latency of GPIO_DUT_IC", cmd_bench_gpio_latency},
    {"bench_timer_read", "Benchmarks time consumed by a timer read", cmd_bench_timer_read},
    {"bench_absolute_timeout", "Benchmarks absolute timeouts", cmd_bench_absolute_timeouts},
    {"get_metadata", "Get the metadata of the test firmware", cmd_get_metadata},
    { NULL, NULL, NULL }
};

int main(void) {
    puts("periph_timer_benchmarks: Benchmarks for the periph_timer API");

    // Init GPIOs
    gpio_init(GPIO_IC, GPIO_OUT);
    gpio_clear(GPIO_IC);

    // Start interactive shell
    char line_buf[SHELL_DEFAULT_BUFSIZE];
    shell_run(shell_commands, line_buf, SHELL_DEFAULT_BUFSIZE);

    return 0;
}
