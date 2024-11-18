import time


class Timer:
    """
    Timer to measure wall clock time
    """

    def __init__(self, name: str):
        """
        Initializer

        :param name: name of the timer (to be printed out)
        """
        self.name = name

        self.start_time = None
        self.stop_time = None

    def start(self) -> None:
        """
        Start the timer

        :return: NOne
        """
        self.start_time = time.perf_counter_ns()

    def stop(self) -> None:
        """
        Stop the timer
        :return: None
        """
        self.stop_time = time.perf_counter_ns()

    def reset(self) -> None:
        """
        Reset the timer
        :return: None
        """
        self.start_time = None
        self.stop_time = None

    def get_time(self,
                 unit: str = 's') -> float:
        """
        Return the measured time in `float` format.

        :param unit: unit of measurement (s, ms, us)
        :return: return measured time in the given unit
        """

        # time is measured in ns, so scale as necessary
        if unit == 's':
            scalar = 1e9
        elif unit == 'ms':
            scalar = 1e6
        elif unit == 'us':
            scalar = 1e3
        else:
            scalar = 1

        elapsed_time = (self.stop_time - self.start_time) / scalar
        return elapsed_time

    def print(self,
              unit: str = 's') -> None:
        """
        Print the measured time.

        :param unit: unit to print (s, ms, us)
        :return: None
        """

        elapsed_time = self.get_time(unit=unit)
        print(f"[{self.name}] Timer: {elapsed_time:.2f} {unit}")
