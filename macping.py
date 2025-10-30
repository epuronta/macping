#!/usr/bin/env python3
"""
MacPing - macOS menu bar network latency monitor
"""

import os
import tempfile
import threading
import time
from collections import deque

import rumps
from PIL import Image, ImageDraw
from ping3 import ping

# Ping configuration
TARGET_HOST = "google.com"
PING_INTERVAL = 1.0  # seconds
PING_TIMEOUT = 2.0  # seconds

# Display configuration
HISTORY_SIZE = 60  # number of pings to display
INITIAL_LATENCY = 10.0  # baseline value (ms) for pre-populating history

# Rendering configuration
# Note: macOS may scale very wide icons to fit menu bar constraints.
# Current total width: 180 pixels (60 pings × 3 pixels/bar)
BAR_WIDTH = 3  # pixels per bar
BAR_HEIGHT = 18  # maximum bar height in pixels
BAR_COLOR = (255, 255, 255)  # RGB: white bars for normal latency
BAR_COLOR_WARNING = (255, 0, 0)  # RGB: red bars for high latency/failures

# Latency scaling range
# Latencies are scaled from 0-100ms for consistent visualization
# Anything above 100ms is shown as a warning (red bar at full height)
LATENCY_MIN = 0.0  # minimum latency for scaling (ms)
LATENCY_MAX = 100.0  # maximum latency for scaling (ms)


class MacPingApp(rumps.App):
    """
    macOS menu bar application that continuously monitors network latency.

    Displays a real-time pixel-based histogram showing the last 60 ping results.
    Normal latency (0-100ms) shown as white bars, high latency/failures as red bars.
    """

    def __init__(self):
        super().__init__("MacPing", icon=None, title="")

        # Disable template mode so colors render correctly (not inverted in dark mode)
        self._template = False

        # Create temporary file for icon
        self.temp_icon_fd, self.temp_icon_path = tempfile.mkstemp(suffix=".png")

        # Rolling buffer of ping results (in milliseconds, None for failures)
        # Pre-populate with baseline latency to maintain constant icon width
        self.ping_history = deque([INITIAL_LATENCY] * HISTORY_SIZE, maxlen=HISTORY_SIZE)

        # Initial display
        self._update_display()

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

            except Exception:
                # On error, record as failure
                self.ping_history.append(None)
                self._update_display()

            # Wait for next ping
            time.sleep(PING_INTERVAL)

    def _update_display(self):
        """Update menu bar with current histogram"""
        if not self.ping_history:
            return

        # Generate histogram image
        pil_image = self._generate_histogram_image()

        # Save to temporary file
        pil_image.save(self.temp_icon_path, format="PNG")

        # Update icon
        self.icon = self.temp_icon_path

    def _generate_histogram_image(self):
        """Generate histogram image from ping history."""
        image_width = HISTORY_SIZE * BAR_WIDTH
        image_height = BAR_HEIGHT

        # Create image with transparent background
        image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Use fixed latency range for consistent scaling across all updates
        latency_range = LATENCY_MAX - LATENCY_MIN

        # Draw each ping result as a vertical bar
        for i, ping_result in enumerate(self.ping_history):
            x_position = i * BAR_WIDTH

            if ping_result is None:
                # Failed ping - full height red bar
                bar_pixels = image_height
                color = BAR_COLOR_WARNING
            elif ping_result > LATENCY_MAX:
                # High latency warning - full height red bar
                bar_pixels = image_height
                color = BAR_COLOR_WARNING
            else:
                # Normal ping - scale latency to bar height in pixels
                normalized = (ping_result - LATENCY_MIN) / latency_range
                normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1
                bar_pixels = max(1, int(normalized * image_height))
                color = BAR_COLOR

            # Draw bar from bottom up
            y_top = image_height - bar_pixels
            draw.rectangle(
                [x_position, y_top, x_position + BAR_WIDTH - 1, image_height - 1], fill=color
            )

        return image

    @rumps.clicked("Quit")
    def quit_app(self, _):
        self.running = False
        # Clean up temporary icon file
        try:
            os.close(self.temp_icon_fd)
            os.unlink(self.temp_icon_path)
        except (OSError, AttributeError):
            # File may already be closed/deleted, or not yet created
            pass
        rumps.quit_application()


def main():
    app = MacPingApp()
    app.run()


if __name__ == "__main__":
    main()
