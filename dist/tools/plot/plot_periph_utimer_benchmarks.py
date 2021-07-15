#!/usr/bin/env python3

import argparse
import json
import logging
import os
import re

import numpy as np
from pathlib import Path
from si_prefix import si_format
import xmltodict

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

LOG = logging.getLogger(__name__)


class FigurePlotter:

    BOARD_F_CPU = {
        'nucleo-f070rb': 48e6,
        'nucleo-l476rg': 80e6,
        'esp32-wroom-32': 80e6,
        'slstk3402a': 40e6
    }

    XUNIT_FILE_PATTERN = '*xunit.xml'
    XUNIT_TESTSUITE_NAME_PATTERN = r"^tests_periph_(u)?timer_benchmarks$"

    SUITE_TIMER = 'tests_periph_timer_benchmarks'
    SUITE_UTIMER = 'tests_periph_utimer_benchmarks'

    PLOTLY_COMMON_LAYOUT_PROPS = dict(
        autosize=False,
        width=600,
        height=500,
        margin=dict(l=10, r=10, b=10, t=10, pad=1)
    )

    def __init__(self, indir, outdir):
        self.indir = indir
        self.outdir = outdir
        self.benchmarks = {}
        self.gpio_latencies = {}

        self._parse_all_benchmarks_from_dir(self.indir)
        self._calc_gpio_latencies()

    def _parse_all_benchmarks_from_dir(self, directory):
        for path in Path(directory).rglob(self.XUNIT_FILE_PATTERN):
            xunit_data = self._parse_xunit_file(path)
            board = xunit_data['Record Metadata']['board'][0]
            suite = xunit_data['Record Metadata']['testsuite'][0]

            api = 'UNKNOWN'
            if suite == self.SUITE_UTIMER:
                api = 'periph_utimer'
            elif suite == self.SUITE_TIMER:
                api = 'periph_timer'

            self.benchmarks.setdefault(board, {})[suite] = {
                'api': api,
                'riot_version': xunit_data['Record Metadata']['riot_version'][0],
                'freq_cpu': xunit_data['Record Metadata']['freq_cpu'][0],
                'instructions_per_spin': xunit_data['Record Metadata']['instructions_per_spin'][0],
                'philip_backoff_spins': xunit_data['Record Metadata']['philip_backoff_spins'][0],
                'benchmarks': xunit_data
            }

            LOG.info("Parsed {} benchmarks from {} - {} testsuite".format(
                len(xunit_data),
                board,
                suite
            ))

    def _parse_xunit_file(self, xunit_file, testsuite_name_pattern=XUNIT_TESTSUITE_NAME_PATTERN):
        # Parse xUnit file
        with open(xunit_file) as fd:
            self.xunit = xmltodict.parse(fd.read())

        # Verify testsuite
        testsuite = self.xunit['testsuite']
        if not re.match(testsuite_name_pattern, testsuite['@name']):
            raise ImportError("Testsuite names doesn't match! Expected: '{}', Actual: '{}'".format(
                testsuite_name_pattern,
                testsuite['@name']
            ))

        # Extract benchmarks (testcase properties) from testsuite
        benchmarks = {}
        for benchmark in testsuite['testcase']:
            props = {}
            for property in benchmark['properties']['property']:
                try:
                    if property['@name'] not in props:
                        props[property['@name']] = []
                    props[property['@name']].append(property['@value'])
                except TypeError:
                    pass  # Failed tests have empty props

            benchmarks[benchmark['@name']] = props

        return benchmarks

    def _extract_bench_values_from_json(self, bench_props, values_key="values"):
        values = []
        for traceset_json in bench_props:
            traceset = json.loads(traceset_json.replace("'", "\""))
            values = values + traceset[values_key]

        return values

    def _calc_statistical_properties(self, dataset):
        return {
            'avg': np.average(dataset),
            'mean': np.mean(dataset),
            'stdev': np.std(dataset),
            'var': np.var(dataset),
            'min': np.min(dataset),
            'max': np.max(dataset),
            'samples': len(dataset)
        }

    def _calc_gpio_latencies(self):
        for board, suites in self.benchmarks.items():
            durations = []
            for suite in suites.values():
                durations = durations + self._extract_bench_values_from_json(
                    suite['benchmarks']['Measure GPIO Latency']['bench_gpio_latency']
                )

            self.gpio_latencies[board] = np.average(durations)
            LOG.info("GPIO Latency on board {} = {}".format(board, self.gpio_latencies[board]))

    def _save_figure_as_html(self, fig, title):
        outfile = "{}/{}.html".format(self.outdir, title)
        fig.write_html(
            outfile,
            full_html=True,
            include_plotlyjs=True,
        )

        LOG.info("Wrote figure: {}".format(outfile))

    def _get_benchmark_data(self, board, testsuite, testcase, datavar):
        return self._extract_bench_values_from_json(
            self.benchmarks[board][testsuite]['benchmarks'][testcase][datavar]
        )

    def _get_gpio_latency(self, board):
        return self.gpio_latencies[board]

    def get_boards(self):
        return self.benchmarks.keys()

    #############################
    ### Board specific plots ####
    #############################

    def plot_board_gpio_latency(self, board):
        # Process samples
        durations = {
            'periph_utimer': self._get_benchmark_data(board, self.SUITE_UTIMER, 'Measure GPIO Latency', 'bench_gpio_latency'),
            'periph_timer': self._get_benchmark_data(board, self.SUITE_TIMER, 'Measure GPIO Latency', 'bench_gpio_latency'),
        }

        LOG.info("periph_utimer GPIO Latency: {}".format(self._calc_statistical_properties(durations['periph_utimer'])))
        LOG.info("periph_timer GPIO Latency: {}".format(self._calc_statistical_properties(durations['periph_timer'])))

        # Generate box plot
        data = pd.DataFrame.from_dict(durations, orient='index').transpose()
        fig = go.Figure()
        fig.add_trace(go.Box(name='periph_utimer', y=durations['periph_utimer']))
        fig.add_trace(go.Box(name='periph_timer', y=durations['periph_timer']))
        fig.update_layout(
            title="GPIO Latency - Board: {}".format(board),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Timer Driver",
            xaxis_showgrid=True,
            yaxis_showgrid=True,
            showlegend=False
        )

        self._save_figure_as_html(fig, "{}_gpio_latency".format(board))

    def plot_board_read_write_ops(self, board):
        lgpio = self._get_gpio_latency(board)

        # Read, combine and process trace samples. Remove GPIO overhead and scale down by the repeat factor of 10
        durations = []
        durations = durations + [('periph_utimer', 'Read (uAPI)',  (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark uAPI Timer Read', 'bench_timer_read_uapi')]
        durations = durations + [('periph_utimer', 'Read (hAPI)',  (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark hAPI Timer Read', 'bench_timer_read_hapi')]
        durations = durations + [('periph_utimer', 'Write (uAPI)', (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark uAPI Timer Write', 'bench_timer_write_uapi')]
        durations = durations + [('periph_utimer', 'Write (hAPI)', (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark hAPI Timer Write', 'bench_timer_write_hapi')]
        durations = durations + [('periph_timer',  'Read',         (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_TIMER, 'Benchmark Timer Read', 'bench_timer_read')]
        df = pd.DataFrame(durations, columns=['api', 'operation', 'duration'])

        # Calc statistical properties
        for api in df['api'].unique():
            for operation in df[df['api'] == api]['operation'].unique():
                LOG.info("Benchmark {} - {}: {}".format(
                    api,
                    operation,
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['operation'] == operation)]['duration'])
                ))

        # Generate plot
        fig = go.Figure()
        fig.add_box(x=df[df['api'] == 'periph_utimer']['operation'], y=df[df['api'] == 'periph_utimer']['duration'], name="periph_utimer")
        fig.add_box(x=df[df['api'] == 'periph_timer']['operation'], y=df[df['api'] == 'periph_timer']['duration'], name="periph_timer")
        fig.update_layout(
            title="Timer Read and Write Operations - Board: {}".format(board),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Operation (via API)",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )
        self._save_figure_as_html(fig, "{}_bench_timer_read_write".format(board))

    def plot_board_set_clear_ops(self, board):
        lgpio = self._get_gpio_latency(board)

        # Read, combine and process trace samples. Remove GPIO overhead and scale down by the repeat factor of 10
        durations = []
        durations = durations + [('periph_utimer', 'Set (uAPI)',   (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark uAPI Timer Set', 'bench_timer_set_uapi')]
        durations = durations + [('periph_utimer', 'Set (hAPI)',   (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark hAPI Timer Set', 'bench_timer_set_hapi')]
        durations = durations + [('periph_utimer', 'Clear (uAPI)', (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark uAPI Timer Clear', 'bench_timer_clear_uapi')]
        durations = durations + [('periph_utimer', 'Clear (hAPI)', (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_UTIMER, 'Benchmark hAPI Timer Clear', 'bench_timer_clear_hapi')]
        durations = durations + [('periph_timer',  'Set',          (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_TIMER, 'Benchmark Timer Set', 'bench_timer_set')]
        durations = durations + [('periph_timer',  'Clear',        (x-lgpio)/10) for x in self._get_benchmark_data(board, self.SUITE_TIMER, 'Benchmark Timer Clear', 'bench_timer_clear')]
        df = pd.DataFrame(durations, columns=['api', 'operation', 'duration'])

        # Calc statistical properties
        for api in df['api'].unique():
            for operation in df[df['api'] == api]['operation'].unique():
                LOG.info("Benchmark {} - {}: {}".format(
                    api,
                    operation,
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['operation'] == operation)]['duration'])
                ))

        # Generate plot
        fig = go.Figure()
        fig.add_box(x=df[df['api'] == 'periph_utimer']['operation'], y=df[df['api'] == 'periph_utimer']['duration'], name="periph_utimer")
        fig.add_box(x=df[df['api'] == 'periph_timer']['operation'], y=df[df['api'] == 'periph_timer']['duration'], name="periph_timer")
        fig.update_layout(
            title="Timer Set and Clear Operations - Board: {}".format(board),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Operation (via API)",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )
        self._save_figure_as_html(fig, "{}_bench_timer_set_clear".format(board))

    def plot_board_absolute_timeouts_grouped_by_freq(self, board, freq, ignored_timeouts=[]):
        # Read, combine and process trace samples
        timeouts = []
        for testsuite, testsuite_data in self.benchmarks[board].items():
            for case, data in testsuite_data['benchmarks'].items():
                if case.startswith('Benchmark Absolute Timeouts'):
                    if not data:
                        continue

                    if int(data['frequency'][0]) == freq:
                        timeout = int(data['ticks'][0])/int(data['frequency'][0])
                        if timeout not in ignored_timeouts:
                            for duration in self._extract_bench_values_from_json(data['bench_absolute_timeouts']):
                                duration = duration - self._get_gpio_latency(board)
                                timeouts.append({
                                    'api': testsuite_data['api'],
                                    'frequency': int(data['frequency'][0]),
                                    'ticks': int(data['ticks'][0]),
                                    'timeout': timeout,
                                    'duration': duration,
                                    'latency': duration - timeout
                                })

        if not timeouts:
            LOG.error("No data for absolute timeouts for: board={}, freq={}Hz".format(board, si_format(freq)))
            return

        df = pd.DataFrame(timeouts)

        # Calculate statistical properties
        for api in df['api'].unique():
            for timeout in df[df['api'] == api]['timeout'].unique():
                LOG.info("Benchmark Absolute Timeouts {} - {}s @ {}Hz: {}".format(
                    api,
                    si_format(timeout, precision=0),
                    si_format(freq, precision=0),
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['timeout'] == timeout)]['latency'])
                ))

        # Plot timeout latencies
        fig = px.box(
            data_frame=df,
            x=[si_format(x, precision=0) for x in df['timeout']],
            y='latency',
            color='api',
            points="outliers"
        )
        fig.update_layout(
            title="Absolute Timeouts - Board: {}, Timer Frequency: {}Hz".format(board, si_format(freq)),
            yaxis_title="Timeout Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Timeout Length",
            xaxis_ticksuffix="s",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )
        self._save_figure_as_html(fig, "{}_bench_absolute_timeouts_grouped_by_freq_{:.0f}".format(board, freq))

    def plot_board_absolute_timeouts_grouped_by_timeout(self, board, timeout):
        # Read, combine and process trace samples
        timeouts = []
        for testsuite, testsuite_data in self.benchmarks[board].items():
            for case, data in testsuite_data['benchmarks'].items():
                if case.startswith('Benchmark Absolute Timeouts'):
                    if not data:
                        continue

                    case_timeout = int(data['ticks'][0])/int(data['frequency'][0])
                    if case_timeout == timeout:
                        for duration in self._extract_bench_values_from_json(data['bench_absolute_timeouts']):
                            duration = duration - self._get_gpio_latency(board)
                            timeouts.append({
                                'api': testsuite_data['api'],
                                'frequency': int(data['frequency'][0]),
                                'ticks': int(data['ticks'][0]),
                                'timeout': case_timeout,
                                'duration': duration,
                                'latency': duration - timeout
                            })

        if not timeouts:
            LOG.error("No data for absolute timeouts for: board={}, timeout={}s".format(board, si_format(timeout)))
            return

        df = pd.DataFrame(timeouts)

        # Calculate statistical properties
        for api in df['api'].unique():
            for frequency in df[df['api'] == api]['frequency'].unique():
                LOG.info("Benchmark Absolute Timeouts {} - {}s @ {}Hz: {}".format(
                    api,
                    si_format(timeout, precision=0),
                    si_format(frequency, precision=0),
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['frequency'] == frequency)]['latency'])
                ))

        # Plot timeout latencies
        fig = px.box(
            data_frame=df,
            x=[si_format(x, precision=0) for x in df['frequency']],
            y='latency',
            color='api',
            points="outliers"
        )
        fig.update_layout(
            title="Absolute Timeouts - Board: {}, Timeout Period: {}s".format(board, si_format(timeout)),
            yaxis_title="Timeout Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Timer Frequency",
            xaxis_ticksuffix="Hz",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )
        self._save_figure_as_html(fig, "{}_bench_absolute_timeouts_grouped_by_timeout_{}s".format(board, si_format(timeout)))

    ######################
    ### Overview plots ###
    ######################

    def plot_gpio_latencies(self):
        # Process samples into DataFrame
        durations = []
        for board, suites in self.benchmarks.items():
            for suite, data in suites.items():
                gpio_latencies = self._get_benchmark_data(board, suite, 'Measure GPIO Latency', 'bench_gpio_latency')
                for duration in gpio_latencies:
                    durations.append({
                        'board': board,
                        'api': data['api'],
                        'duration': duration
                    })

                LOG.info("GPIO Latency on board={} for api={}: {}".format(
                    board,
                    data['api'],
                    self._calc_statistical_properties(gpio_latencies))
                )

        df = pd.DataFrame(durations)

        # Generate box plot
        fig = px.box(
            data_frame=df,
            x='board',
            y='duration',
            color='api',
            points="outliers"
        )
        fig.update_traces(marker=dict(opacity=0))  # Detect but hide outliers
        fig.update_layout(
            title="GPIO Latency",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99
            ),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Board",
            xaxis_ticksuffix="",
            xaxis_showgrid=True,
            yaxis_showgrid=True,
            yaxis_rangemode="tozero",
            **self.PLOTLY_COMMON_LAYOUT_PROPS
        )
        self._save_figure_as_html(fig, "overview_gpio_latencies")

    def plot_timeout_latencies(self, freq, ticks):
        # Determine timeout length
        timeout = ticks/freq

        # Process samples into DataFrame
        timeout_durations = []
        for board, suites in self.benchmarks.items():
            for suite, suite_data in suites.items():
                for bench_name, bench_data in suite_data['benchmarks'].items():
                    if bench_name.startswith('Benchmark Absolute Timeouts'):
                        if not bench_data:
                            continue

                        if int(bench_data['frequency'][0]) == freq and int(bench_data['ticks'][0]) == ticks:
                            durations = self._get_benchmark_data(board, suite, bench_name, 'bench_absolute_timeouts')
                            for duration in durations:
                                timeout_durations.append({
                                    'board': board,
                                    'api': suite_data['api'],
                                    'duration': duration - self._get_gpio_latency(board),
                                    'latency': duration - timeout - self._get_gpio_latency(board)
                                })
        if not timeout_durations:
            return

        df = pd.DataFrame(timeout_durations)

        # Calculate statistical properties
        for board in df['board'].unique():
            for api in df[df['board'] == board]['api'].unique():
                LOG.info("Benchmark Absolute Timeouts (freq={}, ticks={}) on board={} for api={}: {}".format(
                    int(freq),
                    int(ticks),
                    board,
                    api,
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['board'] == board)]['latency'])
                ))

        # Plot timeout latencies
        fig = px.box(
            data_frame=df,
            x='board',
            y='latency',
            color='api',
            points="outliers"
        )
        fig.update_traces(marker=dict(opacity=0))  # Detect but hide outliers
        fig.update_layout(
            title=dict(
                text="Absolute Timeouts - Timer Frequency: {}Hz, Timeout: {}s".format(si_format(freq), si_format(timeout)),
                y=1
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99
            ),
            yaxis_title="Timeout Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Board",
            xaxis_ticksuffix="",
            xaxis_showgrid=True,
            yaxis_showgrid=True,
            yaxis_rangemode="tozero",
            **self.PLOTLY_COMMON_LAYOUT_PROPS
        )
        self._save_figure_as_html(fig, "overview_absolute_timeouts_{}Hz_{}s".format(
            si_format(freq, precision=1),
            si_format(timeout, precision=1)
        ))

    def plot_simple_operations(self, op, convert_to_cpu_cycles=False):
        # Process samples into DataFrame
        op_durations = []
        for board, suites in self.benchmarks.items():
            for suite, suite_data in suites.items():
                relevant_benchmarks = {
                    'Benchmark uAPI Timer '+op: 'bench_timer_'+op.lower()+'_uapi',
                    'Benchmark hAPI Timer '+op: 'bench_timer_'+op.lower()+'_hapi',
                    'Benchmark Timer '+op: 'bench_timer_'+op.lower()
                }

                for bench_name, datavar in relevant_benchmarks.items():
                    try:
                        durations = self._get_benchmark_data(board, suite, bench_name, datavar)
                    except KeyError:
                        continue

                    op_label = 'UNKNOWN'
                    if datavar == 'bench_timer_'+op.lower()+'_uapi':
                        op_label = 'periph_utimer (uAPI)'
                    elif datavar == 'bench_timer_'+op.lower()+'_hapi':
                        op_label = 'periph_utimer (hAPI)'
                    elif datavar == 'bench_timer_'+op.lower():
                        op_label = 'periph_timer'

                    if durations:
                        for duration in durations:
                            read_duration = (duration - self._get_gpio_latency(board)) / 10
                            if convert_to_cpu_cycles:
                                read_duration = round(read_duration*self.BOARD_F_CPU[board], ndigits=1)

                            op_durations.append({
                                'board': board,
                                'api': suite_data['api'],
                                'operation': op_label,
                                'duration': read_duration,
                            })

        if not op_durations:
            return

        df = pd.DataFrame(op_durations)

        # Calculate statistical properties
        for board in df['board'].unique():
            for op_label in df[df['board'] == board]['operation'].unique():
                LOG.info("Benchmark operation={} on board={}: {}".format(
                    "{} {}".format(op_label, op),
                    board,
                    self._calc_statistical_properties(df[(df['operation'] == op_label) & (df['board'] == board)]['duration'])
                ))

        # Plot timeout latencies
        fig = px.box(
            data_frame=df,
            x='board',
            y='duration',
            color='operation',
            points="outliers"
        )
        fig.update_traces(marker=dict(opacity=0))  # Detect but hide outliers
        fig.update_layout(
            title=dict(text="Timer {} Operations".format(op), y=1),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99
            ),
            yaxis_title="Execution time" if not convert_to_cpu_cycles else "CPU cycles",
            yaxis_ticksuffix="s" if not convert_to_cpu_cycles else "",
            xaxis_title="Board",
            xaxis_ticksuffix="",
            xaxis_showgrid=True,
            yaxis_showgrid=True,
            yaxis_rangemode="tozero",
            **self.PLOTLY_COMMON_LAYOUT_PROPS
        )
        self._save_figure_as_html(fig, "overview_"+op.lower()+"_operations" + ("_cpu_cycles" if convert_to_cpu_cycles else ""))


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Parse and verify CLI args
    parser = argparse.ArgumentParser("Plot generation routines for periph_(u)timer_benchmarks")
    parser.add_argument("indir", help="Input directory containing xunit.xml files to parse")
    parser.add_argument("outdir", help="Output directory to write plots to")
    args = parser.parse_args()

    if not os.path.exists(args.indir):
        raise ValueError("Input directory does not exist.")

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Generate plots
    plotter = FigurePlotter(
        indir=args.indir,
        outdir=args.outdir
    )

    # Overview plots
    plotter.plot_gpio_latencies()

    for operation in ["Read", "Write", "Set", "Clear"]:
        plotter.plot_simple_operations(operation)
        plotter.plot_simple_operations(operation, convert_to_cpu_cycles=True)

    for freq in [1e7, 1e6, 1e5, 1e4]:
        for ticks in [1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9]:
            plotter.plot_timeout_latencies(freq=freq, ticks=ticks)

    # Board specific plots
    for board in plotter.get_boards():
        plotter.plot_board_gpio_latency(board)
        plotter.plot_board_read_write_ops(board)
        plotter.plot_board_set_clear_ops(board)

        plotter.plot_board_absolute_timeouts_grouped_by_freq(board, freq=10e6)
        plotter.plot_board_absolute_timeouts_grouped_by_freq(board, freq=10e5)
        plotter.plot_board_absolute_timeouts_grouped_by_freq(board, freq=10e4)
        plotter.plot_board_absolute_timeouts_grouped_by_freq(board, freq=10e3)

        plotter.plot_board_absolute_timeouts_grouped_by_timeout(board, timeout=1e-6)
        plotter.plot_board_absolute_timeouts_grouped_by_timeout(board, timeout=1e-5)
        plotter.plot_board_absolute_timeouts_grouped_by_timeout(board, timeout=1e-4)
        plotter.plot_board_absolute_timeouts_grouped_by_timeout(board, timeout=1e-3)
        plotter.plot_board_absolute_timeouts_grouped_by_timeout(board, timeout=1e-2)
        plotter.plot_board_absolute_timeouts_grouped_by_timeout(board, timeout=1e-1)
        plotter.plot_board_absolute_timeouts_grouped_by_timeout(board, timeout=1e-0)


if __name__ == "__main__":
    main()
