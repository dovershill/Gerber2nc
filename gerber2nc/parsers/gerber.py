"""
Gerber file parsers for copper layers and edge cuts.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from gerber2nc.constants import (
    GERBER_SCALE,
    MM_PER_INCH,
    MARGIN_PAD,
    MARGIN_TRACE,
    MARGIN_EDGE,
)
from gerber2nc.models import BoardExtents, Aperture

logger = logging.getLogger(__name__)


class GerberTracesParser:
    """
    Parses Gerber copper layer files to extract traces and pads.

    Supports both KiCad (mm) and Fritzing (inch) coordinate formats.

    Attributes:
        traces: List of traces as [[start, end, width], ...]
        pads: List of pads as [[[x, y], aperture], ...]
        apertures: Dictionary of aperture definitions
    """

    def __init__(self, filename: Path | str, extents: BoardExtents):
        """
        Initialize and parse a Gerber copper layer file.

        Args:
            filename: Path to the Gerber file
            extents: BoardExtents instance to update with coordinates
        """
        self.apertures: dict[int, Aperture] = {}
        self.current_aperture: int = -1
        self.traces: list[list] = []
        self.pads: list[list] = []
        self.unit_mult: float = 1.0
        self.current_x: float = 0.0
        self.current_y: float = 0.0
        self.extents = extents

        self._parse_file(Path(filename))

    def _parse_file(self, filepath: Path) -> None:
        """Parse the Gerber file."""
        logger.info(f"Parsing copper layer: {filepath.name}")

        content = filepath.read_text(encoding='utf-8')

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('%'):
                self._process_extended_command(line)
            else:
                self._process_command(line)

        logger.info(f"Found {len(self.traces)} traces and {len(self.pads)} pads")

    def _process_extended_command(self, line: str) -> None:
        """Process extended Gerber commands (starting with %)."""
        # Unit mode
        if 'MOMM*%' in line:
            self.unit_mult = 1.0
            logger.debug("Units: millimeters")
        elif 'MOIN*%' in line:
            self.unit_mult = MM_PER_INCH
            logger.debug("Units: inches")

        # Aperture definitions
        aperture_match = re.match(r'%ADD(\d+)([^,]+),([^*]+)\*%', line)
        if aperture_match:
            num = int(aperture_match.group(1))
            ap_type = aperture_match.group(2)
            params = aperture_match.group(3).split('X')

            if ap_type == 'C':  # Circle
                self.apertures[num] = Aperture(
                    type='circle',
                    diameter=float(params[0])
                )
            elif ap_type == 'R':  # Rectangle
                width = float(params[0])
                height = float(params[1]) if len(params) > 1 else width
                self.apertures[num] = Aperture(
                    type='rectangle',
                    width=width,
                    height=height
                )
            elif ap_type == 'RoundRect':  # Rounded rectangle
                corner_radius = float(params[0])
                x1, y1 = float(params[1]), float(params[2])
                x2, y2 = float(params[3]), float(params[4])
                self.apertures[num] = Aperture(
                    type='rectangle',
                    width=abs(x2) + abs(x1) + corner_radius,
                    height=abs(y2) + abs(y1) + corner_radius
                )

            logger.debug(f"Aperture D{num}: {self.apertures[num]}")

    def _process_command(self, line: str) -> None:
        """Process regular Gerber commands."""
        line = line.rstrip('*')

        # Aperture selection (D10+ are user-defined)
        ap_match = re.match(r'D(\d+)', line)
        if ap_match:
            num = int(ap_match.group(1))
            if num >= 10:
                self.current_aperture = num
            return

        # Coordinate commands
        coord_match = re.match(r'X(-?[0-9.]+)Y(-?[0-9.]+)D0([0123])?', line)
        if coord_match:
            x = float(coord_match.group(1)) * GERBER_SCALE * self.unit_mult
            y = float(coord_match.group(2)) * GERBER_SCALE * self.unit_mult
            operation = int(coord_match.group(3))

            # Update extents with appropriate margin
            margin = MARGIN_PAD if operation == 3 else MARGIN_TRACE
            self.extents.update(x, y, margin)

            if operation == 1:  # Draw line
                if self.current_aperture in self.apertures:
                    ap = self.apertures[self.current_aperture]
                    width = ap.diameter if ap.diameter else ap.width
                    self.traces.append([
                        [self.current_x, self.current_y],
                        [x, y],
                        width
                    ])

            elif operation == 3:  # Flash pad
                if self.current_aperture in self.apertures:
                    self.pads.append([
                        [x, y],
                        self.apertures[self.current_aperture]
                    ])

            self.current_x, self.current_y = x, y

    def shift(self, x_offset: float, y_offset: float) -> None:
        """
        Shift all coordinates by given offset.

        Args:
            x_offset: X offset to subtract
            y_offset: Y offset to subtract
        """
        for trace in self.traces:
            trace[0][0] -= x_offset
            trace[0][1] -= y_offset
            trace[1][0] -= x_offset
            trace[1][1] -= y_offset

        for pad in self.pads:
            pad[0][0] -= x_offset
            pad[0][1] -= y_offset


class GerberEdgeCutsParser:
    """
    Parses Gerber edge cuts file to extract board outline.

    Attributes:
        outline: List of (x, y) tuples defining the board boundary
    """

    def __init__(self, filename: Optional[Path | str], extents: BoardExtents):
        """
        Initialize and parse a Gerber edge cuts file.

        Args:
            filename: Path to the edge cuts file (can be None)
            extents: BoardExtents instance to update with coordinates
        """
        self.outline: list[tuple[float, float]] = []
        self.unit_mult: float = 1.0
        self.extents = extents

        if filename:
            self._parse_file(Path(filename))

    def _parse_file(self, filepath: Path) -> None:
        """Parse the edge cuts file."""
        logger.info(f"Parsing edge cuts: {filepath.name}")

        try:
            lines = filepath.read_text(encoding='utf-8').splitlines()
        except FileNotFoundError:
            logger.warning("No edge cuts file found")
            return

        for line in lines:
            line = line.strip()

            # Unit mode
            if 'MOMM*%' in line:
                self.unit_mult = 1.0
            elif 'MOIN*%' in line:
                self.unit_mult = MM_PER_INCH

            # Coordinates
            coord_match = re.match(r'X(-?[0-9.]+)Y(-?[0-9.]+)D0([0123])?', line)
            if coord_match:
                x = float(coord_match.group(1)) * GERBER_SCALE * self.unit_mult
                y = float(coord_match.group(2)) * GERBER_SCALE * self.unit_mult
                operation = coord_match.group(3)

                self.extents.update(x, y, MARGIN_EDGE)

                if self.outline and operation != '1':
                    logger.warning("Outline should be drawn as one continuous path")

                self.outline.append((x, y))

        if self.outline:
            if self.outline[0] != self.outline[-1]:
                logger.warning("Outline is not closed")
            logger.info(f"Found outline with {len(self.outline)} points")
        else:
            logger.info("No outline coordinates found")

    def shift(self, x_offset: float, y_offset: float) -> None:
        """
        Shift all coordinates by given offset.

        Args:
            x_offset: X offset to subtract
            y_offset: Y offset to subtract
        """
        self.outline = [
            (x - x_offset, y - y_offset)
            for x, y in self.outline
        ]
