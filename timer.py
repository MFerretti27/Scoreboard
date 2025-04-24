"""This module provides a Timer."""
import time


class Timer:
    """This class provides functionality to check if a certain time interval has expired."""
    def __init__(self, seconds) -> None:
        """Initializes the timer with a specified interval in seconds.

        :param interval_seconds: The interval in seconds for the timer.
        """
        self.interval = seconds
        self.next_time = time.time() + self.interval

    def expired(self) -> bool:
        """Checks if the timer has expired.

        :return: True if the timer has expired, otherwise False.
        """
        now = time.time()
        if now >= self.next_time:
            self.next_time = now + self.interval  # ⏱ reset immediately
            return True
        return False

    def reset(self) -> None:
        """Resets the timer to the current time."""
        self.next_time = time.time() + self.interval
        print("Timer reset!")

    def pause(self) -> None:
        """Pauses the timer."""
        self.paused = True
        print("Timer paused.")

    def resume(self) -> None:
        """Resumes the timer."""
        self.paused = False
        print("Timer resumed.")
