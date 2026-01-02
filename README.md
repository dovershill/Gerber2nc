# Gerber2nc

Convert Gerber PCB files to G-code for CNC milling.

![Example PCB](images/example_pcb.png)

A Python tool that generates CNC toolpaths from Gerber files for milling
single-sided PCBs. Displays a preview of traces and toolpaths before
generating G-code.

![Example Milled PCBs](images/example_milled_pcbs.jpg)

## Features

- **Supports KiCad and Fritzing** Gerber exports
- **Visual preview** of traces, pads, and toolpaths before milling
- **Automatic file detection** - finds the right files by naming convention
- **Configurable parameters** via command line or code
- **Multi-pass isolation milling** for clean trace separation

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gerber2nc.git
cd gerber2nc

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Quick Start

```bash
# KiCad project
gerber2nc /path/to/myboard

# Fritzing project
gerber2nc /path/to/fritzing_export/myproject

# With custom output filename
gerber2nc /path/to/myboard -o custom_output.nc

# Skip visualization (headless mode)
gerber2nc /path/to/myboard --no-gui
```

## Supported File Formats

The tool auto-detects files from both KiCad and Fritzing:

| File Type | KiCad | Fritzing |
|-----------|-------|----------|
| Copper layer | `*-F_Cu.gbr` | `*_copperTop.gtl` / `*_copperBottom.gbl` |
| Board outline | `*-Edge_Cuts.gbr` | `*_contour.gm1` |
| Drill holes | `*-PTH.drl` | `*_drill.txt` |

## Using with KiCad

1. In KiCad, go to **File → Fabrication Outputs → Gerbers**
2. Export your Gerber and drill files to a folder
3. Run: `gerber2nc path/to/myboard`

## Using with Fritzing

1. Open your Fritzing project (`.fzz` file)
2. Go to **File → Export → For Production → Extended Gerber (RS-274X)**
3. Select your output folder and export
4. Run: `gerber2nc path/to/myproject`

## Command Line Options

```
gerber2nc [-h] [-o OUTPUT] [--no-gui] [--offset MM] [--passes N]
          [--spacing MM] [--spindle-speed RPM] [--cut-depth MM]
          [--feed-rate MM/MIN] [-v] [-q] [--version] project

Arguments:
  project               Base path to Gerber files (without extension)

Options:
  -o, --output FILE     Output G-code filename (default: <project>.nc)
  --no-gui              Skip visualization, generate G-code directly
  -v, --verbose         Enable verbose output
  -q, --quiet           Suppress non-error output
  --version             Show version number

Toolpath parameters:
  --offset MM           Initial offset from copper (default: 0.22mm)
  --passes N            Number of milling passes (default: 3)
  --spacing MM          Spacing between passes (default: 0.2mm)

Milling parameters:
  --spindle-speed RPM   Spindle speed (default: 12000)
  --cut-depth MM        Trace isolation depth (default: -0.1mm)
  --feed-rate MM/MIN    Horizontal feed rate (default: 450)
```

## Development

### Dependencies

This project uses `pyproject.toml` for dependency management (PEP 621 standard):

**Core dependencies** (required to run):
- `shapely>=2.0.0` - Geometry operations for toolpath generation

**Development dependencies** (optional, for testing/linting):
- `pytest>=7.0.0` - Test framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `mypy>=1.0.0` - Static type checking

Install with:
```bash
pip install -e .           # Core dependencies only
pip install -e ".[dev]"    # Core + development dependencies
```

The `pyproject.toml` also configures pytest and mypy behavior, so no separate config files are needed.

### Quick Start with Makefile

```bash
# Create virtual environment and install dev dependencies
make venv
source venv/bin/activate
make install-dev

# Run tests
make test

# Run tests with coverage
make test-cov

# Type checking
make type-check

# Clean artifacts
make clean

# See all available commands
make help
```

### Manual Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy gerber2nc
```

## Project Structure

```
gerber2nc/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point for python -m gerber2nc
├── cli.py               # Command-line interface
├── constants.py         # Configuration constants
├── models.py            # Data classes
├── file_utils.py        # File detection utilities
├── processing.py        # Toolpath generation
├── visualization.py     # Tkinter preview
├── gcode.py             # G-code generation
└── parsers/
    ├── __init__.py
    ├── gerber.py        # Gerber file parsers
    └── drill.py         # Drill file parser
```

## Credits

- **Original Author**: Matthias Wandel (August 2025)
- **Fork Author**: Enrico Gasparini (December 2025)
  - Added Fritzing support
  - Refactored to Python best practices

## License

MIT License - see LICENSE file for details.
