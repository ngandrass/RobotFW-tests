#!/usr/bin/env python3

import argparse
import json
import logging
import os

import numpy as np
from si_prefix import si_format
import xmltodict

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

LOG = logging.getLogger(__name__)


class FigurePlotter:

    def __init__(self, utimer_xunit_file, timer_xunit_file, outdir):
        self.outdir = outdir
        self.benchmarks = {
            'utimer': self._parse_xunit(utimer_xunit_file, 'tests_periph_utimer_benchmarks'),
            'timer': self._parse_xunit(timer_xunit_file, 'tests_periph_timer_benchmarks'),
        }
        self.board = self.benchmarks['utimer']['Record Metadata']['board'][0]
        self.riot_version = self.benchmarks['utimer']['Record Metadata']['riot_version'][0]

        self.gpio_latency = np.mean([self._calc_gpio_latency(x['Measure GPIO Latency']['bench_gpio_latency']) for x in self.benchmarks.values()])
        LOG.info("GPIO latency: {}".format(self.gpio_latency))

    def _parse_xunit(self, xunit_file, testsuite_name):
        # Parse xUnit file
        with open(xunit_file) as fd:
            self.xunit = xmltodict.parse(fd.read())

        # Verify testsuite
        testsuite = self.xunit['testsuite']
        if testsuite['@name'] != testsuite_name:
            raise ImportError("Testsuite names doesn't match! Expected: '{}'".format(testsuite_name))

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

        LOG.info("Parsed {} benchmarks from {} testsuite".format(
            len(benchmarks),
            testsuite_name
        ))

        return benchmarks

    def _extract_bench_values_from_json(self, bench_props, values_key="values"):
        values = []
        for traceset_json in bench_props:
            traceset = json.loads(traceset_json.replace("'", "\""))
            values = values + traceset[values_key]

        return values

    def _calc_statistical_properties(self, dataset):
        return {
            'max': np.max(dataset),
            'min': np.min(dataset),
            'avg': np.average(dataset),
            'mean': np.mean(dataset),
            'stdev': np.std(dataset),
            'samples': len(dataset)
        }

    def _calc_gpio_latency(self, gpio_latency_bench_data):
        return self._calc_statistical_properties(
            self._extract_bench_values_from_json(gpio_latency_bench_data)
        )['avg']

    def _save_figure_as_html(self, fig, title):
        outfile = "{}/{}.html".format(self.outdir, title)
        fig.write_html(
            outfile,
            full_html=True,
            include_plotlyjs=True,
        )

        LOG.info("Wrote figure: {}".format(outfile))

    def plot_gpio_latency(self):
        # Process samples
        BENCH_NAME = 'bench_gpio_latency'
        durations = {
            'periph_utimer': self._extract_bench_values_from_json(self.benchmarks['utimer']['Measure GPIO Latency'][BENCH_NAME]),
            'periph_timer': self._extract_bench_values_from_json(self.benchmarks['timer']['Measure GPIO Latency'][BENCH_NAME]),
        }

        LOG.info("periph_utimer GPIO Latency: {}".format(self._calc_statistical_properties(durations['periph_utimer'])))
        LOG.info("periph_timer GPIO Latency: {}".format(self._calc_statistical_properties(durations['periph_timer'])))

        # Generate box plot
        data = pd.DataFrame.from_dict(durations, orient='index').transpose()
        fig = go.Figure()
        fig.add_trace(go.Box(name='periph_utimer', y=durations['periph_utimer']))
        fig.add_trace(go.Box(name='periph_timer', y=durations['periph_timer']))
        fig.update_layout(
            title="GPIO Latency - Board: {}".format(self.board),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Timer Driver",
            xaxis_showgrid=True,
            yaxis_showgrid=True,
            showlegend=False
        )

        self._save_figure_as_html(fig, BENCH_NAME)

    def plot_read_write_ops(self):
        # Read, combine and process trace samples. Remove GPIO overhead and scale down by the repeat factor of 10
        durations = []
        durations = durations + [('periph_utimer', 'Read (uAPI)',  (x-self.gpio_latency)/10) for x in self._extract_bench_values_from_json(self.benchmarks['utimer']['Benchmark uAPI Timer Read']['bench_timer_read_uapi'])]
        durations = durations + [('periph_utimer', 'Read (hAPI)',  (x-self.gpio_latency)/10) for x in self._extract_bench_values_from_json(self.benchmarks['utimer']['Benchmark hAPI Timer Read']['bench_timer_read_hapi'])]
        durations = durations + [('periph_utimer', 'Write (uAPI)', (x-self.gpio_latency)/10) for x in self._extract_bench_values_from_json(self.benchmarks['utimer']['Benchmark uAPI Timer Write']['bench_timer_write_uapi'])]
        durations = durations + [('periph_utimer', 'Write (hAPI)', (x-self.gpio_latency)/10) for x in self._extract_bench_values_from_json(self.benchmarks['utimer']['Benchmark hAPI Timer Write']['bench_timer_write_hapi'])]
        durations = durations + [('periph_timer',  'Read',         (x-self.gpio_latency)/10) for x in self._extract_bench_values_from_json(self.benchmarks['timer']['Benchmark Timer Read']['bench_timer_read'])]
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
            title="Timer Read and Write Operations - Board: {}".format(self.board),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Operation (via API)",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )
        self._save_figure_as_html(fig, "bench_timer_read_write")

    def plot_absolute_timeouts_grouped_by_freq(self, freq, ignored_timeouts=[]):
        # Read, combine and process trace samples
        timeouts = []
        for api, benchmarks in self.benchmarks.items():
            for case, data in benchmarks.items():
                if case.startswith('Benchmark Absolute Timeouts'):
                    if int(data['frequency'][0]) == freq:
                        timeout = int(data['ticks'][0])/int(data['frequency'][0])
                        if timeout not in ignored_timeouts:
                            for duration in self._extract_bench_values_from_json(data['bench_absolute_timeouts']):
                                duration = duration - self.gpio_latency
                                timeouts.append({
                                    'api': "periph_{}".format(api),
                                    'frequency': int(data['frequency'][0]),
                                    'ticks': int(data['ticks'][0]),
                                    'timeout': timeout,
                                    'duration': duration,
                                    'latency': duration - timeout
                                })

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
            title="Absolute Timeouts - Board: {}, Timer Frequency: {}Hz".format(self.board, si_format(freq)),
            yaxis_title="Timeout Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Timeout Length",
            xaxis_ticksuffix="s",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )
        self._save_figure_as_html(fig, "bench_absolute_timeouts_grouped_by_freq_{:.0f}".format(freq))

    def plot_absolute_timeouts_grouped_by_timeout(self, timeout):
        # Read, combine and process trace samples
        timeouts = []
        for api, benchmarks in self.benchmarks.items():
            for case, data in benchmarks.items():
                if case.startswith('Benchmark Absolute Timeouts'):
                    case_timeout = int(data['ticks'][0])/int(data['frequency'][0])
                    if case_timeout == timeout:
                        for duration in self._extract_bench_values_from_json(data['bench_absolute_timeouts']):
                            duration = duration - self.gpio_latency
                            timeouts.append({
                                'api': "periph_{}".format(api),
                                'frequency': int(data['frequency'][0]),
                                'ticks': int(data['ticks'][0]),
                                'timeout': case_timeout,
                                'duration': duration,
                                'latency': duration - timeout
                            })

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
            title="Absolute Timeouts - Board: {}, Timeout Period: {}s".format(self.board, si_format(timeout)),
            yaxis_title="Timeout Latency",
            yaxis_ticksuffix="s",
            xaxis_title="Timer Frequency",
            xaxis_ticksuffix="Hz",
            xaxis_showgrid=True,
            yaxis_showgrid=True
        )
        self._save_figure_as_html(fig, "bench_absolute_timeouts_grouped_by_timeout_{}s".format(si_format(timeout)))


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Parse and verify CLI args
    parser = argparse.ArgumentParser("Plot generation routines for periph_(u)timer_benchmarks")
    parser.add_argument("utimer_xunit", help="xUnit result file for periph_utimer to parse")
    parser.add_argument("timer_xunit", help="xUnit result file for periph_timer to parse")
    parser.add_argument("outdir", help="Output directory to write plots to")
    args = parser.parse_args()

    if not os.path.isfile(args.utimer_xunit) or not os.path.isfile(args.timer_xunit):
        raise ValueError("Invalid input file.")

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Generate plots
    plotter = FigurePlotter(
        utimer_xunit_file=args.utimer_xunit,
        timer_xunit_file=args.timer_xunit,
        outdir=args.outdir
    )
    plotter.plot_gpio_latency()
    plotter.plot_read_write_ops()
    # plotter.plot_absolute_timeouts_grouped_by_freq(freq=10e6, ignored_timeouts=[1, 0.1])
    plotter.plot_absolute_timeouts_grouped_by_freq(freq=10e6)
    plotter.plot_absolute_timeouts_grouped_by_freq(freq=10e5)
    plotter.plot_absolute_timeouts_grouped_by_freq(freq=10e4)
    plotter.plot_absolute_timeouts_grouped_by_freq(freq=10e3)
    plotter.plot_absolute_timeouts_grouped_by_timeout(timeout=1e-6)
    plotter.plot_absolute_timeouts_grouped_by_timeout(timeout=1e-5)
    plotter.plot_absolute_timeouts_grouped_by_timeout(timeout=1e-4)
    plotter.plot_absolute_timeouts_grouped_by_timeout(timeout=1e-3)
    plotter.plot_absolute_timeouts_grouped_by_timeout(timeout=1e-2)
    plotter.plot_absolute_timeouts_grouped_by_timeout(timeout=1e-1)
    plotter.plot_absolute_timeouts_grouped_by_timeout(timeout=1e-0)


if __name__ == "__main__":
    main()
