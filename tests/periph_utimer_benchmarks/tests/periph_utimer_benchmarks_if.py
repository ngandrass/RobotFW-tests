# Copyright (C) 2021 Niels Gandraß <niels@gandrass.de>
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.
"""@package PyToAPI
This module handles parsing of information from periph_utimer_benchmarks suite.
"""
import logging
import numpy as np

from periph_timer_benchmarks_if_base import PeriphUTimerBenchmarksIfBase


class PeriphUTimerBenchmarksIf(PeriphUTimerBenchmarksIfBase):
    """Interface to the a node with periph_utimer_benchmarks firmware."""

    FW_ID = 'periph_utimer_benchmarks'


def main():
    """Execution routine for periph_utimer_benchmarks suite."""

    logging.getLogger().setLevel(logging.DEBUG)
    try:
        utimer = PeriphUTimerBenchmarksIf()
        cmds = utimer.get_command_list()
        logging.debug("======================================================")
        for cmd in cmds:
            cmd()
            logging.debug("--------------------------------------------------")
        logging.debug("======================================================")
    except Exception as exc:
        logging.debug(exc)


if __name__ == "__main__":
    main()
