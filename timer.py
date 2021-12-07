# timer.py
import time

"""
General purpose timer class that starts and stops a stopwatch,
and can return the elapsed time using check_time.
"""
class Timer:

    def __init__(self):
        self._start_time = None

    """ Start timer. """
    def start(self):
        self._start_time = time.perf_counter()

    """ Sets the timer to 0, and returns the elapsed time (ms). """
    def stop(self):
        """Stop the timer, and report the elapsed time"""
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        return float(format(elapsed_time*1000, ".2f"))

    """ returns the elapsed time (ms) since start, but doesn't stop the timer. """
    def check_time(self):
        elapsed_time = time.perf_counter() - self._start_time
        return float(format(elapsed_time*1000, ".2f"))
