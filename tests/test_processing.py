"""
Tests for toolpath generation.
"""

import pytest
from pathlib import Path
from textwrap import dedent
from gerber2nc.models import BoardExtents, Aperture
from gerber2nc.parsers import GerberTracesParser
from gerber2nc.processing import ToolpathGenerator


@pytest.fixture
def temp_gerber_with_traces_and_pads(tmp_path):
    """Create a Gerber file with traces and various pad types."""
    content = dedent("""\
        %FSLAX46Y46*%
        %MOMM*%
        %ADD10C,0.200000*%
        %ADD11C,1.000000*%
        %ADD12R,2.000000X1.500000*%
        D10*
        X10000000Y10000000D02*
        X20000000Y10000000D01*
        D11*
        X30000000Y10000000D03*
        D12*
        X40000000Y10000000D03*
        M02*
    """)
    filepath = tmp_path / "test.gbr"
    filepath.write_text(content)
    return filepath


class TestToolpathGenerator:
    """Tests for ToolpathGenerator."""

    def test_build_geometry_with_traces(self, tmp_path):
        """Test building geometry from traces."""
        content = dedent("""\
            %FSLAX46Y46*%
            %MOMM*%
            %ADD10C,0.200000*%
            D10*
            X10000000Y10000000D02*
            X20000000Y10000000D01*
            X20000000Y20000000D01*
            M02*
        """)
        filepath = tmp_path / "traces.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberTracesParser(filepath, extents)
        generator = ToolpathGenerator(parser)

        assert generator.combined_geometry is not None
        assert not generator.combined_geometry.is_empty

    def test_build_geometry_with_circle_pads(self, tmp_path):
        """Test building geometry from circular pads."""
        content = dedent("""\
            %FSLAX46Y46*%
            %MOMM*%
            %ADD10C,1.000000*%
            D10*
            X10000000Y10000000D03*
            X20000000Y10000000D03*
            M02*
        """)
        filepath = tmp_path / "circle_pads.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberTracesParser(filepath, extents)
        generator = ToolpathGenerator(parser)

        assert generator.combined_geometry is not None
        assert not generator.combined_geometry.is_empty

    def test_build_geometry_with_rectangle_pads(self, tmp_path):
        """Test building geometry from rectangular pads."""
        content = dedent("""\
            %FSLAX46Y46*%
            %MOMM*%
            %ADD10R,2.000000X1.000000*%
            D10*
            X10000000Y10000000D03*
            M02*
        """)
        filepath = tmp_path / "rect_pads.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberTracesParser(filepath, extents)
        generator = ToolpathGenerator(parser)

        assert generator.combined_geometry is not None
        assert not generator.combined_geometry.is_empty

    def test_build_geometry_mixed(self, temp_gerber_with_traces_and_pads):
        """Test building geometry with mixed traces and pads."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_with_traces_and_pads, extents)
        generator = ToolpathGenerator(parser)

        assert generator.combined_geometry is not None
        # Should have 1 trace, 1 circle pad, 1 rect pad
        assert not generator.combined_geometry.is_empty

    def test_build_geometry_unknown_pad_type(self, tmp_path):
        """Test handling of unknown pad type."""
        extents = BoardExtents()
        parser = GerberTracesParser.__new__(GerberTracesParser)
        parser.traces = []
        parser.pads = [
            [[10.0, 10.0], Aperture(type='unknown', diameter=1.0)]
        ]

        generator = ToolpathGenerator(parser)

        # Should skip unknown pad type
        assert generator.combined_geometry.is_empty

    def test_compute_toolpaths_single_pass(self, temp_gerber_with_traces_and_pads):
        """Test computing toolpaths with single pass."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_with_traces_and_pads, extents)
        generator = ToolpathGenerator(parser)

        toolpaths = generator.compute_toolpaths(
            offset_distance=0.22,
            num_passes=1,
            path_spacing=0.2
        )

        assert toolpaths is not None
        assert len(toolpaths.geoms) > 0

    def test_compute_toolpaths_multiple_passes(self, temp_gerber_with_traces_and_pads):
        """Test computing toolpaths with multiple passes."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_with_traces_and_pads, extents)
        generator = ToolpathGenerator(parser)

        toolpaths = generator.compute_toolpaths(
            offset_distance=0.22,
            num_passes=3,
            path_spacing=0.2
        )

        assert toolpaths is not None
        # Should have multiple segments
        assert len(toolpaths.geoms) > 0

    def test_compute_toolpaths_different_spacing(self, temp_gerber_with_traces_and_pads):
        """Test computing toolpaths with different spacing."""
        extents = BoardExtents()
        parser = GerberTracesParser(temp_gerber_with_traces_and_pads, extents)
        generator = ToolpathGenerator(parser)

        toolpaths = generator.compute_toolpaths(
            offset_distance=0.5,
            num_passes=2,
            path_spacing=0.3
        )

        assert toolpaths is not None
        assert len(toolpaths.geoms) > 0

    def test_compute_toolpaths_simple_geometry(self, tmp_path):
        """Test computing toolpaths with simple single-trace geometry."""
        content = dedent("""\
            %FSLAX46Y46*%
            %MOMM*%
            %ADD10C,0.200000*%
            D10*
            X10000000Y10000000D02*
            X20000000Y10000000D01*
            M02*
        """)
        filepath = tmp_path / "simple.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        parser = GerberTracesParser(filepath, extents)
        generator = ToolpathGenerator(parser)

        toolpaths = generator.compute_toolpaths(
            offset_distance=0.22,
            num_passes=2,
            path_spacing=0.2
        )

        assert toolpaths is not None
