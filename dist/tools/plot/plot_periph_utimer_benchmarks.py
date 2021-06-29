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

    def plot_gpio_latency(self):
        # Combine trace samples
        durations = []
        for traceset_json in self.benchmarks['Measure GPIO Latency']['bench_gpio_latency']:
            traceset = json.loads(traceset_json.replace("'", "\""))
            durations = durations + traceset['values']

        # Calculate statistical properties
        stats = {
            'max': np.max(durations),
            'min': np.min(durations),
            'avg': np.average(durations),
            'mean': np.mean(durations),
            'stdev': np.std(durations),
            'samples': len(durations)
        }

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

        fig.show()
        LOG.info("GPIO Latency: {}".format(stats))


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


if __name__ == "__main__":
    main()
