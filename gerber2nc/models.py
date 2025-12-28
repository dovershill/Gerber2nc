"""
Data models for gerber2nc.
"""

from dataclasses import dataclass
from gerber2nc.constants import (
    DEFAULT_SPINDLE_SPEED,
    DEFAULT_CUT_DEPTH,
    DEFAULT_EDGE_CUT_DEPTH,
    DEFAULT_SAFE_HEIGHT,
    DEFAULT_PLUNGE_FEED_RATE,
    DEFAULT_FEED_RATE,
    DEFAULT_HOLE_START,
    DEFAULT_HOLE_DEPTH,
    DEFAULT_LARGE_HOLE_THRESHOLD,
)


@dataclass
class BoardExtents:
    """
    Tracks the bounding box of the PCB design.

    Used to normalize coordinates so the board origin is at (0, 0).

    Attributes:
        x_min: Minimum X coordinate seen
        x_max: Maximum X coordinate seen
        y_min: Minimum Y coordinate seen
        y_max: Maximum Y coordinate seen
    """
    x_min: float = 1e9
    x_max: float = -1e9
    y_min: float = 1e9
    y_max: float = -1e9

    def update(self, x: float, y: float, margin: float = 0.0) -> None:
        """
        Expand extents to include point (x, y) with optional margin.

        Args:
            x: X coordinate
            y: Y coordinate
            margin: Extra margin to add around the point
        """
        self.x_min = min(self.x_min, x - margin)
        self.x_max = max(self.x_max, x + margin)
        self.y_min = min(self.y_min, y - margin)
        self.y_max = max(self.y_max, y + margin)

    @property
    def width(self) -> float:
        """Board width in mm."""
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """Board height in mm."""
        return self.y_max - self.y_min

    def is_valid(self) -> bool:
        """Check if any coordinates have been recorded."""
        return self.x_min < 1e8 and self.x_max > -1e8


@dataclass
class Aperture:
    """
    Gerber aperture definition (pad/trace shape).

    Apertures define the shape and size of pads and trace widths
    in Gerber files.

    Attributes:
        type: Shape type ('circle' or 'rectangle')
        diameter: Diameter for circular apertures (mm)
        width: Width for rectangular apertures (mm)
        height: Height for rectangular apertures (mm)
    """
    type: str  # 'circle' or 'rectangle'
    diameter: float = 0.0
    width: float = 0.0
    height: float = 0.0


@dataclass
class MillingParams:
    """
    CNC milling parameters.

    All measurements in mm unless otherwise noted.

    Attributes:
        spindle_speed: Spindle speed in RPM
        cut_depth: Depth for trace isolation cuts (negative value)
        edge_cut_depth: Depth for board outline marking (negative value)
        safe_height: Safe travel height above workpiece
        plunge_feed_rate: Feed rate for plunge moves (mm/min)
        feed_rate: Feed rate for horizontal moves (mm/min)
        hole_start: Approach depth before slow drilling
        hole_depth: Final drill depth (negative, through PCB)
        large_hole_threshold: Diameter above which holes use large drill
    """
    spindle_speed: int = DEFAULT_SPINDLE_SPEED
    cut_depth: float = DEFAULT_CUT_DEPTH
    edge_cut_depth: float = DEFAULT_EDGE_CUT_DEPTH
    safe_height: float = DEFAULT_SAFE_HEIGHT
    plunge_feed_rate: int = DEFAULT_PLUNGE_FEED_RATE
    feed_rate: int = DEFAULT_FEED_RATE
    hole_start: float = DEFAULT_HOLE_START
    hole_depth: float = DEFAULT_HOLE_DEPTH
    large_hole_threshold: float = DEFAULT_LARGE_HOLE_THRESHOLD
