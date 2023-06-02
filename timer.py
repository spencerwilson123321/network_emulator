import time


class Timer:
    """
        General purpose timer class that starts and stops a stopwatch,
        and can return the elapsed time using check_time.
    """

    def __init__(self):
        self._start_time = None

    def start(self):
        self._start_time = time.perf_counter()

    def stop(self):
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        return float(format(elapsed_time*1000, ".2f"))

    def check_time(self):
        elapsed_time = time.perf_counter() - self._start_time
        return float(format(elapsed_time*1000, ".2f"))
