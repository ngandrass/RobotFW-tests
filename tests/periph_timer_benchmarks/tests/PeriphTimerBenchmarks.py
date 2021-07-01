from periph_timer_benchmarks_if import PeriphTimerBenchmarksIf
from robot.version import get_version


class PeriphTimerBenchmarks(PeriphTimerBenchmarksIf):

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = get_version()
