"""
Tests for __main__.py entry point.
"""

import pytest
import sys
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch, MagicMock
import subprocess


def test_main_module_import():
    """Test that __main__ module can be imported."""
    import gerber2nc.__main__
    # Should have main imported
    assert hasattr(gerber2nc.__main__, 'main')
    # Should have sys module
    assert hasattr(gerber2nc.__main__, 'sys')


def test_main_entry_point_via_subprocess(tmp_path):
    """Test running __main__ as a script via subprocess."""
    # Create test Gerber files
    copper_content = dedent("""\
        %FSLAX46Y46*%
        %MOMM*%
        %ADD10C,0.200000*%
        D10*
        X10000000Y10000000D02*
        X20000000Y10000000D01*
        M02*
    """)
    (tmp_path / "test-F_Cu.gbr").write_text(copper_content)

    # Run as subprocess to avoid import issues
    result = subprocess.run(
        [sys.executable, '-m', 'gerber2nc', str(tmp_path / "test"), '--no-gui'],
        capture_output=True,
        text=True
    )

    # Should exit with code 0
    assert result.returncode == 0


def test_main_calls_cli_main():
    """Test that __main__ imports cli.main correctly."""
    # Import __main__ module
    import gerber2nc.__main__ as main_module

    # Verify that main_module.main is actually cli.main
    from gerber2nc.cli import main as cli_main
    assert main_module.main == cli_main
