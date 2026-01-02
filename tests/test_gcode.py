"""
Tests for G-code generation.
"""

import pytest
from pathlib import Path
from shapely.geometry import LineString, MultiLineString
from gerber2nc.models import MillingParams
from gerber2nc.gcode import GcodeGenerator


class TestGcodeGenerator:
    """Tests for GcodeGenerator."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        generator = GcodeGenerator()
        assert generator.params is not None
        assert generator.params.spindle_speed == 12000

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        params = MillingParams(spindle_speed=10000, cut_depth=-0.15)
        generator = GcodeGenerator(params)
        assert generator.params.spindle_speed == 10000
        assert generator.params.cut_depth == -0.15

    def test_generate_full_file(self, tmp_path):
        """Test generating complete G-code file."""
        generator = GcodeGenerator()

        # Create simple toolpaths
        line1 = LineString([(0, 0), (10, 0), (10, 10)])
        line2 = LineString([(20, 0), (30, 0)])
        toolpaths = MultiLineString([line1, line2])

        # Create outline
        outline = [(0, 0), (50, 0), (50, 30), (0, 30), (0, 0)]

        # Create holes (mix of small <= 0.85 and large > 0.85)
        holes = [(10, 10, 0.8), (20, 10, 1.0), (30, 10, 2.5)]

        output_file = tmp_path / "output.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=outline,
            holes=holes,
            board_height=30.0
        )

        assert result.exists()
        content = result.read_text()

        # Verify header
        assert "G21" in content  # mm units
        assert "G90" in content  # absolute positioning
        assert "S12000 M3" in content  # spindle speed

        # Verify trace milling
        assert "G1 Z-0.100" in content  # cut depth

        # Verify edge cuts
        assert "(Mill edge cut mark)" in content

        # Verify drilling
        assert "(Load small drill)" in content
        assert "(Load large drill)" in content

        # Verify footer
        assert "M30" in content  # end of program

    def test_generate_no_outline(self, tmp_path):
        """Test generating G-code without edge cuts."""
        generator = GcodeGenerator()

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        output_file = tmp_path / "no_outline.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=[],
            board_height=10.0
        )

        assert result.exists()
        content = result.read_text()
        # Should not have edge cut commands
        assert "(Mill edge cut mark)" not in content

    def test_generate_no_holes(self, tmp_path):
        """Test generating G-code without drill holes."""
        generator = GcodeGenerator()

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        output_file = tmp_path / "no_holes.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=[],
            board_height=10.0
        )

        assert result.exists()
        content = result.read_text()
        # Should not have drilling commands
        assert "(Load small drill)" not in content
        assert "(Load large drill)" not in content

    def test_generate_small_holes_only(self, tmp_path):
        """Test generating G-code with only small holes."""
        generator = GcodeGenerator()

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        # Only small holes (<= 0.85mm threshold)
        holes = [(10, 10, 0.5), (20, 10, 0.8)]

        output_file = tmp_path / "small_holes.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=holes,
            board_height=10.0
        )

        assert result.exists()
        content = result.read_text()
        assert "(Load small drill)" in content
        assert "(Load large drill)" not in content

    def test_generate_large_holes_only(self, tmp_path):
        """Test generating G-code with only large holes."""
        generator = GcodeGenerator()

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        # Only large holes (> 2.0mm threshold)
        holes = [(10, 10, 2.5), (20, 10, 3.0)]

        output_file = tmp_path / "large_holes.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=holes,
            board_height=10.0
        )

        assert result.exists()
        content = result.read_text()
        assert "(Load small drill)" not in content
        assert "(Load large drill)" in content

    def test_generate_mixed_holes(self, tmp_path):
        """Test generating G-code with both small and large holes."""
        generator = GcodeGenerator()

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        # Mix of small and large holes
        holes = [(10, 10, 0.8), (20, 10, 2.5)]

        output_file = tmp_path / "mixed_holes.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=holes,
            board_height=10.0
        )

        assert result.exists()
        content = result.read_text()
        assert "(Load small drill)" in content
        assert "(Load large drill)" in content

    def test_generate_with_string_filename(self, tmp_path):
        """Test generating G-code with string filename."""
        generator = GcodeGenerator()

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        output_file = str(tmp_path / "string_name.nc")
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=[],
            board_height=10.0
        )

        assert result.exists()
        assert isinstance(result, Path)

    def test_custom_milling_params(self, tmp_path):
        """Test G-code generation with custom milling parameters."""
        params = MillingParams(
            spindle_speed=10000,
            cut_depth=-0.15,
            feed_rate=300,
            plunge_feed_rate=100
        )
        generator = GcodeGenerator(params)

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        output_file = tmp_path / "custom_params.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=[],
            board_height=10.0
        )

        assert result.exists()
        content = result.read_text()
        assert "S10000 M3" in content  # custom spindle speed
        assert "G1 Z-0.150" in content  # custom cut depth

    def test_write_header(self, tmp_path):
        """Test header writing."""
        generator = GcodeGenerator()
        test_file = tmp_path / "test_header.nc"

        with test_file.open('w') as f:
            generator._write_header(f, generator.params)

        content = test_file.read_text()
        assert "G21" in content
        assert "G90" in content
        assert f"S{generator.params.spindle_speed} M3" in content

    def test_write_footer(self, tmp_path):
        """Test footer writing."""
        generator = GcodeGenerator()
        test_file = tmp_path / "test_footer.nc"

        with test_file.open('w') as f:
            generator._write_footer(f, 50.0)

        content = test_file.read_text()
        assert "M5" in content
        assert "G0 X0 Y50.0 Z50" in content
        assert "M30" in content

    def test_trace_milling_multiple_paths(self, tmp_path):
        """Test trace milling with multiple toolpath segments."""
        generator = GcodeGenerator()

        line1 = LineString([(0, 0), (10, 0), (10, 10)])
        line2 = LineString([(20, 0), (30, 0), (30, 10)])
        toolpaths = MultiLineString([line1, line2])

        output_file = tmp_path / "multi_paths.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=[],
            holes=[],
            board_height=10.0
        )

        content = result.read_text()
        # Should have multiple G0 (rapid) moves for different paths
        assert content.count("G0 X") >= 2

    def test_edge_cuts_with_multiple_points(self, tmp_path):
        """Test edge cuts with multiple points."""
        generator = GcodeGenerator()

        line = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line])

        outline = [(0, 0), (50, 0), (50, 30), (0, 30), (0, 0)]

        output_file = tmp_path / "edge_cuts.nc"
        result = generator.generate(
            filename=output_file,
            toolpaths=toolpaths,
            outline=outline,
            holes=[],
            board_height=30.0
        )

        content = result.read_text()
        assert "(Mill edge cut mark)" in content
        # Should have G1 moves for each point after the first
        assert content.count("G1 X") >= len(outline) - 1
