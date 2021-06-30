#!/usr/bin/env python3

import argparse
import json
import logging
import os

import numpy as np
import xmltodict

import pandas as pd
import plotly.express as px

LOG = logging.getLogger(__name__)


class FigurePlotter:

    def __init__(self, testsuite_name, xunit_file, outdir):
        self.outdir = outdir

        # Parse xUnit file and extract benchmark data
        with open(xunit_file) as fd:
            self.xunit = xmltodict.parse(fd.read())

        self.benchmarks = {}
        testsuite = self.xunit['testsuite']
        if testsuite['@name'] != testsuite_name:
            raise ImportError("Testsuite names doesn't match! Expected: '{}'".format(testsuite_name))

        for benchmark in testsuite['testcase']:
            props = {}
            for property in benchmark['properties']['property']:
                if property['@name'] not in props:
                    props[property['@name']] = []
                props[property['@name']].append(property['@value'])
            self.benchmarks[benchmark['@name']] = props

        # Determine metadata
        self.board = self.benchmarks['Record Metadata']['board'][0]
        LOG.info("Parsed {} benchmarks run on a {} board.".format(
            len(self.benchmarks),
            self.board
        ))

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
        durations = self._extract_bench_values_from_json(self.benchmarks['Measure GPIO Latency'][BENCH_NAME])
        LOG.info("GPIO Latency: {}".format(self._calc_statistical_properties(durations)))

        # Generate box plot
        fig = px.box(
            data_frame=pd.DataFrame({self.board: durations}),
            points="outliers"
        )

        fig.update_layout(
            title="GPIO Latency",
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Board",
        )

        self._save_figure_as_html(fig, BENCH_NAME)

    def plot_read_write_ops(self):
        # Read, combine and process trace samples
        reads_uapi = self._extract_bench_values_from_json(self.benchmarks['Benchmark uAPI Timer Read']['bench_timer_read_uapi'])
        reads_hapi = self._extract_bench_values_from_json(self.benchmarks['Benchmark hAPI Timer Read']['bench_timer_read_hapi'])
        writes_uapi = self._extract_bench_values_from_json(self.benchmarks['Benchmark uAPI Timer Write']['bench_timer_write_uapi'])
        writes_hapi = self._extract_bench_values_from_json(self.benchmarks['Benchmark hAPI Timer Write']['bench_timer_write_hapi'])

        LOG.info("Benchmark uAPI Timer Read: {}".format(self._calc_statistical_properties(reads_uapi)))
        LOG.info("Benchmark hAPI Timer Read: {}".format(self._calc_statistical_properties(reads_hapi)))
        LOG.info("Benchmark uAPI Timer Write: {}".format(self._calc_statistical_properties(writes_uapi)))
        LOG.info("Benchmark uAPI Timer Write: {}".format(self._calc_statistical_properties(writes_hapi)))

        # Generate plot
        data = pd.DataFrame({
            'Read (uAPI)':  reads_uapi,
            'Read (hAPI)':  reads_hapi,
            'Write (uAPI)': writes_uapi,
            'Write (hAPI)': writes_hapi
        })

        fig = px.box(data_frame=data, points="outliers")
        fig.update_layout(
            title="Timer Read and Write Operations - Board: {}".format(self.board),
            yaxis_title="Execution time",
            yaxis_ticksuffix="s",
            xaxis_title="Operation (via API)"
        )
        self._save_figure_as_html(fig, "bench_timer_read_write")


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Parse and verify CLI args
    parser = argparse.ArgumentParser("Plot generation routines for periph_utimer_benchmarks")
    parser.add_argument("input", help="xUnit result file to parse")
    parser.add_argument("outdir", help="Output directory to write plots to")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        raise ValueError("Invalid input file.")

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Generate plots
    plotter = FigurePlotter(testsuite_name="tests_periph_utimer_benchmarks", xunit_file=args.input, outdir=args.outdir)
    plotter.plot_gpio_latency()
    plotter.plot_read_write_ops()


if __name__ == "__main__":
    main()
