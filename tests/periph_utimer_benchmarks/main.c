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

#include "shell.h"
#include "periph/timer.h"
#include "periph/gpio.h"

#include "sc_args.h"

#define ARG_ERROR       (-1)
#define CONVERT_ERROR   (-32768)
#define RESULT_OK       (0)
#define RESULT_ERROR    (-1)
#define INVALID_ARGS    puts("Error: Invalid number of arguments")
#define PARSE_ERROR     puts("Error: unable to parse arguments")

/* helper calls (non-API) */

int cmd_get_metadata(int argc, char **argv) {
    (void) argv;
    (void) argc;

    printf("Success: [%s, %s]\n", RIOT_BOARD, RIOT_APPLICATION);

    return 0;
}

/* Initialization and shell setup */

static const shell_command_t shell_commands[] = {
    {"get_metadata", "Get the metadata of the test firmware", cmd_get_metadata},
    { NULL, NULL, NULL }
};

int main(void) {
    puts("periph_utimer_benchmarks: Benchmarks for the utimer API");

    char line_buf[SHELL_DEFAULT_BUFSIZE];
    shell_run(shell_commands, line_buf, SHELL_DEFAULT_BUFSIZE);

    return 0;
}
