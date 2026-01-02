"""
Tests for __main__.py entry point.
"""

import pytest
import sys
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch


def test_main_module_import():
    """Test that __main__ module can be imported."""
    import gerber2nc.__main__
    # Should have main imported
    assert hasattr(gerber2nc.__main__, 'main')


def test_main_entry_point(tmp_path):
    """Test running __main__ as a script."""
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

    # Mock sys.argv and run
    with patch('sys.argv', ['gerber2nc', str(tmp_path / "test"), '--no-gui']):
        with patch('sys.exit') as mock_exit:
            # Run __main__ module
            import runpy
            runpy.run_module('gerber2nc', run_name='__main__')

            # Should call sys.exit with 0
            mock_exit.assert_called_once_with(0)
