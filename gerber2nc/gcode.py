"""
G-code generation for CNC milling.
"""

import logging
from pathlib import Path
from typing import Optional

from shapely.geometry import MultiLineString

from gerber2nc.models import MillingParams

logger = logging.getLogger(__name__)


class GcodeGenerator:
    """
    Generates G-code for CNC PCB milling.

    Produces G-code for:
    - Trace isolation milling
    - Board edge marking
    - Hole drilling (small and large holes separately)

    Attributes:
        params: Milling parameters (speeds, depths, etc.)
    """

    def __init__(self, params: Optional[MillingParams] = None):
        """
        Initialize G-code generator.

        Args:
            params: Milling parameters (uses defaults if not provided)
        """
        self.params = params or MillingParams()

    def generate(
        self,
        filename: str | Path,
        toolpaths: MultiLineString,
        outline: list[tuple[float, float]],
        holes: list[tuple[float, float, float]],
        board_height: float
    ) -> Path:
        """
        Generate G-code file.

        Args:
            filename: Output file path
            toolpaths: Milling toolpaths for trace isolation
            outline: Board edge cut coordinates
            holes: List of (x, y, diameter) drill holes
            board_height: Board height for return position

        Returns:
            Path to generated file
        """
        filepath = Path(filename)
        p = self.params

        logger.info(f"Generating G-code: {filepath}")

        with filepath.open('w') as f:
            self._write_header(f, p)
            self._write_trace_milling(f, p, toolpaths)
            self._write_edge_cuts(f, p, outline)
            self._write_drilling(f, p, holes)
            self._write_footer(f, board_height)

        logger.info(f"G-code generated: {filepath}")
        return filepath

    def _write_header(self, f, p: MillingParams) -> None:
        """Write G-code header."""
        f.write("%\n")
        f.write("G21  ; Set units to mm\n")
        f.write("G90  ; Absolute positioning\n")
        f.write(f"G0 Z{p.safe_height}  ; Move to safe height\n")
        f.write("(Load 0.2mm engraving tool)\n")
        f.write("T1 M06\n")
        f.write(f"S{p.spindle_speed} M3  ; Start spindle clockwise\n")

    def _write_trace_milling(
        self,
        f,
        p: MillingParams,
        toolpaths: MultiLineString
    ) -> None:
        """Write trace isolation milling commands."""
        path_count = len(list(toolpaths.geoms))
        logger.debug(f"Writing {path_count} toolpath segments")

        for path in toolpaths.geoms:
            started = False
            for x, y in path.coords:
                if not started:
                    f.write(f"G0 X{x:.2f} Y{y:.2f}\n")
                    f.write("G0 Z0.1\n")
                    f.write(f"G1 Z{p.cut_depth:.3f} F{p.plunge_feed_rate}\n")
                    f.write(f"G1 F{p.feed_rate}\n")
                    started = True
                else:
                    f.write(f"G1 X{x:.2f} Y{y:.2f}\n")
            f.write(f"G0 Z{p.safe_height}\n")

    def _write_edge_cuts(
        self,
        f,
        p: MillingParams,
        outline: list[tuple[float, float]]
    ) -> None:
        """Write edge cut marking commands."""
        if not outline:
            logger.debug("No edge cuts to write")
            return

        logger.debug(f"Writing edge cuts with {len(outline)} points")
        f.write("(Mill edge cut mark)\n")

        started = False
        for x, y in outline:
            if not started:
                f.write(f"G0 X{x:.2f} Y{y:.2f}\n")
                f.write("G0 Z0.1\n")
                f.write(f"G1 Z{p.edge_cut_depth:.3f} F{p.plunge_feed_rate}\n")
                f.write(f"G1 F{p.feed_rate}\n")
                started = True
            else:
                f.write(f"G1 X{x:.2f} Y{y:.2f}\n")

        f.write(f"G0 Z{p.safe_height}\n")
        f.write("M5  ; Stop spindle\n")

    def _write_drilling(
        self,
        f,
        p: MillingParams,
        holes: list[tuple[float, float, float]]
    ) -> None:
        """Write drilling commands (small holes first, then large)."""
        if not holes:
            logger.debug("No holes to drill")
            return

        small_holes = [h for h in holes if h[2] <= p.large_hole_threshold]
        large_holes = [h for h in holes if h[2] > p.large_hole_threshold]

        logger.debug(f"Drilling {len(small_holes)} small holes, {len(large_holes)} large holes")

        # Small holes
        if small_holes:
            f.write("(Load small drill)\n")
            f.write("T2 M06\n")
            f.write(f"S{p.spindle_speed} M3  ; Start spindle\n")

            for x, y, _ in small_holes:
                f.write(f"G0 X{x:.2f} Y{y:.2f}\n")
                f.write(f"G0 Z{p.hole_start:.2f}\n")
                f.write(f"G1 Z{p.hole_depth:.2f} F{p.plunge_feed_rate}\n")
                f.write(f"G0 Z{p.safe_height}\n")

        # Large holes
        if large_holes:
            f.write("(Load large drill)\n")
            f.write("T3 M06\n")
            f.write(f"S{p.spindle_speed} M3  ; Start spindle\n")

            for x, y, _ in large_holes:
                f.write(f"G0 X{x:.2f} Y{y:.2f}\n")
                f.write(f"G0 Z{p.hole_start:.2f}\n")
                f.write(f"G1 Z{p.hole_depth:.2f} F{p.plunge_feed_rate}\n")
                f.write(f"G0 Z{p.safe_height}\n")

    def _write_footer(self, f, board_height: float) -> None:
        """Write G-code footer."""
        f.write("M5  ; Stop spindle\n")
        f.write(f"G0 X0 Y{board_height:.1f} Z50  ; Return home\n")
        f.write("M30  ; End of program\n")
        f.write("%\n")
