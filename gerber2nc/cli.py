"""
Command-line interface for gerber2nc.
"""

import argparse
import logging
import sys
from pathlib import Path

from gerber2nc import __version__
from gerber2nc.constants import (
    DEFAULT_OFFSET_DISTANCE,
    DEFAULT_NUM_PASSES,
    DEFAULT_PATH_SPACING,
)
from gerber2nc.file_utils import find_gerber_files
from gerber2nc.gcode import GcodeGenerator
from gerber2nc.models import BoardExtents, MillingParams
from gerber2nc.parsers import GerberTracesParser, GerberEdgeCutsParser, DrillFileParser
from gerber2nc.processing import ToolpathGenerator
from gerber2nc.visualization import Visualizer


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Configure logging based on verbosity settings.

    Args:
        verbose: Enable debug output
        quiet: Suppress all but error messages
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='gerber2nc',
        description='Convert Gerber PCB files to G-code for CNC milling. '
                    'Supports both KiCad and Fritzing exports.',
        epilog='Example: gerber2nc ~/projects/myboard -o output.nc'
    )

    parser.add_argument(
        'project',
        type=Path,
        help='Base path to Gerber files (without extension). '
             'For KiCad: expects *-F_Cu.gbr, *-Edge_Cuts.gbr, *-PTH.drl. '
             'For Fritzing: expects *_copperTop.gtl, *_contour.gm1, *_drill.txt'
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output G-code filename (default: <project>.nc)'
    )

    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Skip visualization, generate G-code directly'
    )

    # Toolpath parameters
    toolpath_group = parser.add_argument_group('Toolpath parameters')
    toolpath_group.add_argument(
        '--offset',
        type=float,
        default=DEFAULT_OFFSET_DISTANCE,
        metavar='MM',
        help=f'Initial offset from copper edge (default: {DEFAULT_OFFSET_DISTANCE}mm)'
    )
    toolpath_group.add_argument(
        '--passes',
        type=int,
        default=DEFAULT_NUM_PASSES,
        metavar='N',
        help=f'Number of milling passes (default: {DEFAULT_NUM_PASSES})'
    )
    toolpath_group.add_argument(
        '--spacing',
        type=float,
        default=DEFAULT_PATH_SPACING,
        metavar='MM',
        help=f'Spacing between passes (default: {DEFAULT_PATH_SPACING}mm)'
    )

    # Milling parameters
    milling_group = parser.add_argument_group('Milling parameters')
    milling_group.add_argument(
        '--spindle-speed',
        type=int,
        default=12000,
        metavar='RPM',
        help='Spindle speed in RPM (default: 12000)'
    )
    milling_group.add_argument(
        '--cut-depth',
        type=float,
        default=-0.1,
        metavar='MM',
        help='Trace isolation cut depth (default: -0.1mm)'
    )
    milling_group.add_argument(
        '--feed-rate',
        type=int,
        default=450,
        metavar='MM/MIN',
        help='Horizontal feed rate (default: 450 mm/min)'
    )

    # Verbosity
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    verbosity.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress non-error output'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    return parser


def main(args: list[str] = None) -> int:
    """
    Main entry point.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success)
    """
    parser = create_parser()
    opts = parser.parse_args(args)

    setup_logging(verbose=opts.verbose, quiet=opts.quiet)
    logger = logging.getLogger(__name__)

    # Validate cut depth - must be negative (below surface)
    if opts.cut_depth > 0:
        logger.warning(f"Cut depth {opts.cut_depth} is positive - converting to -{opts.cut_depth}")
        opts.cut_depth = -opts.cut_depth

    # Determine output filename
    output_file = opts.output or Path(f"{opts.project.name}.nc")

    logger.info(f"Gerber2nc v{__version__}")
    logger.info("")

    # Find input files
    copper_file, edgecuts_file, drill_file = find_gerber_files(opts.project)
    logger.info("")

    # Parse files
    extents = BoardExtents()

    traces_parser = GerberTracesParser(copper_file, extents)
    edgecuts_parser = GerberEdgeCutsParser(edgecuts_file, extents)
    drill_parser = DrillFileParser(drill_file, extents)

    # Shift coordinates to origin
    traces_parser.shift(extents.x_min, extents.y_min)
    edgecuts_parser.shift(extents.x_min, extents.y_min)
    drill_parser.shift(extents.x_min, extents.y_min)

    logger.info(f"Board size: {extents.width:.1f} x {extents.height:.1f} mm")

    # Generate toolpaths
    toolpath_gen = ToolpathGenerator(traces_parser)
    toolpaths = toolpath_gen.compute_toolpaths(
        offset_distance=opts.offset,
        num_passes=opts.passes,
        path_spacing=opts.spacing
    )

    # Visualize (unless --no-gui)
    if not opts.no_gui:
        visualizer = Visualizer(extents)
        visualizer.load_data(
            traces=traces_parser,
            toolpaths=toolpaths,
            outline=edgecuts_parser.outline,
            holes=drill_parser.holes
        )
        visualizer.show(title=opts.project.name)

    # Generate G-code
    milling_params = MillingParams(
        spindle_speed=opts.spindle_speed,
        cut_depth=opts.cut_depth,
        feed_rate=opts.feed_rate,
    )

    gcode_gen = GcodeGenerator(milling_params)
    gcode_gen.generate(
        filename=output_file,
        toolpaths=toolpaths,
        outline=edgecuts_parser.outline,
        holes=drill_parser.holes,
        board_height=extents.height
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
