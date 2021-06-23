from periph_utimer_if import PeriphUTimerIf
from robot.version import get_version


class PeriphUTimer(PeriphUTimerIf):

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = get_version()
