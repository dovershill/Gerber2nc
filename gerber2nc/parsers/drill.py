"""
Excellon drill file parser.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from gerber2nc.constants import (
    MM_PER_INCH,
    DRILL_FORMAT_INCH,
    DRILL_FORMAT_METRIC,
)
from gerber2nc.models import BoardExtents

logger = logging.getLogger(__name__)


class DrillFileParser:
    """
    Parses Excellon drill files to extract hole positions.

    Supports both KiCad (decimal coordinates) and Fritzing
    (implied decimal format) drill files.

    Attributes:
        holes: List of (x, y, diameter) tuples
        tool_diameters: Dictionary mapping tool numbers to diameters
    """

    def __init__(self, filename: Optional[Path | str], extents: BoardExtents):
        """
        Initialize and parse an Excellon drill file.

        Args:
            filename: Path to the drill file (can be None)
            extents: BoardExtents instance to update with coordinates
        """
        self.tool_diameters: dict[str, float] = {}
        self.holes: list[tuple[float, float, float]] = []
        self.extents = extents

        if filename:
            self._parse_file(Path(filename))

    def _parse_file(self, filepath: Path) -> None:
        """Parse the drill file."""
        logger.info(f"Parsing drill file: {filepath.name}")

        try:
            lines = filepath.read_text(encoding='utf-8').splitlines()
        except FileNotFoundError:
            logger.warning("No drill file found")
            return

        # Detect coordinate format (decimal vs implied)
        has_decimal_coords = self._detect_decimal_format(lines)
        logger.debug(f"Decimal coordinates: {has_decimal_coords}")

        units_mult = 1.0
        coord_scale = 1.0
        current_tool: Optional[str] = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            # Unit detection
            if 'METRIC' in line.upper():
                units_mult = 1.0
                if not has_decimal_coords:
                    coord_scale = DRILL_FORMAT_METRIC
                logger.debug("Units: metric")
            elif 'INCH' in line.upper():
                units_mult = MM_PER_INCH
                if not has_decimal_coords:
                    coord_scale = DRILL_FORMAT_INCH
                logger.debug("Units: inches")

            # Tool definition: T01C0.800
            tool_match = re.match(r'^T(\d+)C([\d.]+)', line)
            if tool_match:
                tool_num = tool_match.group(1)
                diameter = float(tool_match.group(2)) * units_mult
                self.tool_diameters[tool_num] = diameter
                logger.debug(f"Tool T{tool_num}: {diameter:.3f}mm")
                continue

            # Tool change: T01
            change_match = re.match(r'^T(\d+)$', line)
            if change_match:
                current_tool = change_match.group(1)
                continue

            # Drill coordinates
            coord_match = re.match(r'^X(-?[\d.]+)Y(-?[\d.]+)', line)
            if coord_match and current_tool:
                x_str, y_str = coord_match.group(1), coord_match.group(2)

                # Apply scaling based on format
                x = self._parse_coord(x_str, coord_scale, units_mult)
                y = self._parse_coord(y_str, coord_scale, units_mult)

                diameter = self.tool_diameters.get(current_tool, 0.8)
                self.holes.append((x, y, diameter))
                self.extents.update(x, y)

                logger.debug(f"Hole ({x:.1f}, {y:.1f}), diameter: {diameter:.2f}mm")

        logger.info(f"Found {len(self.holes)} holes")

    def _detect_decimal_format(self, lines: list[str]) -> bool:
        """
        Check if coordinates contain decimal points.

        KiCad uses explicit decimals (X1.234Y5.678),
        while Fritzing uses implied format (X012345Y067890).

        Args:
            lines: List of lines from the drill file

        Returns:
            True if coordinates have decimal points
        """
        for line in lines:
            line = line.strip()
            match = re.match(r'^X-?[\d.]+Y-?[\d.]+', line)
            if match and '.' in line.split('Y')[0]:
                return True
        return False

    def _parse_coord(
        self,
        coord_str: str,
        scale: float,
        units_mult: float
    ) -> float:
        """
        Parse a coordinate value with appropriate scaling.

        Args:
            coord_str: Coordinate string (may or may not have decimal)
            scale: Scale factor for implied decimal format
            units_mult: Unit conversion multiplier

        Returns:
            Coordinate value in mm
        """
        if '.' in coord_str:
            return float(coord_str) * units_mult
        else:
            return float(coord_str) / scale * units_mult

    def shift(self, x_offset: float, y_offset: float) -> None:
        """
        Shift all coordinates by given offset.

        Args:
            x_offset: X offset to subtract
            y_offset: Y offset to subtract
        """
        self.holes = [
            (x - x_offset, y - y_offset, d)
            for x, y, d in self.holes
        ]
