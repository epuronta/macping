#!/usr/bin/env python3
"""
MacPing - macOS menu bar network latency monitor
"""

import rumps


class MacPingApp(rumps.App):
    def __init__(self):
        super(MacPingApp, self).__init__("MacPing")
        self.title = "▁▂▃▄▅▆▇█"  # Initial placeholder sparkline

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()


def main():
    app = MacPingApp()
    app.run()


if __name__ == "__main__":
    main()
