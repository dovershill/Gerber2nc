"""
Constants used throughout the gerber2nc package.
"""

# =============================================================================
# Coordinate Scaling
# =============================================================================

# Gerber coordinate scaling (both KiCad and Fritzing use 6 decimal places)
GERBER_SCALE: float = 1e-6  # 1,000,000 units per base unit

# Unit conversions
MM_PER_INCH: float = 25.4

# Drill file coordinate formats (when no decimal point present)
DRILL_FORMAT_INCH: float = 10000.0   # 2.4 format: divide by 10000
DRILL_FORMAT_METRIC: float = 1000.0  # 3.3 format: divide by 1000


# =============================================================================
# Visualization Colors (KiCad style)
# =============================================================================

COLOR_BACKGROUND: str = '#202020'
COLOR_PCB: str = '#005000'
COLOR_COPPER: str = '#C83434'
COLOR_COPPER_HIGHLIGHT: str = '#E85050'
COLOR_EDGE_CUTS: str = '#F0E14A'
COLOR_TOOLPATH: str = 'white'
COLOR_HOLE_FILL: str = 'black'
COLOR_HOLE_OUTLINE: str = 'white'


# =============================================================================
# Extent Margins (mm)
# =============================================================================

MARGIN_PAD: float = 1.5
MARGIN_TRACE: float = 0.6
MARGIN_EDGE: float = 0.2


# =============================================================================
# Default Milling Parameters
# =============================================================================

DEFAULT_SPINDLE_SPEED: int = 12000      # RPM
DEFAULT_CUT_DEPTH: float = -0.1         # mm (trace isolation)
DEFAULT_EDGE_CUT_DEPTH: float = -0.2    # mm (board outline)
DEFAULT_SAFE_HEIGHT: float = 3.0        # mm above workpiece
DEFAULT_PLUNGE_FEED_RATE: int = 200     # mm/min
DEFAULT_FEED_RATE: int = 450            # mm/min
DEFAULT_HOLE_START: float = 0.1         # mm (approach depth)
DEFAULT_HOLE_DEPTH: float = -1.8        # mm (through PCB)
DEFAULT_LARGE_HOLE_THRESHOLD: float = 0.85  # mm diameter


# =============================================================================
# Default Toolpath Parameters
# =============================================================================

DEFAULT_OFFSET_DISTANCE: float = 0.22   # mm from copper edge
DEFAULT_NUM_PASSES: int = 3
DEFAULT_PATH_SPACING: float = 0.2       # mm between passes
