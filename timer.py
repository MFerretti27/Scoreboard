import asyncio
import time


class Timer:
    """Asynchronous timer with pause, resume, reset, and expiration checking."""
    def __init__(self, seconds: float):
        self.interval = seconds
        self.next_time = time.time() + self.interval
        self._paused = False
        self._pause_time = None

    async def expired(self) -> bool:
        """Asynchronously checks if the timer has expired.

        Waits non-blockingly until the interval has passed, taking pause state into account.
        """
        while True:
            if self._paused:
                await asyncio.sleep(0.1)
                continue

            now = time.time()
            if now >= self.next_time:
                self.next_time = now + self.interval  # Reset next time
                return True
            await asyncio.sleep(0.1)  # Check periodically

    def reset(self) -> None:
        """Resets the timer to start the countdown again from now."""
        self.next_time = time.time() + self.interval
        print("⏱️ Timer reset!")

    def pause(self) -> None:
        """Pauses the timer."""
        if not self._paused:
            self._paused = True
            self._pause_time = time.time()
            print("⏸️ Timer paused.")

    def resume(self) -> None:
        """Resumes the timer and adjusts the next_time accordingly."""
        if self._paused:
            pause_duration = time.time() - self._pause_time
            self.next_time += pause_duration
            self._paused = False
            print("▶️ Timer resumed.")
