"""
Gerber2nc - Convert Gerber PCB files to G-code for CNC milling.

Supports both KiCad and Fritzing Gerber exports.

Original Author: Matthias Wandel (August 2025)
Fork Author: Enrico Gasparini (December 2025)
    - Added Fritzing support
    - Refactored to Python best practices
"""

__version__ = "2.0.0"
__author__ = "Matthias Wandel, Enrico Gasparini"

from gerber2nc.models import BoardExtents, Aperture, MillingParams
from gerber2nc.parsers import GerberTracesParser, GerberEdgeCutsParser, DrillFileParser
from gerber2nc.processing import ToolpathGenerator
from gerber2nc.gcode import GcodeGenerator
from gerber2nc.visualization import Visualizer
from gerber2nc.file_utils import find_gerber_files

__all__ = [
    "BoardExtents",
    "Aperture",
    "MillingParams",
    "GerberTracesParser",
    "GerberEdgeCutsParser",
    "DrillFileParser",
    "ToolpathGenerator",
    "GcodeGenerator",
    "Visualizer",
    "find_gerber_files",
]
