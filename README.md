# MacPing

A lightweight macOS menu bar app that monitors network latency with real-time sparkline visualization.

## What it does

MacPing continuously pings google.com and displays the last 60 ping results as a pixel-based histogram in your menu bar. Taller bars = higher latency. Updates in real-time. Bars above 100ms shown in red.

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
- `ping3` - ICMP ping library
- `pillow` - Image generation for histogram rendering

## How it works

- Pings google.com every 1 second
- Maintains rolling buffer of last 60 results
- Generates pixel-based histogram (configurable bar width and height)
- Scales latency from 0-100ms (hardcoded min/max)
- Updates menu bar in real-time
- Failed pings or latency >100ms shown as red bars

## License

MIT
