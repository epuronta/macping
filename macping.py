#!/usr/bin/env python3
"""
MacPing - macOS menu bar network latency monitor
"""

import rumps
import threading
import time
from collections import deque
from ping3 import ping

# Configuration
TARGET_HOST = "google.com"
PING_INTERVAL = 1.0  # seconds
HISTORY_SIZE = 30    # number of pings to display
PING_TIMEOUT = 2.0   # seconds

# Unicode block characters for histogram
BLOCKS = "▁▂▃▄▅▆▇█"


class MacPingApp(rumps.App):
    def __init__(self):
        super(MacPingApp, self).__init__("MacPing")

        # Rolling buffer of ping results (in milliseconds, None for failures)
        # Pre-populate with minimal values to maintain constant width
        self.ping_history = deque([10.0] * HISTORY_SIZE, maxlen=HISTORY_SIZE)

        # Initial display
        self.title = BLOCKS[0] * HISTORY_SIZE

        # Start ping thread
        self.running = True
        self.ping_thread = threading.Thread(target=self._ping_worker, daemon=True)
        self.ping_thread.start()

    def _ping_worker(self):
        """Background thread that performs pings"""
        while self.running:
            try:
                # Perform ping (returns seconds or None on failure)
                result = ping(TARGET_HOST, timeout=PING_TIMEOUT)

                if result is not None:
                    # Convert to milliseconds
                    latency_ms = result * 1000
                    self.ping_history.append(latency_ms)
                else:
                    # Timeout/failure
                    self.ping_history.append(None)

                # Update display
                self._update_display()

            except Exception as e:
                # On error, record as failure
                self.ping_history.append(None)
                self._update_display()

            # Wait for next ping
            time.sleep(PING_INTERVAL)

    def _update_display(self):
        """Update menu bar with current histogram"""
        if not self.ping_history:
            self.title = "Waiting..."
            return

        # Generate histogram
        histogram = self._generate_histogram()
        self.title = histogram

    def _generate_histogram(self):
        """Convert ping history to Unicode block histogram"""
        if not self.ping_history:
            return ""

        # Separate valid pings from failures
        valid_pings = [p for p in self.ping_history if p is not None]

        if not valid_pings:
            # All failures - show all max blocks
            return BLOCKS[-1] * len(self.ping_history)

        # Calculate min/max for scaling
        min_latency = min(valid_pings)
        max_latency = max(valid_pings)
        latency_range = max_latency - min_latency

        # Generate histogram
        histogram = []
        for ping_result in self.ping_history:
            if ping_result is None:
                # Failed ping - use max block
                histogram.append(BLOCKS[-1])
            else:
                # Scale to block index
                if latency_range == 0:
                    # All pings have same latency
                    block_index = 0
                else:
                    normalized = (ping_result - min_latency) / latency_range
                    block_index = int(normalized * (len(BLOCKS) - 1))
                    block_index = min(block_index, len(BLOCKS) - 1)  # Clamp to max

                histogram.append(BLOCKS[block_index])

        return "".join(histogram)

    @rumps.clicked("Quit")
    def quit_app(self, _):
        self.running = False
        rumps.quit_application()


def main():
    app = MacPingApp()
    app.run()


if __name__ == "__main__":
    main()
