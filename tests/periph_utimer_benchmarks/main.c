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
 * @brief       Benchmarking application for periph utimer API
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
#include "periph/utimer.h"

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
#define REPEAT_10(X)    X; X; X; X; X; X; X; X; X; X;

/**
 * @brief   Repeats a single operation 20 times
 */
#define REPEAT_20(X)    REPEAT_10(X); REPEAT_10(X);

/**
 * @brief   Repeats a single operation 100 times
 */
#define REPEAT_100(X)   REPEAT_20(X); REPEAT_20(X); REPEAT_20(X); REPEAT_20(X); REPEAT_20(X);

#include "board_params.h"

#if (!defined(F_CPU) || !defined(INSTRUCTIONS_PER_SPIN))
#error Board clock parameters not specified!
#endif

#define CYCLES_PER_SEC          (F_CPU / INSTRUCTIONS_PER_SPIN)
#define CYCLES_PER_MSEC         (CYCLES_PER_SEC / 1000)
#define CYCLES_PER_USEC         (CYCLES_PER_MSEC / 1000)

#define PHILIP_BACKOFF_SPINS    (1 * CYCLES_PER_USEC)  /**< Worst case number of spins PHiLIP needs between two consecutive trace edges */

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
    spin(10 * PHILIP_BACKOFF_SPINS);
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
 * by the gpio_set() and gpio_clear() calls. A 1ms spin between the two GPIO
 * calls represents a time-measured operation.
 */
int cmd_bench_gpio_latency(int argc, char **argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        spin(1 * CYCLES_PER_MSEC);
        gpio_clear(GPIO_IC);
        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 uAPI timer read operations
 *
 * During timer read the GPIO_IC pin is pulled high and gets released
 * immediately after the last utimer_read() returns.
 */
int cmd_bench_timer_read_uapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }

    // Perform benchmark (uAPI timer read)
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(utimer_read(tim_ptr));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 hAPI timer read operations
 *
 * During timer read the GPIO_IC pin is pulled high and gets released
 * immediately after the last tim->read() returns.
 */
int cmd_bench_timer_read_hapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }
    const utim_driver_t *const driver = tim.driver;
    utim_cnt_t (*const f_read)(utim_periph_t *const tim) = driver->read;

    // Perform benchmark (hAPI timer read)
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(f_read(tim_ptr));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 uAPI timer write operations
 *
 * During timer write the GPIO_IC pin is pulled high and gets released
 * immediately after the last utimer_write() returns.
 */
int cmd_bench_timer_write_uapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }

    // Perform benchmark (uAPI timer write)
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(utimer_write(tim_ptr, 0x42));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 hAPI timer write operations
 *
 * During timer write the GPIO_IC pin is pulled high and gets released
 * immediately after the last tim->write() returns.
 */
int cmd_bench_timer_write_hapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }
    const utim_driver_t *driver = tim.driver;
    void (*const f_write)(utim_periph_t *const tim, utim_cnt_t cnt) = driver->write;

    // Perform benchmark (hAPI timer read)
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(f_write(tim_ptr, 0x42));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 uAPI timer set operations
 *
 * During timer set the GPIO_IC pin is pulled high and gets released
 * immediately after the last call returns.
 */
int cmd_bench_timer_set_uapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }

    // Perform benchmark
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(utimer_set_absolute(tim_ptr, 0, 0x42));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 hAPI timer set operations
 *
 * During timer set the GPIO_IC pin is pulled high and gets released
 * immediately after the last call returns.
 */
int cmd_bench_timer_set_hapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }
    const utim_driver_t *driver = tim.driver;
    int (*const f_set_channel)(utim_periph_t *const tim, unsigned int channel, utim_chan_mode_t mode, utim_cnt_t cnt) = driver->set_channel;

    // Perform benchmark
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(f_set_channel(tim_ptr, 0, UTIM_CHAN_ONESHOT, 0x42));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 uAPI timer clear operations
 *
 * During timer clear the GPIO_IC pin is pulled high and gets released
 * immediately after the last call returns.
 */
int cmd_bench_timer_clear_uapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }

    // Perform benchmark
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(utimer_clear(tim_ptr, 0));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by 10 hAPI timer clear operations
 *
 * During timer clear the GPIO_IC pin is pulled high and gets released
 * immediately after the last call returns.
 */
int cmd_bench_timer_clear_hapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    utim_periph_t *const tim_ptr = &tim;
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }
    const utim_driver_t *driver = tim.driver;
    int (*const f_set_channel)(utim_periph_t *const tim, unsigned int channel, utim_chan_mode_t mode, utim_cnt_t cnt) = driver->set_channel;

    // Perform benchmark
    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        REPEAT_10(f_set_channel(tim_ptr, 0, UTIM_CHAN_DISABLED, 0));
        gpio_clear(GPIO_IC);

        spin(PHILIP_BACKOFF_SPINS);
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

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    if (tim.dev == UTIMER_DEV_INVALID || tim.channels < 1) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return ARGS_ERROR;
    }

    // Initialize timer and callback
    if (utimer_init(&tim, freq, UTIM_CLK_DEFAULT, &_bench_absolute_timeouts_cb, NULL, NULL, NULL) != 0) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }
    utimer_stop(&tim);
    utimer_write(&tim, 0);

    if (((uint64_t) timeout) >> tim.width) {  // Skip on too large counter values
        print_result(PARSER_DEV_NUM, TEST_RESULT_SKIPPED);
        return -1;
    }

    if (utimer_set(&tim, 0, timeout) != 0) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }

    // Execute timeout by starting timer and setting GPIO_IC
    utimer_start(&tim);
    gpio_set(GPIO_IC);

    // Wait for GPIO_IC to be cleard by attached callback function
    while(gpio_read(GPIO_IC));
    utimer_stop(&tim);

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
    print_data_int(PARSER_DEV_NUM, F_CPU);
    print_data_int(PARSER_DEV_NUM, INSTRUCTIONS_PER_SPIN);
    print_data_int(PARSER_DEV_NUM, PHILIP_BACKOFF_SPINS);
    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    return 0;
}

/**
 * @brief   Routine to calibrate time consumed by spin() function.
 *
 * Generate rising and falling edges every 1000 spin iterations. The elapsed
 * time can be used to determine INSTRUCTIONS_PER_SPIN parameter.
 *
 * Execution time (w/o DEFAULT_BENCH_REPEAT_COUNT):
 *   - 1000 spins @ 1 MHz = 1 ms
 *   - 1000 spins @ 1 GHz = 1 us
 */
int cmd_calibrate_spin(int argc, char **argv) {
    (void) argv;
    (void) argc;

    _bench_setup(DISABLE_IRQs);

    for (int i = 0; i < DEFAULT_BENCH_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        spin(1000);
        gpio_clear(GPIO_IC);
        spin(1000);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Spins for argv[1] amount of milliseconds.
 *
 * This function is used to verify that F_CPU and INSTRUCTIONS_PER_SPIN are set
 * correctly for the current board.
 *
 * @param argv[1]   Number of milliseconds to spin
 */
int cmd_spin_timeout_ms(int argc, char **argv) {
    // Parse arguments
    if (sc_args_check(argc, argv, 1, 1, "TIMEOUT_MS") != ARGS_OK) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return ARGS_ERROR;
    }

    unsigned int timeout_ms = 0;
    if (sc_arg2uint(argv[1], &timeout_ms) != ARGS_OK) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return ARGS_ERROR;
    }

    _bench_setup(ENABLE_IRQs);

    // Do the spin!
    gpio_set(GPIO_IC);
    spin(timeout_ms * CYCLES_PER_MSEC);
    gpio_clear(GPIO_IC);

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/* Initialization and shell setup */

static const shell_command_t shell_commands[] = {
    {"bench_gpio_latency", "Benchmarks latency of GPIO_DUT_IC", cmd_bench_gpio_latency},
    {"bench_timer_read_uapi", "Benchmarks time consumed by a uAPI timer read", cmd_bench_timer_read_uapi},
    {"bench_timer_read_hapi", "Benchmarks time consumed by a hAPI timer read", cmd_bench_timer_read_hapi},
    {"bench_timer_write_uapi", "Benchmarks time consumed by a uAPI timer write", cmd_bench_timer_write_uapi},
    {"bench_timer_write_hapi", "Benchmarks time consumed by a hAPI timer write", cmd_bench_timer_write_hapi},
    {"bench_timer_set_uapi", "Benchmarks time consumed by a uAPI timer set", cmd_bench_timer_set_uapi},
    {"bench_timer_set_hapi", "Benchmarks time consumed by a hAPI timer set", cmd_bench_timer_set_hapi},
    {"bench_timer_clear_uapi", "Benchmarks time consumed by a uAPI timer clear", cmd_bench_timer_clear_uapi},
    {"bench_timer_clear_hapi", "Benchmarks time consumed by a hAPI timer clear", cmd_bench_timer_clear_hapi},
    {"bench_absolute_timeout", "Benchmarks absolute timeouts", cmd_bench_absolute_timeouts},
    {"get_metadata", "Get the metadata of the test firmware", cmd_get_metadata},
    {"calibrate_spin", "Calibrate clk specific board parameters", cmd_calibrate_spin},
    {"spin_timeout_ms", "Spin for the given amount of milliseconds", cmd_spin_timeout_ms},
    { NULL, NULL, NULL }
};

int main(void) {
    puts("periph_utimer_benchmarks: Benchmarks for the utimer API");

    // Init GPIOs
    gpio_init(GPIO_IC, GPIO_OUT);
    gpio_clear(GPIO_IC);

    // Start interactive shell
    char line_buf[SHELL_DEFAULT_BUFSIZE];
    shell_run(shell_commands, line_buf, SHELL_DEFAULT_BUFSIZE);

    return 0;
}
