# timer.py
import time


class Timer:

    def __init__(self):
        self._start_time = None

    # Start timer
    def start(self):
        self._start_time = time.perf_counter()

    # Sets the timer to 0, and returns the elapsed time (ms).
    def stop(self):
        """Stop the timer, and report the elapsed time"""
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        return elapsed_time*1000

    # returns the elapsed time (ms) since start, but doesn't stop the timer.
    def check_time(self):
        elapsed_time = time.perf_counter() - self._start_time
        return elapsed_time*1000
