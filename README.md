# MacPing

A lightweight macOS menu bar app that monitors network latency with real-time sparkline visualization.

## What it does

MacPing continuously pings google.com and displays the last 30 ping results as a sparkline histogram in your menu bar using Unicode block characters (▁▂▃▄▅▆▇█). Taller bars = higher latency. Updates in real-time.

## Installation

```bash
uv sync
uv run macping.py
```

## Requirements

- macOS 10.14+
- Python 3.8+

## Dependencies

- `rumps` - macOS menu bar framework
- `ping3` or `pythonping` - ICMP ping library

## How it works

- Pings google.com every 1 second
- Maintains rolling buffer of last 30 results
- Maps latency to Unicode blocks (▁▂▃▄▅▆▇█)
- Updates menu bar in real-time
- Failed pings shown as █

## Configuration

Hardcoded defaults in `macping.py`:
- Target: `google.com`
- Interval: `1 second`
- History: `30 pings`

## Tech Stack

- Python with `rumps` for menu bar integration
- Background thread for non-blocking ping operations
- Dynamic scaling for histogram rendering

## License

MIT
