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

    def test_inch_units(self, tmp_path):
        """Test parsing Gerber file with inch units."""
        content = dedent("""\
            %FSLAX46Y46*%
            %MOIN*%
            %ADD10C,0.100000*%
            D10*
            X1000000Y1000000D02*
            X2000000Y1000000D01*
            M02*
        """)
        filepath = tmp_path / "inch.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberTracesParser(filepath, extents)

        # 1.0 inch = 25.4 mm
        assert len(parser.traces) == 1
        assert abs(parser.traces[0][0][0] - 25.4) < 0.1
        assert abs(parser.traces[0][0][1] - 25.4) < 0.1

    def test_roundrect_aperture(self, tmp_path):
        """Test parsing RoundRect aperture."""
        content = dedent("""\
            %FSLAX46Y46*%
            %MOMM*%
            %ADD12RoundRect,0.200000X-1.000000X-0.500000X1.000000X0.500000*%
            D12*
            X10000000Y10000000D03*
            M02*
        """)
        filepath = tmp_path / "roundrect.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberTracesParser(filepath, extents)

        assert len(parser.pads) == 1
        assert 12 in parser.apertures
        assert parser.apertures[12].type == 'rectangle'
        # width = abs(1.0) + abs(-1.0) + 0.2 = 2.2
        # height = abs(0.5) + abs(-0.5) + 0.2 = 1.2
        assert abs(parser.apertures[12].width - 2.2) < 0.01
        assert abs(parser.apertures[12].height - 1.2) < 0.01


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

    def test_comments_and_empty_lines(self, tmp_path):
        """Test parsing file with comments and empty lines."""
        content = dedent("""\
            M48
            ; This is a comment
            METRIC

            T1C0.800
            %
            ; Another comment
            T1
            X10.0Y10.0

            M30
        """)
        filepath = tmp_path / "test_comments.drl"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = DrillFileParser(filepath, extents)
        assert len(parser.holes) == 1

    def test_metric_fritzing_format(self, tmp_path):
        """Test metric drill file with Fritzing-style (non-decimal) coordinates."""
        content = dedent("""\
            M48
            METRIC
            T1C0.800
            %
            T1
            X010000Y015000
            M30
        """)
        filepath = tmp_path / "test_metric_fritzing.drl"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = DrillFileParser(filepath, extents)
        assert len(parser.holes) == 1
        # Should be 10mm and 15mm (with DRILL_FORMAT_METRIC scaling)
        x, y, _ = parser.holes[0]
        assert abs(x - 10.0) < 0.1
        assert abs(y - 15.0) < 0.1


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

    def test_missing_file(self, tmp_path):
        """Test handling of missing edge cuts file."""
        extents = BoardExtents()
        parser = GerberEdgeCutsParser(tmp_path / "nonexistent.gbr", extents)
        assert len(parser.outline) == 0

    def test_inch_units_edge_cuts(self, tmp_path):
        """Test parsing edge cuts file with inch units."""
        content = dedent("""\
            %MOIN*%
            X0Y0D02*
            X1000000Y0D01*
            X1000000Y1000000D01*
            X0Y1000000D01*
            X0Y0D01*
            M02*
        """)
        filepath = tmp_path / "edge_inch.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberEdgeCutsParser(filepath, extents)

        # 1.0 inch = 25.4 mm
        assert len(parser.outline) == 5
        assert abs(parser.outline[1][0] - 25.4) < 0.1

    def test_non_continuous_outline(self, tmp_path):
        """Test warning for non-continuous outline path."""
        content = dedent("""\
            %MOMM*%
            X0Y0D02*
            X50000000Y0D01*
            X100000000Y0D02*
            M02*
        """)
        filepath = tmp_path / "non_continuous.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberEdgeCutsParser(filepath, extents)
        assert len(parser.outline) == 3

    def test_non_closed_outline(self, tmp_path):
        """Test warning for non-closed outline."""
        content = dedent("""\
            %MOMM*%
            X0Y0D02*
            X50000000Y0D01*
            X50000000Y30000000D01*
            M02*
        """)
        filepath = tmp_path / "non_closed.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberEdgeCutsParser(filepath, extents)
        assert len(parser.outline) == 3
        assert parser.outline[0] != parser.outline[-1]

    def test_empty_outline(self, tmp_path):
        """Test file with no outline coordinates."""
        content = dedent("""\
            %MOMM*%
            M02*
        """)
        filepath = tmp_path / "empty.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberEdgeCutsParser(filepath, extents)
        assert len(parser.outline) == 0

    def test_shift_edge_cuts(self, tmp_path):
        """Test shifting edge cuts coordinates."""
        content = dedent("""\
            %MOMM*%
            X10000000Y10000000D02*
            X20000000Y10000000D01*
            M02*
        """)
        filepath = tmp_path / "shift_edge.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberEdgeCutsParser(filepath, extents)

        parser.shift(5.0, 5.0)

        assert parser.outline[0] == (5.0, 5.0)
        assert parser.outline[1] == (15.0, 5.0)
