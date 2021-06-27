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
#include "periph/gpio.h"
#include "periph/utimer.h"

#include "sc_args.h"

#ifndef PARSER_DEV_NUM
#define PARSER_DEV_NUM 0
#endif

#ifndef BENCH_TIMER_DEV
#define BENCH_TIMER_DEV 0
#endif

#define DEFAULT_REPEAT_COUNT (50)

#define F_CPU           MHZ(16)
#define CYCLES_PER_SEC  (F_CPU)
#define CYCLES_PER_MSEC (CYCLES_PER_SEC / 1000)
#define CYCLES_PER_USEC (CYCLES_PER_MSEC / 1000)

#define GPIO_IC GPIO_PIN(HIL_DUT_IC_PORT, HIL_DUT_IC_PIN)

#define DISABLE_IRQs    false
#define ENABLE_IRQs     true

/* Helper functions */

/**
 * @brief   Busy wait (spin) for the given number of loop iterations
 */
static void spin(uint32_t n) {
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
 * The GPIO_IC pin is toggled repeatedly to measure the delay between two
 * consecutive rising edges on the GPIO_IC pin.
 */
int cmd_bench_gpio_latency(int argc, char **argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Generate consecutive rising edges
    for (int i = 0; i < DEFAULT_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        gpio_clear(GPIO_IC);
        gpio_set(GPIO_IC);
        gpio_clear(GPIO_IC);

        spin(1 * CYCLES_PER_MSEC);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by a uAPI timer read operation
 *
 * During timer read the GPIO_IC pin is pulled high and gets released
 * immediately after utimer_read() returns.
 */
int cmd_bench_timer_read_uapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }

    // Perform benchmark (uAPI timer read)
    for (int i = 0; i < DEFAULT_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        utimer_read(&tim);
        gpio_clear(GPIO_IC);

        spin(1 * CYCLES_PER_MSEC);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by a hAPI timer read operation
 *
 * During timer read the GPIO_IC pin is pulled high and gets released
 * immediately after tim->read() returns.
 */
int cmd_bench_timer_read_hapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }
    utim_driver_t *driver = tim.driver;

    // Perform benchmark (hAPI timer read)
    for (int i = 0; i < DEFAULT_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        driver->read(&tim);
        gpio_clear(GPIO_IC);

        spin(1 * CYCLES_PER_MSEC);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by a uAPI timer write operation
 *
 * During timer write the GPIO_IC pin is pulled high and gets released
 * immediately after utimer_write() returns.
 */
int cmd_bench_timer_write_uapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }

    // Perform benchmark (uAPI timer write)
    for (int i = 0; i < DEFAULT_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        utimer_write(&tim, 0x42);
        gpio_clear(GPIO_IC);

        spin(1 * CYCLES_PER_MSEC);
    }

    print_result(PARSER_DEV_NUM, TEST_RESULT_SUCCESS);

    _bench_teardown();
    return 0;
}

/**
 * @brief   Benchmarks time consumed by a hAPI timer write operation
 *
 * During timer write the GPIO_IC pin is pulled high and gets released
 * immediately after tim->write() returns.
 */
int cmd_bench_timer_write_hapi(int argc, char** argv) {
    (void) argc;
    (void) argv;

    _bench_setup(DISABLE_IRQs);

    // Get timer peripheral
    utim_periph_t tim = utimer_get_periph(BENCH_TIMER_DEV);
    if (tim.dev == UTIMER_DEV_INVALID) {
        print_result(PARSER_DEV_NUM, TEST_RESULT_ERROR);
        return -1;
    }
    utim_driver_t *driver = tim.driver;

    // Perform benchmark (hAPI timer read)
    for (int i = 0; i < DEFAULT_REPEAT_COUNT; i++) {
        gpio_set(GPIO_IC);
        driver->write(&tim, 0x42);
        gpio_clear(GPIO_IC);

        spin(1 * CYCLES_PER_MSEC);
    }

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
    {"bench_timer_read_uapi", "Benchmarks time consumed by a uAPI timer read", cmd_bench_timer_read_uapi},
    {"bench_timer_read_hapi", "Benchmarks time consumed by a hAPI timer read", cmd_bench_timer_read_hapi},
    {"bench_timer_write_uapi", "Benchmarks time consumed by a uAPI timer write", cmd_bench_timer_write_uapi},
    {"bench_timer_write_hapi", "Benchmarks time consumed by a hAPI timer write", cmd_bench_timer_write_hapi},
    {"get_metadata", "Get the metadata of the test firmware", cmd_get_metadata},
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
