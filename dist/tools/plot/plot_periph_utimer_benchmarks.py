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

    XUNIT_FILE_PATTERN = '*xunit.xml'
    XUNIT_TESTSUITE_NAME_PATTERN = r"^tests_periph_(u)?timer_benchmarks$"

    SUITE_TIMER = 'tests_periph_timer_benchmarks'
    SUITE_UTIMER = 'tests_periph_utimer_benchmarks'
    EXPECTED_SUITES = [
        SUITE_TIMER,
        SUITE_UTIMER
    ]

    PLOTLY_COMMON_PLOT_PROPS = dict(
        color_discrete_sequence=px.colors.qualitative.Plotly
    )

    PLOTLY_COMMON_LAYOUT_PROPS = dict(
        autosize=False,
        width=600,
        height=500,
        margin=dict(l=10, r=10, b=10, t=10, pad=1),
        template="plotly_white",
        xaxis_mirror=True,
        xaxis_showline=True,
        yaxis_mirror=True,
        yaxis_showline=True
    )

    def __init__(self, indir, outdir, dump_data):
        self.indir = indir
        self.outdir = outdir
        self.dump_data = dump_data

        self.benchmarks = {}
        self.board_fcpu = {}
        self.gpio_latencies = {}

        self._parse_all_benchmarks_from_dir(self.indir)
        self._validate_benchmark_data()
        self._calc_board_fcpu()
        self._calc_gpio_latencies()

        # GPIO latencies 500 repeats (TEST_REPEATS = 10)
        # self.gpio_latencies = {'arduino-mega2560': 5.010871000000085e-06, 'nucleo-l152re': 7.175460000000281e-07, 'stk3200': 1.083816000000127e-06, 'nucleo-f767zi': 4.309980000001695e-07, 'nucleo-f103rb': 4.6523099999990044e-07, 'esp32-wroom-32': 4.677369999999414e-07, 'z1': 7.87545200000019e-06, 'esp8266-esp-12x': 4.3250200000000227e-07, 'slstk3401a': 5.742140000002957e-07, 'slstk3400a': 1.083989999999952e-06, 'nucleo-g474re': 1.0577600000019707e-07}

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
                'build_timestamp': xunit_data['Record Metadata']['build_timestamp'][0],
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
            if 'skipped' in benchmark:
                continue

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

    def _validate_benchmark_data(self):
        for board, benchmarks in self.benchmarks.items():
            for suite in self.EXPECTED_SUITES:
                if suite not in benchmarks:
                    raise ValueError(f"{suite} is missing for board {board}.")

        return True

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

    def _calc_board_fcpu(self):
        for board, suites in self.benchmarks.items():
            for suite in suites.values():
                self.board_fcpu[board] = int(suite['freq_cpu'])

    def _calc_gpio_latencies(self):
        for board, suites in self.benchmarks.items():
            durations = []
            for suite in suites.values():
                durations = durations + self._extract_bench_values_from_json(
                    suite['benchmarks']['Measure GPIO Latency 1us']['bench_gpio_latency']
                )

            self.gpio_latencies[board] = np.average(durations)
            LOG.info("GPIO Latency on board {} = {}".format(board, self.gpio_latencies[board]))

    def _dump_dataframe_to_csv(self, df, title):
        outfile = "{}.csv".format(os.path.join(self.outdir, title))
        df.to_csv(
            outfile,
            sep=",",
            header=True,
            index=True
        )
        LOG.info("Exported DataFrame to csv: {}".format(outfile))

    def _save_figure_as_html(self, fig, title):
        outfile = "{}.html".format(os.path.join(self.outdir, title))
        fig.write_html(
            outfile,
            full_html=True,
            include_plotlyjs=True,
        )
        LOG.info("Wrote figure: {}".format(outfile))

    def _save_figure_as_image(self, fig, title, filetype="pdf"):
        outfile = "{}.{}".format(os.path.join(self.outdir, title), filetype)
        fig.write_image(outfile, scale=1)
        LOG.info("Wrote figure: {}".format(outfile))

    def _save_figure(self, fig, title):
        self._save_figure_as_html(fig, title)
        #self._save_figure_as_image(fig, title, filetype="png")
        #self._save_figure_as_image(fig, title, filetype="svg")
        self._save_figure_as_image(fig, title, filetype="pdf")

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
        durations = []
        for testsuite, testsuite_data in self.benchmarks[board].items():
            for case, data in testsuite_data['benchmarks'].items():
                if case.startswith('Measure GPIO Latency'):
                    if not data:
                        continue

                    timeout_us = int(data['timeout_us'][0])
                    for duration in self._extract_bench_values_from_json(data['bench_gpio_latency']):
                        durations.append({
                            'api': testsuite_data['api'],
                            'timeout': timeout_us / 1e6,
                            'timeout_us': timeout_us,
                            'duration': duration
                        })
        df = pd.DataFrame(durations)

        # Calculate statistical properties
        for api in df['api'].unique():
            for timeout_us in df[df['api'] == api]['timeout_us'].unique():
                LOG.info("GPIO Latency {}us on board={} for api={}: {}".format(
                    timeout_us,
                    board,
                    api,
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['timeout_us'] == timeout_us)]['duration'])
                ))

        # Generate box plot
        fig = px.box(
            data_frame=df,
            x=[si_format(x, precision=0) for x in df['timeout']],
            y='duration',
            color='api',
            points="outliers",
            **self.PLOTLY_COMMON_PLOT_PROPS
        )
        fig.update_traces(
            marker=dict(opacity=0),  # Detect but hide outliers
            line=dict(width=1)
        )
        fig.update_layout(
            title="GPIO Latency - Board: {}".format(board),
            legend=dict(
                title="",
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99,
            ),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Spin timeout",
            xaxis_ticksuffix="s",
            xaxis_showgrid=True,
            yaxis_showgrid=True,
            yaxis_rangemode="tozero",
            **self.PLOTLY_COMMON_LAYOUT_PROPS
        )

        self._save_figure(fig, "{}_gpio_latency".format(board))

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

        title = "{}_bench_timer_read_write".format(board)
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

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

        title = "{}_bench_timer_set_clear".format(board)
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

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

        title = "{}_bench_absolute_timeouts_grouped_by_freq_{:.0f}".format(board, freq)
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

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

        title = "{}_bench_absolute_timeouts_grouped_by_timeout_{}s".format(board, si_format(timeout))
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

    def plot_board_periodic_timeouts_grouped_by_timeout(self, board, timeout):
        # Read, combine and process trace samples
        timeouts = []
        for testsuite, testsuite_data in self.benchmarks[board].items():
            for case, data in testsuite_data['benchmarks'].items():
                if case.startswith('Benchmark Periodic Timeouts'):
                    if not data:
                        continue

                    case_timeout = int(data['ticks'][0])/int(data['frequency'][0])
                    if case_timeout == timeout:
                        for duration in self._extract_bench_values_from_json(data['bench_periodic_timeouts']):
                            cycles = int(data['cycles'][0])
                            duration = (duration / cycles) - self._get_gpio_latency(board)
                            timeouts.append({
                                'api': testsuite_data['api'],
                                'frequency': int(data['frequency'][0]),
                                'ticks': int(data['ticks'][0]),
                                'cycles': cycles,
                                'timeout': case_timeout,
                                'duration': duration,
                                'latency': duration - timeout
                            })

        if not timeouts:
            LOG.error("No data for periodic timeouts for: board={}, timeout={}s".format(board, si_format(timeout)))
            return

        df = pd.DataFrame(timeouts)

        # Calculate statistical properties
        for api in df['api'].unique():
            for cycles in df[df['api'] == api]['cycles'].unique():
                LOG.info("Benchmark Periodic Timeouts {} - {}x {}s: {}".format(
                    api,
                    cycles,
                    si_format(timeout, precision=0),
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['cycles'] == cycles)]['latency'])
                ))

        # Plot timeout latencies
        fig = px.box(
            data_frame=df,
            x=[si_format(x, precision=0) for x in df['cycles']],
            y='latency',
            color='api',
            points="outliers"
        )
        fig.update_layout(
            title="Periodic Timeouts - Board: {}, Timeout Period: {}s".format(board, si_format(timeout)),
            yaxis_title="Timeout Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Timeout Cycles",
            xaxis_ticksuffix="",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )

        title = "{}_bench_periodic_timeouts_grouped_by_timeout_{}s".format(board, si_format(timeout))
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

    def plot_board_parallel_callback_latencies(self, board):
        # Read, combine and process trace samples
        timeouts = []
        freq = None
        timeout = None
        for testsuite, testsuite_data in self.benchmarks[board].items():
            for case, data in testsuite_data['benchmarks'].items():
                if case.startswith('Benchmark Parallel Callbacks'):
                    if not data:
                        continue

                    case_timeout = int(data['ticks'][0])/int(data['frequency'][0])
                    freq = int(data['frequency'][0])
                    timeout = case_timeout
                    for duration in self._extract_bench_values_from_json(data['bench_parallel_callbacks']):
                        duration = duration - self._get_gpio_latency(board)
                        timeouts.append({
                            'api': testsuite_data['api'],
                            'frequency': int(data['frequency'][0]),
                            'ticks': int(data['ticks'][0]),
                            'channels': int(data['channels'][0]),
                            'timeout': case_timeout,
                            'duration': duration,
                            'latency': duration - case_timeout
                        })

        if not timeouts:
            LOG.error(f"No data for parallel callback timeouts for: board={board}")
            return

        df = pd.DataFrame(timeouts)

        # Calculate statistical properties
        for api in df['api'].unique():
            for channels in df[df['api'] == api]['channels'].unique():
                LOG.info("Benchmark Parallel Callbacks: board={}, api={}, freq={}Hz, timeout={}s, channels={}: {}".format(
                    board,
                    api,
                    si_format(freq, precision=0),
                    si_format(timeout, precision=0),
                    channels,
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['channels'] == channels)]['latency'])
                ))

        # Plot latencies of latest callback latency for each benchmarked number of parallel channels
        fig = px.box(
            data_frame=df,
            x=[channels for channels in df['channels']],
            y='latency',
            color='api',
            points="outliers"
        )
        fig.update_layout(
            title=f"Parallel Callback Execution Latency - Board: {board}, Timeout: {si_format(timeout, precision=0)}s, Frequency: {si_format(freq, precision=0)}Hz",
            yaxis_title="Timeout Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Parallel Timeouts",
            xaxis_ticksuffix="",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )

        title = f"{board}_bench_parallel_callbacks"
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

    ######################
    ### Overview plots ###
    ######################

    def plot_gpio_latencies(self):
        # Process samples into DataFrame
        durations = []
        for board, suites in self.benchmarks.items():
            for suite, data in suites.items():
                gpio_latencies = self._get_benchmark_data(board, suite, 'Measure GPIO Latency 1us', 'bench_gpio_latency')
                for duration in gpio_latencies:
                    durations.append({
                        'board': board,
                        'api': data['api'],
                        'duration': duration,
                        'samples': len(gpio_latencies)
                    })

                LOG.info("GPIO Latency 1us on board={} for api={}: {}".format(
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
            points="outliers",
            **self.PLOTLY_COMMON_PLOT_PROPS
        )
        fig.update_traces(
            marker=dict(opacity=0),  # Detect but hide outliers
            line=dict(width=1)
        )
        fig.update_layout(
            title="GPIO Latency",
            legend=dict(
                title="",
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99,
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

        self._save_figure(fig, "overview_gpio_latencies")
        if self.dump_data:
            self._dump_dataframe_to_csv(df, "overview_gpio_latencies")

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
                                    'frequency': freq,
                                    'ticks': ticks,
                                    'duration': duration - self._get_gpio_latency(board),
                                    'latency': duration - timeout - self._get_gpio_latency(board),
                                    'samples': len(durations)
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
            points="outliers",
            **self.PLOTLY_COMMON_PLOT_PROPS
        )
        fig.update_traces(
            marker=dict(opacity=0),  # Detect but hide outliers
            line=dict(width=1)
        )
        fig.update_layout(
            title=dict(
                text="Absolute Timeouts - Timer Frequency: {}Hz, Timeout: {}s".format(si_format(freq), si_format(timeout)),
                y=1
            ),
            legend=dict(
                title="",
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99,
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

        title = "overview_absolute_timeouts_{}Hz_{}s".format(
            si_format(freq, precision=1),
            si_format(timeout, precision=1)
        )
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

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
                                read_duration = round(read_duration*self.board_fcpu[board], ndigits=1)

                            op_durations.append({
                                'board': board,
                                'api': suite_data['api'],
                                'operation': op_label,
                                'functioncall': op.lower(),
                                'duration': read_duration,
                                'samples': len(durations) + int(len(durations)/49)
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
            points="outliers",
            **self.PLOTLY_COMMON_PLOT_PROPS
        )
        fig.update_traces(
            marker=dict(opacity=0),  # Detect but hide outliers
            line=dict(width=1)
        )
        fig.update_layout(
            title=dict(text="Timer {} Operations".format(op), y=1),
            legend=dict(
                title="",
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99,
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

        title = "overview_"+op.lower()+"_operations" + ("_cpu_cycles" if convert_to_cpu_cycles else "")
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)

    def plot_parallel_callbacks(self, channels):
        # Process samples into DataFrame
        samples = []
        timeout = None
        freq = None
        for board, suites in self.benchmarks.items():
            for suite, suite_data in suites.items():
                for bench_name, bench_data in suite_data['benchmarks'].items():
                    if bench_name.startswith('Benchmark Parallel Callbacks'):
                        if not bench_data:
                            continue

                        if int(bench_data['channels'][0]) == channels:
                            freq = int(bench_data['frequency'][0])
                            timeout = int(bench_data['ticks'][0])/int(bench_data['frequency'][0])
                            durations = self._get_benchmark_data(board, suite, bench_name, 'bench_parallel_callbacks')
                            for duration in durations:
                                samples.append({
                                    'board': board,
                                    'api': suite_data['api'],
                                    'frequency': freq,
                                    'timeout': timeout,
                                    'channels': channels,
                                    'duration': duration - self._get_gpio_latency(board),
                                    'latency': duration - timeout - self._get_gpio_latency(board)
                                })

        if len(samples) == 0:
            return

        df = pd.DataFrame(samples)

        # Calculate statistical properties
        for board in df['board'].unique():
            for api in df[df['board'] == board]['api'].unique():
                LOG.info("Benchmark Parallel Callbacks {}x {}s @ {}Hz on board={} for api={}: {}".format(
                    channels,
                    si_format(timeout, precision=0),
                    si_format(freq, precision=0),
                    board,
                    api,
                    self._calc_statistical_properties(df[(df['api'] == api) & (df['board'] == board)]['latency'])
                ))

        # Plot parallel callback latencies
        fig = px.box(
            data_frame=df,
            x='board',
            y='latency',
            color='api',
            points="outliers",
            **self.PLOTLY_COMMON_PLOT_PROPS
        )
        fig.update_traces(
            marker=dict(opacity=0),  # Detect but hide outliers
            line=dict(width=1)
        )
        fig.update_layout(
            title=dict(
                text=f"Parallel Callback Execution Latency - {channels} Channel(s) x {si_format(timeout, precision=0)}s @ {si_format(freq, precision=0)}Hz",
                y=1
            ),
            legend=dict(
                title="",
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=0.99,
            ),
            yaxis_title="Callback Execution Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Board",
            xaxis_ticksuffix="",
            xaxis_showgrid=True,
            yaxis_showgrid=True,
            yaxis_rangemode="tozero",
            **self.PLOTLY_COMMON_LAYOUT_PROPS
        )

        title = f"overview_parallel_callbacks_{channels}x"
        self._save_figure(fig, title)
        if self.dump_data:
            self._dump_dataframe_to_csv(df, title)


def main():
    # Parse and verify CLI args
    parser = argparse.ArgumentParser("Plot generation routines for periph_(u)timer_benchmarks")
    parser.add_argument("indir", help="Input directory containing xunit.xml files to parse")
    parser.add_argument("outdir", help="Output directory to write plots to")
    parser.add_argument(
        "--dump-data",
        dest="dump_data",
        action="store_true",
        default=False,
        help="Dumps generated Pandas DaraFrames to outdir"
    )
    args = parser.parse_args()

    if not os.path.exists(args.indir):
        raise ValueError("Input directory does not exist.")

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(args.outdir, "output.log"))
        ]
    )

    # Generate plots
    plotter = FigurePlotter(
        indir=args.indir,
        outdir=args.outdir,
        dump_data=args.dump_data
    )

    # Overview plots
    plotter.plot_gpio_latencies()

    for operation in ["Read", "Write", "Set", "Clear"]:
        plotter.plot_simple_operations(operation)
        plotter.plot_simple_operations(operation, convert_to_cpu_cycles=True)

    for freq in [1e7, 1e6, 1e5, 1e4, 250000, 32768]:
        for ticks in [1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 250]:
            plotter.plot_timeout_latencies(freq=freq, ticks=ticks)

    for channels in range(1, 9):
        plotter.plot_parallel_callbacks(channels)

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

        plotter.plot_board_periodic_timeouts_grouped_by_timeout(board, timeout=1e-3)

        plotter.plot_board_parallel_callback_latencies(board)


if __name__ == "__main__":
    main()
