from periph_utimer_benchmarks_if import PeriphUTimerBenchmarksIf
from robot.version import get_version


class PeriphUTimerBenchmarks(PeriphUTimerBenchmarksIf):

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = get_version()
