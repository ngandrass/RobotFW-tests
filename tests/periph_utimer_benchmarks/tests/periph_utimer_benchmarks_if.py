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

from riot_pal import DutShell


class PeriphUTimerBenchmarksIf(DutShell):
    """Interface to the a node with periph_utimer_benchmarks firmware."""

    FW_ID = 'periph_utimer_benchmarks'

    # Benchmark calls
    def bench_gpio_latency(self):
        """Execute GPIO latency benchmark."""
        return self.send_cmd('bench_gpio_latency')

    def process_bench_gpio_latency(self, trace):
        """Postprocess trace data from GPIO latency benchmark."""
        consecutive_edges = [x for x in trace if
            x['source'] == "DUT_IC" and
            x['event'] == "RISING" and
            1e-12 < x['diff'] < 1e-6
        ]

        edge_diffs = [x['diff'] for x in consecutive_edges][1:]  # First edge doesn't count since it has no valid predecessor

        return {
            'gpio_latency': self._calc_statistical_properties([x/2 for x in edge_diffs]),
                # GPIO latency is half the diff between two rising edges since
                # it requires two GPIO operations (clear + set) to produce one
                # rising edge.
                #'min': np.min(edge_diffs)/2,
                #'max': np.max(edge_diffs)/2,
                #'avg': np.average(edge_diffs)/2,
                #'mean': np.mean(edge_diffs)/2
            'edge_diffs': self._calc_statistical_properties(edge_diffs)
        }

    def bench_timer_read(self, api):
        """Execute timer read benchmark.

        :param api: API to use ('uAPI' or 'hAPI')
        """
        api = str.lower(api)

        if api == 'uapi':
            return self.send_cmd('bench_timer_read_uapi')
        elif api == 'hapi':
            return self.send_cmd('bench_timer_read_hapi')
        else:
            raise ValueError("api must be either 'uAPI' or 'hAPI'")

    def process_bench_timer_read(self, trace):
        """Postprocess trace data from uAPI/hAPI timer read benchmark."""

        # Select benchmark samples from trace
        edges = trace[4:]

        # Extract timer read durations (time between rising and falling edge)
        read_durations = [x['diff'] for x in edges if
            x['source'] == "DUT_IC" and
            x['event'] == "FALLING" and
            x['diff'] < 1e-3
        ]

        return {
            'min': np.min(read_durations),
            'max': np.max(read_durations),
            'avg': np.average(read_durations),
            'mean': np.mean(read_durations),
            'values': read_durations,
            'samples': len(read_durations)
        }

    # Util calls
    def get_metadata(self):
        """Get the metadata of the firmware."""
        return self.send_cmd('get_metadata')

    def get_command_list(self):
        """List of all commands."""
        return [
            self.bench_gpio_latency,
            self.get_metadata,
        ]

    # Helper functions
    @staticmethod
    def _calc_statistical_properties(data):
        return {
            'min': np.min(data),
            'max': np.max(data),
            'avg': np.average(data),
            'mean': np.mean(data),
            'values': data,
            'samples': len(data)
        }


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
