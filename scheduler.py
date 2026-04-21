"""
Scheduler module for Job Automation Dashboard.

Provides a reusable, AI-free scheduling mechanism.
Runs automation at a user-defined daily time using a background thread.
"""

import threading
from datetime import datetime, timedelta
import time


class AutomationScheduler:
    """
    Lightweight daily scheduler that fires a callback at a configured HH:MM time.

    Usage (no AI required):
        scheduler = AutomationScheduler(callback=run_automation)
        scheduler.set_time("09:00")
        scheduler.enable()
        ...
        scheduler.disable()
    """

    def __init__(self, callback):
        """
        Args:
            callback: Zero-argument callable invoked when the scheduled time arrives.
        """
        self._callback = callback
        self._enabled = False
        self._run_time = "09:00"   # Default: 09:00 daily
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_time(self, hhmm: str) -> None:
        """Set the daily run time, e.g. '09:30'.  Restarts loop if active."""
        self._run_time = hhmm
        if self._enabled:
            self._restart()

    def get_time(self) -> str:
        """Return the configured daily run time string (HH:MM)."""
        return self._run_time

    def enable(self) -> None:
        """Start the background scheduling loop."""
        with self._lock:
            if self._enabled:
                return
            self._enabled = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def disable(self) -> None:
        """Stop the background scheduling loop and wait for the thread to exit."""
        with self._lock:
            if not self._enabled:
                return
            self._enabled = False
            self._stop_event.set()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5)

    def is_enabled(self) -> bool:
        return self._enabled

    def next_run_str(self) -> str:
        """Return a human-readable description of when the next run will occur."""
        if not self._enabled:
            return "Scheduler disabled"
        next_dt = self._next_run_datetime(datetime.now())
        return next_dt.strftime("%Y-%m-%d %H:%M")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_run_datetime(self, now: datetime) -> datetime:
        try:
            hour, minute = [int(x) for x in self._run_time.split(":")]
        except (ValueError, AttributeError):
            hour, minute = 9, 0
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    def _loop(self) -> None:
        """Background thread: sleep until next scheduled time, then fire."""
        while not self._stop_event.is_set():
            now = datetime.now()
            next_run = self._next_run_datetime(now)
            delay = (next_run - now).total_seconds()
            # Sleep in small chunks so we can respond to stop/reschedule quickly.
            while delay > 0 and not self._stop_event.is_set():
                chunk = min(delay, 30)
                time.sleep(chunk)
                delay -= chunk
            if self._stop_event.is_set():
                break
            self._callback()
            # Small pause to avoid double-firing at boundary.
            time.sleep(61)

    def _restart(self) -> None:
        """Disable (joining the old thread) then re-enable with a fresh thread."""
        self.disable()
        with self._lock:
            self._enabled = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
