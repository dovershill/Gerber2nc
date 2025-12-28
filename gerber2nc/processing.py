"""
Toolpath generation from parsed Gerber data.
"""

import logging

from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.ops import unary_union

from gerber2nc.parsers.gerber import GerberTracesParser

logger = logging.getLogger(__name__)


class ToolpathGenerator:
    """
    Generates milling toolpaths from parsed Gerber data.

    Creates isolation routing paths around copper features to
    separate traces from each other.

    Attributes:
        combined_geometry: Unified Shapely geometry of all copper features
    """

    def __init__(self, traces_parser: GerberTracesParser):
        """
        Initialize toolpath generator from parsed traces.

        Args:
            traces_parser: Parsed Gerber copper layer data
        """
        self.combined_geometry = self._build_geometry(traces_parser)

    def _build_geometry(self, parser: GerberTracesParser):
        """
        Combine traces and pads into unified geometry.

        Args:
            parser: Parsed Gerber data

        Returns:
            Unified Shapely geometry object
        """
        geometries = []

        # Add traces as buffered lines
        for trace in parser.traces:
            start, end, width = trace
            line = LineString([start, end])
            geometries.append(line.buffer(width / 2))

        # Add pads
        for pad in parser.pads:
            pos, aperture = pad
            x, y = pos

            if aperture.type == 'circle':
                logger.debug(f"Circle pad at ({x:.2f}, {y:.2f})")
                geometries.append(Point(x, y).buffer(aperture.diameter / 2))

            elif aperture.type == 'rectangle':
                w, h = aperture.width / 2, aperture.height / 2
                geometries.append(box(x - w, y - h, x + w, y + h))

            else:
                logger.warning(f"Unknown pad type: {aperture.type}, skipping")

        logger.info(f"Built geometry from {len(parser.traces)} traces and {len(parser.pads)} pads")
        return unary_union(geometries)

    def compute_toolpaths(
        self,
        offset_distance: float,
        num_passes: int,
        path_spacing: float
    ) -> MultiLineString:
        """
        Compute isolation milling toolpaths.

        Creates multiple concentric passes around copper features.

        Args:
            offset_distance: Initial offset from copper edge (mm)
            num_passes: Number of milling passes
            path_spacing: Spacing between passes (mm)

        Returns:
            MultiLineString containing all toolpath segments
        """
        logger.info(f"Computing toolpaths: {num_passes} passes, "
                   f"{offset_distance}mm offset, {path_spacing}mm spacing")

        all_passes = []

        for pass_num in range(num_passes):
            offset = offset_distance + path_spacing * pass_num
            path = self.combined_geometry.buffer(offset).simplify(0.03).boundary

            if hasattr(path, 'geoms'):
                all_passes.extend(path.geoms)
            else:
                all_passes.append(path)

        logger.info(f"Generated {len(all_passes)} toolpath segments")
        return MultiLineString(all_passes)
