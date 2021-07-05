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
        # Extract diffs between edges and remove intermediate wait period from results
        edge_diffs_with_delay = [x['diff'] for x in trace if
            x['source'] == "DUT_IC" and
            x['diff'] < 1e-2
        ][2:]  # First value has to diff, cut first two to be symmetrical between gpio_set() and gpio_clear()

        edge_delay = 1e-3  # 1 ms
        edge_diffs = [x - edge_delay for x in edge_diffs_with_delay if (x-edge_delay > 0)]

        return self._calc_statistical_properties(edge_diffs)

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
        edges = trace[2:]

        # Extract timer read durations (time between rising and falling edge)
        read_durations = [x['diff'] for x in edges if
            x['source'] == "DUT_IC" and
            x['event'] == "FALLING" and
            x['diff'] < 1e-3
        ]

        # Scale down from 10-times repeated instruction
        read_durations = [x/10 for x in read_durations]

        return self._calc_statistical_properties(read_durations)

    def bench_timer_write(self, api):
        """Execute timer write benchmark.

        :param api: API to use ('uAPI' or 'hAPI')
        """
        api = str.lower(api)

        if api == 'uapi':
            return self.send_cmd('bench_timer_write_uapi')
        elif api == 'hapi':
            return self.send_cmd('bench_timer_write_hapi')
        else:
            raise ValueError("api must be either 'uAPI' or 'hAPI'")

    def process_bench_timer_write(self, trace):
        """Postprocess trace data from uAPI/hAPI timer write benchmark."""

        # Select benchmark samples from trace
        edges = trace[2:]

        # Extract timer write durations (time between rising and falling edge)
        write_durations = [x['diff'] for x in edges if
            x['source'] == "DUT_IC" and
            x['event'] == "FALLING" and
            x['diff'] < 1e-3
        ]

        # Scale down from 10-times repeated instruction
        write_durations = [x/10 for x in write_durations]

        return self._calc_statistical_properties(write_durations)

    def bench_absolute_timeout(self, freq, ticks):
        """Executes the absolute timeout benchmark.

        :param freq:    Frequency to initialize the timer to
        :param ticks:   Number of absolute timer ticks to timeout
        """
        return self.send_cmd("bench_absolute_timeout {} {}".format(freq, ticks))

    def process_bench_absolute_timeout(self, trace):
        """Postprocess trace data from absolute timeout benchmark."""

        # Extract recorded timeout durations (time between rising and falling edge)
        timeout_durations = [x['diff'] for x in trace if
            x['source'] == "DUT_IC" and
            x['event'] == "FALLING"
        ]

        return self._calc_statistical_properties(timeout_durations)

    # Util calls
    def get_metadata(self):
        """Get the metadata of the firmware."""
        return self.send_cmd('get_metadata')

    def spin_timeout_ms(self, timeout_ms):
        """Let the DUT spin for the given timeout period.

        :param timeout_ms:  Number of milliseconds to spin
        """
        return self.send_cmd('spin_timeout_ms {}'.format(timeout_ms))

    def verify_spin_timeout_ms(self, trace, timeout_ms, max_diff_ms=1e-3):
        """Verify that a spin timeout is within accepted time range.

        :param trace:       PHiLIP trace data from spin_timeout_ms()
        :param timeout_ms:  Number of milliseconds the DUT spun for
        :param max_diff_ms: Maximum allowed deviation in milliseconds
        """
        durations_ms = [x['diff']*1e3 for x in trace if
            x['source'] == "DUT_IC" and
            x['event'] == "FALLING" and
            x['diff'] < 1
        ]

        if len(durations_ms) == 0:
            raise IndexError("No matching timeout edge found in trace")

        if len(durations_ms) > 1:
            raise IndexError("Too many timeout edges found in trace")

        if not (timeout_ms - max_diff_ms) < durations_ms[0] < (timeout_ms + max_diff_ms):
            raise ValueError("Recorded spin timeout period out of bounds. Expected: {} ms, Actual: {} ms".format(
                timeout_ms,
                durations_ms[0]
            ))


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

    @staticmethod
    def concat_traces(head, tail):
        """Concatenates two lists of traces."""
        return head + tail


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
