"""
Entry point for running gerber2nc as a module.

Usage: python -m gerber2nc [args]
"""

import sys
from gerber2nc.cli import main

if __name__ == '__main__':
    sys.exit(main())
