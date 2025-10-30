"""
Native macOS window components for MacPing detail view.
"""

from AppKit import (
    NSApplication,
    NSPanel,
    NSView,
    NSColor,
    NSBezierPath,
    NSFont,
    NSMakeRect,
    NSWindowStyleMaskBorderless,
    NSVisualEffectView,
    NSEvent,
    NSScreen,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
)
from Foundation import NSObject, NSAttributedString, NSDictionary
from objc import super as objc_super, python_method

# Configuration
# ============

# Window dimensions
WINDOW_WIDTH = 560
WINDOW_HEIGHT = 350

# Graph margins
MARGIN_LEFT = 60
MARGIN_RIGHT = 20
MARGIN_TOP = 20
MARGIN_BOTTOM = 30

# Graph appearance
LINE_WIDTH = 2
POINT_RADIUS = 2
AXES_LINE_WIDTH = 1
GRID_LINE_WIDTH = 0.5

# Opacity levels
AXES_OPACITY = 0.5
GRID_OPACITY = 0.2
LABEL_OPACITY = 0.6
GRAPH_OPACITY = 0.6


class WindowDelegate(NSObject):
    """Delegate to handle window events"""

    def initWithManager_(self, manager):
        """Initialize with reference to the window manager"""
        self = objc_super(WindowDelegate, self).init()
        if self is None:
            return None
        self.manager = manager
        return self

    @python_method
    def windowWillClose_(self, notification):
        """Called when window is about to close"""
        self.manager.on_window_close()


class LatencyGraphView(NSView):
    """
    Custom NSView that renders a detailed latency graph using Core Graphics.
    """

    def initWithManager_(self, manager):
        """Initialize with reference to the window manager"""
        self = objc_super(LatencyGraphView, self).init()
        if self is None:
            return None
        self.manager = manager
        self.latency_min = manager.latency_min
        self.latency_max = manager.latency_max
        return self

    def drawRect_(self, rect):
        """Render the graph using Core Graphics"""
        # Get live ping history from the manager
        ping_history = list(self.manager.ping_history) if hasattr(self, 'manager') else []
        if not ping_history:
            return

        # Get view dimensions
        bounds = self.bounds()
        width = bounds.size.width
        height = bounds.size.height

        # Calculate graph area
        graph_width = width - MARGIN_LEFT - MARGIN_RIGHT
        graph_height = height - MARGIN_TOP - MARGIN_BOTTOM

        # Draw axes (adapts to system dark/light mode)
        self._draw_axes(width, height, graph_width, graph_height)

        # Draw grid and Y-axis labels
        self._draw_grid_and_labels(width, graph_width, graph_height)

        # Draw latency data
        self._draw_latency_graph(ping_history, graph_width, graph_height)

    def _draw_axes(self, width, height, graph_width, graph_height):
        """Draw X and Y axes"""
        axes_color = NSColor.labelColor().colorWithAlphaComponent_(AXES_OPACITY)
        axes_color.setStroke()

        axes_path = NSBezierPath.bezierPath()
        axes_path.moveToPoint_((MARGIN_LEFT, MARGIN_BOTTOM))
        axes_path.lineToPoint_((MARGIN_LEFT, height - MARGIN_TOP))  # Y-axis
        axes_path.moveToPoint_((MARGIN_LEFT, MARGIN_BOTTOM))
        axes_path.lineToPoint_((width - MARGIN_RIGHT, MARGIN_BOTTOM))  # X-axis
        axes_path.setLineWidth_(AXES_LINE_WIDTH)
        axes_path.stroke()

    def _draw_grid_and_labels(self, width, graph_width, graph_height):
        """Draw grid lines and Y-axis labels"""
        grid_color = NSColor.labelColor().colorWithAlphaComponent_(GRID_OPACITY)
        grid_color.setStroke()
        grid_path = NSBezierPath.bezierPath()
        grid_path.setLineWidth_(GRID_LINE_WIDTH)

        label_color = NSColor.labelColor().colorWithAlphaComponent_(LABEL_OPACITY)
        label_attrs = NSDictionary.dictionaryWithObjects_forKeys_(
            [NSFont.systemFontOfSize_(10), label_color],
            [NSFontAttributeName, NSForegroundColorAttributeName]
        )

        for i in range(5):
            y_value = (self.latency_max / 4) * i
            y_pos = MARGIN_BOTTOM + (graph_height / 4) * i

            # Grid line
            grid_path.moveToPoint_((MARGIN_LEFT, y_pos))
            grid_path.lineToPoint_((width - MARGIN_RIGHT, y_pos))

            # Label
            label_text = f"{y_value:.0f}ms"
            label_str = NSAttributedString.alloc().initWithString_attributes_(label_text, label_attrs)
            label_str.drawAtPoint_((5, y_pos - 6))

        grid_path.stroke()

    def _draw_latency_graph(self, ping_history, graph_width, graph_height):
        """Draw the latency line graph with data points"""

        if len(ping_history) < 2:
            return

        x_step = graph_width / (len(ping_history) - 1)

        # Draw connecting line
        line_path = NSBezierPath.bezierPath()
        line_path.setLineWidth_(LINE_WIDTH)

        started = False
        for i, latency in enumerate(ping_history):
            if latency is not None:
                x = MARGIN_LEFT + i * x_step
                y = self._calculate_y_position(latency, graph_height)

                if not started:
                    line_path.moveToPoint_((x, y))
                    started = True
                else:
                    line_path.lineToPoint_((x, y))

        NSColor.controlAccentColor().colorWithAlphaComponent_(GRAPH_OPACITY).setStroke()
        line_path.stroke()

        # Draw data points and failure markers
        for i, latency in enumerate(ping_history):
            x = MARGIN_LEFT + i * x_step

            if latency is None:
                self._draw_failure_marker(x)
            else:
                y = self._calculate_y_position(latency, graph_height)
                self._draw_data_point(x, y, latency)

    def _calculate_y_position(self, latency, graph_height):
        """Calculate Y position for a latency value"""
        clamped_latency = min(latency, self.latency_max)
        y_ratio = clamped_latency / self.latency_max
        return MARGIN_BOTTOM + y_ratio * graph_height

    def _draw_failure_marker(self, x):
        """Draw red X mark for failed pings"""
        NSColor.systemRedColor().colorWithAlphaComponent_(GRAPH_OPACITY).set()
        x_mark = NSBezierPath.bezierPath()
        x_mark.moveToPoint_((x - 3, MARGIN_BOTTOM - 3))
        x_mark.lineToPoint_((x + 3, MARGIN_BOTTOM + 3))
        x_mark.moveToPoint_((x - 3, MARGIN_BOTTOM + 3))
        x_mark.lineToPoint_((x + 3, MARGIN_BOTTOM - 3))
        x_mark.setLineWidth_(LINE_WIDTH)
        x_mark.stroke()

    def _draw_data_point(self, x, y, latency):
        """Draw a data point (colored by latency threshold)"""
        if latency > self.latency_max:
            color = NSColor.systemRedColor()
        else:
            color = NSColor.controlAccentColor()

        color.colorWithAlphaComponent_(GRAPH_OPACITY).setFill()

        point_path = NSBezierPath.bezierPath()
        point_rect = NSMakeRect(x - POINT_RADIUS, y - POINT_RADIUS,
                               POINT_RADIUS * 2, POINT_RADIUS * 2)
        point_path.appendBezierPathWithOvalInRect_(point_rect)
        point_path.fill()


class WindowManager:
    """Manages the detail window state and lifecycle"""

    def __init__(self, ping_history, latency_min, latency_max):
        """
        Initialize window manager.

        Args:
            ping_history: Reference to the app's ping history deque
            latency_min: Minimum latency for scaling (ms)
            latency_max: Maximum latency for scaling (ms)
        """
        self.ping_history = ping_history
        self.latency_min = latency_min
        self.latency_max = latency_max

        self.window = None
        self.graph_view = None
        self.update_timer = None
        self.delegate = WindowDelegate.alloc().initWithManager_(self)

    def show_details(self):
        """Show the detail window (create if needed, or bring to front if exists)"""
        # If window already exists and is visible, just bring it to front
        if self.window is not None and self.window.isVisible():
            self.window.makeKeyAndOrderFront_(None)
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            return

        # Create new window
        self._create_window()
        self._start_update_timer()

    def on_window_close(self):
        """Called when the window is closed"""
        self._stop_update_timer()
        self.window = None
        self.graph_view = None

    def cleanup(self):
        """Clean up resources"""
        self._stop_update_timer()

    def _create_window(self):
        """Create and configure the detail window"""
        # Calculate window position (centered under menu bar icon)
        window_rect = _calculate_window_position()

        # Create borderless panel (like native menu bar dropdowns)
        self.window = _create_panel(window_rect)
        self.window.setDelegate_(self.delegate)

        # Create translucent background
        visual_effect_view = _create_visual_effect_view()

        # Create graph view with live data
        self.graph_view = LatencyGraphView.alloc().initWithManager_(self)
        self.graph_view.setFrame_(NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        # Assemble window hierarchy
        visual_effect_view.addSubview_(self.graph_view)
        self.window.setContentView_(visual_effect_view)

        # Show window
        self.graph_view.setNeedsDisplay_(True)
        self.window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    def _start_update_timer(self):
        """Start timer to refresh the graph every second"""
        if self.update_timer is not None:
            self.update_timer.invalidate()

        from Foundation import NSTimer
        self.update_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0,  # Update every second
            self,
            "updateGraph:",
            None,
            True
        )

    def _stop_update_timer(self):
        """Stop the update timer"""
        if self.update_timer is not None:
            self.update_timer.invalidate()
            self.update_timer = None

    @python_method
    def updateGraph_(self, _timer):
        """Timer callback to update the graph (called every second)"""
        if self.graph_view is None or self.window is None:
            return

        if self.window.isVisible():
            # Window is visible, refresh the graph
            self.graph_view.setNeedsDisplay_(True)
        else:
            # Window closed, stop the timer
            self._stop_update_timer()


def _calculate_window_position():
    """Calculate optimal window position below menu bar icon"""
    mouse_location = NSEvent.mouseLocation()
    screen_frame = NSScreen.mainScreen().visibleFrame()

    # Center horizontally under cursor
    x_position = mouse_location.x - (WINDOW_WIDTH / 2)

    # Position just below menu bar
    y_position = screen_frame.origin.y + screen_frame.size.height - WINDOW_HEIGHT - 5

    # Keep window on screen
    x_position = max(screen_frame.origin.x + 10, x_position)
    x_position = min(screen_frame.origin.x + screen_frame.size.width - WINDOW_WIDTH - 10,
                    x_position)

    return NSMakeRect(x_position, y_position, WINDOW_WIDTH, WINDOW_HEIGHT)


def _create_panel(window_rect):
    """Create and configure the borderless panel"""
    window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        window_rect, NSWindowStyleMaskBorderless, 2, False  # 2 = NSBackingStoreBuffered
    )

    window.setOpaque_(False)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setLevel_(25)  # Popup menu level - floats above other windows
    window.setHidesOnDeactivate_(True)  # Auto-close when clicking outside
    window.setFloatingPanel_(True)
    window.setBecomesKeyOnlyIfNeeded_(True)
    window.setReleasedWhenClosed_(False)  # Prevent crashes on reopen

    return window


def _create_visual_effect_view():
    """Create translucent background view with rounded corners"""
    view = NSVisualEffectView.alloc().initWithFrame_(
        NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    )

    # Popover material - adapts to system dark/light mode
    view.setMaterial_(5)  # NSVisualEffectMaterialPopover
    view.setBlendingMode_(0)  # NSVisualEffectBlendingModeBehindWindow
    view.setState_(1)  # NSVisualEffectStateActive

    # Add rounded corners
    view.setWantsLayer_(True)
    if view.layer():
        view.layer().setCornerRadius_(10.0)
        view.layer().setMasksToBounds_(True)

    return view
