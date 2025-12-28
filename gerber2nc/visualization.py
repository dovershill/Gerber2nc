"""
Tkinter-based PCB visualization.
"""

import logging
from typing import Optional

from shapely.geometry import MultiLineString

from gerber2nc.constants import (
    COLOR_BACKGROUND,
    COLOR_PCB,
    COLOR_COPPER,
    COLOR_COPPER_HIGHLIGHT,
    COLOR_EDGE_CUTS,
    COLOR_TOOLPATH,
    COLOR_HOLE_FILL,
    COLOR_HOLE_OUTLINE,
)
from gerber2nc.models import BoardExtents
from gerber2nc.parsers.gerber import GerberTracesParser

logger = logging.getLogger(__name__)


class Visualizer:
    """
    Tkinter-based PCB visualization.

    Displays copper traces, pads, toolpaths, edge cuts, and drill holes
    for visual verification before G-code generation.

    Attributes:
        extents: Board extents for sizing the canvas
        scale: Pixels per mm for display scaling
    """

    def __init__(self, extents: BoardExtents):
        """
        Initialize visualizer with board extents.

        Args:
            extents: Board bounding box for canvas sizing
        """
        self.extents = extents
        self.traces_parser: Optional[GerberTracesParser] = None
        self.toolpaths: Optional[MultiLineString] = None
        self.outline: list[tuple[float, float]] = []
        self.holes: list[tuple[float, float, float]] = []
        self.scale = 25  # pixels per mm

    def load_data(
        self,
        traces: GerberTracesParser,
        toolpaths: MultiLineString,
        outline: list[tuple[float, float]],
        holes: list[tuple[float, float, float]]
    ) -> None:
        """
        Load all data for visualization.

        Args:
            traces: Parsed copper layer data
            toolpaths: Generated milling toolpaths
            outline: Board edge cut coordinates
            holes: List of (x, y, diameter) drill holes
        """
        self.traces_parser = traces
        self.toolpaths = toolpaths
        self.outline = outline
        self.holes = holes

    def show(self, title: str) -> None:
        """
        Display the visualization window.

        Blocks until the window is closed.

        Args:
            title: Window title
        """
        import tkinter as tk

        logger.info("Opening visualization window")

        root = tk.Tk()
        root.title(f"{title}: Tool paths in white, edge cuts in yellow. Close to generate G-code")

        # Calculate canvas size
        max_width = root.winfo_screenwidth() * 0.9
        if self.scale * self.extents.width > max_width:
            self.scale = max_width / self.extents.width

        canvas_width = int(self.extents.width * self.scale)
        canvas_height = int(self.extents.height * self.scale)

        logger.debug(f"Canvas size: {canvas_width}x{canvas_height} pixels")

        bg_color = COLOR_BACKGROUND if self.outline else COLOR_PCB
        canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg=bg_color)
        canvas.pack(padx=5, pady=5)

        self._draw_outline(canvas, canvas_height)
        self._draw_traces(canvas, canvas_height)
        self._draw_pads(canvas, canvas_height)
        self._draw_toolpaths(canvas, canvas_height)
        self._draw_holes(canvas, canvas_height)

        logger.info("Waiting for window to close...")
        root.mainloop()
        logger.info("Visualization closed")

    def _draw_outline(self, canvas, canvas_height: int) -> None:
        """Draw board outline."""
        if not self.outline:
            return

        coords = []
        for x, y in self.outline:
            coords.extend([
                x * self.scale,
                canvas_height - y * self.scale
            ])

        if len(coords) >= 6:
            canvas.create_polygon(
                coords[:-2],
                fill=COLOR_PCB,
                outline=COLOR_EDGE_CUTS,
                width=2
            )

    def _draw_traces(self, canvas, canvas_height: int) -> None:
        """Draw copper traces."""
        import tkinter as tk

        for trace in self.traces_parser.traces:
            start, end, width = trace
            x1 = start[0] * self.scale
            y1 = canvas_height - start[1] * self.scale
            x2 = end[0] * self.scale
            y2 = canvas_height - end[1] * self.scale
            line_width = max(1, int(width * self.scale))

            canvas.create_line(
                x1, y1, x2, y2,
                fill=COLOR_COPPER,
                width=line_width,
                capstyle=tk.ROUND
            )

    def _draw_pads(self, canvas, canvas_height: int) -> None:
        """Draw pads."""
        for pad in self.traces_parser.pads:
            pos, aperture = pad
            x = pos[0] * self.scale
            y = canvas_height - pos[1] * self.scale

            if aperture.type == 'circle':
                r = (aperture.diameter / 2) * self.scale
                canvas.create_oval(
                    x - r, y - r, x + r, y + r,
                    fill=COLOR_COPPER,
                    outline=COLOR_COPPER_HIGHLIGHT
                )
            elif aperture.type == 'rectangle':
                w = aperture.width * self.scale / 2
                h = aperture.height * self.scale / 2
                canvas.create_rectangle(
                    x - w, y - h, x + w, y + h,
                    fill=COLOR_COPPER,
                    outline=COLOR_COPPER_HIGHLIGHT
                )

    def _draw_toolpaths(self, canvas, canvas_height: int) -> None:
        """Draw milling toolpaths."""
        for path in self.toolpaths.geoms:
            coords = []
            for x, y in path.coords:
                coords.extend([
                    x * self.scale,
                    canvas_height - y * self.scale
                ])
            canvas.create_line(coords, fill=COLOR_TOOLPATH, width=2)

    def _draw_holes(self, canvas, canvas_height: int) -> None:
        """Draw drill holes."""
        for x, y, diameter in self.holes:
            sx = x * self.scale
            sy = canvas_height - y * self.scale
            r = (diameter / 2) * self.scale
            canvas.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=COLOR_HOLE_FILL,
                outline=COLOR_HOLE_OUTLINE,
                width=1
            )
