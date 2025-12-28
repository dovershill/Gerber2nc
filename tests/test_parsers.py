"""
Tests for Gerber and drill file parsers.
"""

import pytest
from pathlib import Path
from textwrap import dedent
from gerber2nc.models import BoardExtents
from gerber2nc.parsers import GerberTracesParser, GerberEdgeCutsParser, DrillFileParser


@pytest.fixture
def temp_gerber_file(tmp_path):
    """Create a temporary Gerber file for testing."""
    content = dedent("""\
        G04 Test Gerber*
        %FSLAX46Y46*%
        %MOMM*%
        %ADD10C,0.200000*%
        %ADD11R,1.500000X1.500000*%
        D10*
        X10000000Y10000000D02*
        X20000000Y10000000D01*
        D11*
        X15000000Y15000000D03*
        M02*
    """)

    filepath = tmp_path / "test.gbr"
    filepath.write_text(content)
    return filepath


@pytest.fixture
def temp_drill_file(tmp_path):
    """Create a temporary drill file for testing."""
    content = dedent("""\
        M48
        METRIC
        T1C0.800
        T2C1.000
        %
        T1
        X10.0Y10.0
        X20.0Y10.0
        T2
        X15.0Y15.0
        M30
    """)

    filepath = tmp_path / "test.drl"
    filepath.write_text(content)
    return filepath


@pytest.fixture
def temp_fritzing_drill(tmp_path):
    """Create a Fritzing-style drill file (no decimals)."""
    content = dedent("""\
        M48
        INCH
        T100C0.039
        %
        T100
        X010000Y015000
        X020000Y015000
        M30
    """)

    filepath = tmp_path / "test_drill.txt"
    filepath.write_text(content)
    return filepath


class TestGerberTracesParser:
    """Tests for GerberTracesParser."""

    def test_parse_traces(self, temp_gerber_file):
        """Test parsing traces from Gerber file."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_file, extents)

        assert len(parser.traces) == 1
        trace = parser.traces[0]
        assert trace[0] == [10.0, 10.0]  # start
        assert trace[1] == [20.0, 10.0]  # end
        assert trace[2] == 0.2  # width

    def test_parse_pads(self, temp_gerber_file):
        """Test parsing pads from Gerber file."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_file, extents)

        assert len(parser.pads) == 1
        pad = parser.pads[0]
        assert pad[0] == [15.0, 15.0]  # position
        assert pad[1].type == 'rectangle'
        assert pad[1].width == 1.5
        assert pad[1].height == 1.5

    def test_extents_updated(self, temp_gerber_file):
        """Test that extents are updated during parsing."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_file, extents)

        assert extents.is_valid()
        # Check approximate bounds (accounting for margins)
        assert extents.x_min < 15.0
        assert extents.x_max > 15.0

    def test_shift_coordinates(self, temp_gerber_file):
        """Test coordinate shifting."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_file, extents)

        parser.shift(5.0, 5.0)

        # First trace should be shifted
        assert parser.traces[0][0] == [5.0, 5.0]
        assert parser.traces[0][1] == [15.0, 5.0]

        # Pad should be shifted
        assert parser.pads[0][0] == [10.0, 10.0]


class TestDrillFileParser:
    """Tests for DrillFileParser."""

    def test_parse_metric_drill(self, temp_drill_file):
        """Test parsing metric drill file."""
        extents = BoardExtents()
        parser = DrillFileParser(temp_drill_file, extents)

        assert len(parser.holes) == 3
        assert parser.tool_diameters['1'] == 0.8
        assert parser.tool_diameters['2'] == 1.0

        # Check first hole
        x, y, dia = parser.holes[0]
        assert x == 10.0
        assert y == 10.0
        assert dia == 0.8

    def test_parse_fritzing_drill(self, temp_fritzing_drill):
        """Test parsing Fritzing-style drill file (implied decimals)."""
        extents = BoardExtents()
        parser = DrillFileParser(temp_fritzing_drill, extents)

        assert len(parser.holes) == 2

        # X010000 with INCH and 2.4 format = 1.0 inches = 25.4mm
        x, y, dia = parser.holes[0]
        assert abs(x - 25.4) < 0.1  # 1.0 inch
        assert abs(y - 38.1) < 0.1  # 1.5 inch

    def test_shift_holes(self, temp_drill_file):
        """Test hole coordinate shifting."""
        extents = BoardExtents()
        parser = DrillFileParser(temp_drill_file, extents)

        parser.shift(10.0, 10.0)

        x, y, _ = parser.holes[0]
        assert x == 0.0
        assert y == 0.0

    def test_missing_file(self, tmp_path):
        """Test handling of missing file."""
        extents = BoardExtents()
        parser = DrillFileParser(tmp_path / "nonexistent.drl", extents)
        assert len(parser.holes) == 0


class TestGerberEdgeCutsParser:
    """Tests for GerberEdgeCutsParser."""

    def test_parse_outline(self, tmp_path):
        """Test parsing board outline."""
        content = dedent("""\
            %MOMM*%
            X0Y0D02*
            X50000000Y0D01*
            X50000000Y30000000D01*
            X0Y30000000D01*
            X0Y0D01*
            M02*
        """)
        filepath = tmp_path / "edge.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberEdgeCutsParser(filepath, extents)

        assert len(parser.outline) == 5
        assert parser.outline[0] == (0.0, 0.0)
        assert parser.outline[1] == (50.0, 0.0)
        assert parser.outline[4] == (0.0, 0.0)  # Closed

    def test_none_filename(self):
        """Test with None filename."""
        extents = BoardExtents()
        parser = GerberEdgeCutsParser(None, extents)
        assert len(parser.outline) == 0
