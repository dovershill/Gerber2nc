"""
File detection utilities for Gerber files.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def find_gerber_files(
    base_path: str | Path
) -> tuple[Path, Optional[Path], Optional[Path]]:
    """
    Find Gerber files for copper, edge cuts, and drill holes.

    Supports both KiCad and Fritzing naming conventions.
    Searches in priority order, returning the first match for each type.

    Args:
        base_path: Base path/name for the project files (without extension)

    Returns:
        Tuple of (copper_file, edgecuts_file, drill_file)
        Edge cuts and drill files may be None if not found.

    Raises:
        SystemExit: If no copper layer file is found
    """
    base_path = Path(base_path)
    directory = base_path.parent if base_path.parent != base_path else Path(".")
    base_name = base_path.name

    # Search patterns ordered by priority (KiCad first, then Fritzing)
    copper_patterns = [
        f"{base_name}-F_Cu.gbr",
        f"{base_name}-B_Cu.gbr",
        f"{base_name}_copperTop.gtl",
        f"{base_name}_copperBottom.gbl",
        f"{base_name}*_Cu.gbr",
        f"{base_name}*.gtl",
        f"{base_name}*.gbl",
    ]

    edgecuts_patterns = [
        f"{base_name}-Edge_Cuts.gbr",
        f"{base_name}-Edge_cuts.gbr",
        f"{base_name}_contour.gm1",
        f"{base_name}*Edge*.gbr",
        f"{base_name}*contour*",
        f"{base_name}*.gm1",
    ]

    drill_patterns = [
        f"{base_name}-PTH.drl",
        f"{base_name}.drl",
        f"{base_name}-NPTH.drl",
        f"{base_name}_drill.txt",
        f"{base_name}*.drl",
        f"{base_name}*drill*.txt",
    ]

    def find_first_match(patterns: list[str]) -> Optional[Path]:
        for pattern in patterns:
            matches = list(directory.glob(pattern))
            if matches:
                return matches[0]
        return None

    copper_file = find_first_match(copper_patterns)
    edgecuts_file = find_first_match(edgecuts_patterns)
    drill_file = find_first_match(drill_patterns)

    # Log findings
    logger.info("File detection:")
    if copper_file:
        logger.info(f"  Copper layer: {copper_file.name}")
    else:
        logger.error(f"  Copper layer: NOT FOUND")
        logger.error(f"    Searched for: {base_name}-F_Cu.gbr, {base_name}_copperTop.gtl, etc.")

    if edgecuts_file:
        logger.info(f"  Edge cuts:    {edgecuts_file.name}")
    else:
        logger.info(f"  Edge cuts:    NOT FOUND (optional)")

    if drill_file:
        logger.info(f"  Drill file:   {drill_file.name}")
    else:
        logger.info(f"  Drill file:   NOT FOUND (optional)")

    if not copper_file:
        import sys
        logger.critical("No copper layer file found!")
        logger.critical(f"Please ensure Gerber files are in: {directory}")
        logger.critical(f"With base name: {base_name}")
        sys.exit(1)

    return copper_file, edgecuts_file, drill_file
