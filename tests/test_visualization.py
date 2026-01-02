"""
Tests for visualization module.
"""

import pytest
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch
from shapely.geometry import LineString, MultiLineString
from gerber2nc.models import BoardExtents, Aperture
from gerber2nc.parsers import GerberTracesParser
from gerber2nc.visualization import Visualizer


@pytest.fixture
def temp_gerber_file(tmp_path):
    """Create a Gerber file for testing."""
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
        X30000000Y15000000D03*
        D12*
        X40000000Y15000000D03*
        M02*
    """)
    filepath = tmp_path / "test.gbr"
    filepath.write_text(content)
    return filepath


class TestVisualizer:
    """Tests for Visualizer class."""

    def test_init(self):
        """Test visualizer initialization."""
        extents = BoardExtents()
        extents.update(0, 0)
        extents.update(50, 30)

        viz = Visualizer(extents)

        assert viz.extents == extents
        assert viz.scale == 25
        assert viz.traces_parser is None
        assert viz.toolpaths is None
        assert viz.outline == []
        assert viz.holes == []

    def test_load_data(self, temp_gerber_file):
        """Test loading visualization data."""
        extents = BoardExtents()
        traces = GerberTracesParser(temp_gerber_file, extents)

        line1 = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line1])

        outline = [(0, 0), (50, 0), (50, 30), (0, 30), (0, 0)]
        holes = [(10, 10, 0.8), (20, 10, 1.0)]

        viz = Visualizer(extents)
        viz.load_data(
            traces=traces,
            toolpaths=toolpaths,
            outline=outline,
            holes=holes
        )

        assert viz.traces_parser == traces
        assert viz.toolpaths == toolpaths
        assert viz.outline == outline
        assert viz.holes == holes

    @patch('tkinter.Tk')
    @patch('tkinter.Canvas')
    def test_show_with_outline(self, mock_canvas_class, mock_tk_class, temp_gerber_file):
        """Test show method with outline."""
        extents = BoardExtents()
        traces = GerberTracesParser(temp_gerber_file, extents)

        line1 = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line1])

        outline = [(0, 0), (50, 0), (50, 30), (0, 30), (0, 0)]
        holes = [(10, 10, 0.8)]

        # Setup mocks
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_root.winfo_screenwidth.return_value = 1920

        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        viz = Visualizer(extents)
        viz.load_data(traces, toolpaths, outline, holes)
        viz.show(title="Test Board")

        # Verify window was created
        mock_tk_class.assert_called_once()
        mock_root.title.assert_called_once()
        mock_root.mainloop.assert_called_once()

        # Verify canvas was created
        mock_canvas_class.assert_called_once()
        mock_canvas.pack.assert_called_once()

    @patch('tkinter.Tk')
    @patch('tkinter.Canvas')
    def test_show_without_outline(self, mock_canvas_class, mock_tk_class, temp_gerber_file):
        """Test show method without outline."""
        extents = BoardExtents()
        traces = GerberTracesParser(temp_gerber_file, extents)

        line1 = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line1])

        # Setup mocks
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_root.winfo_screenwidth.return_value = 1920

        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        viz = Visualizer(extents)
        viz.load_data(traces, toolpaths, [], [])
        viz.show(title="Test Board")

        # Verify visualization was shown
        mock_root.mainloop.assert_called_once()

    @patch('tkinter.Tk')
    @patch('tkinter.Canvas')
    def test_show_with_scale_adjustment(self, mock_canvas_class, mock_tk_class, temp_gerber_file):
        """Test show method with scale adjustment for large boards."""
        extents = BoardExtents()
        extents.update(0, 0)
        extents.update(500, 300)  # Large board

        traces = GerberTracesParser(temp_gerber_file, extents)

        line1 = LineString([(0, 0), (10, 0)])
        toolpaths = MultiLineString([line1])

        # Setup mocks with small screen
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_root.winfo_screenwidth.return_value = 800  # Small screen

        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        viz = Visualizer(extents)
        viz.load_data(traces, toolpaths, [], [])
        viz.show(title="Large Board")

        # Scale should have been adjusted
        assert viz.scale < 25

    def test_draw_outline(self):
        """Test drawing board outline."""
        extents = BoardExtents()
        extents.update(0, 0)
        extents.update(50, 30)

        outline = [(0, 0), (50, 0), (50, 30), (0, 30), (0, 0)]

        viz = Visualizer(extents)
        viz.outline = outline

        mock_canvas = MagicMock()
        viz._draw_outline(mock_canvas, canvas_height=600)

        # Should have created polygon
        mock_canvas.create_polygon.assert_called_once()

    def test_draw_outline_empty(self):
        """Test drawing with no outline."""
        extents = BoardExtents()
        viz = Visualizer(extents)
        viz.outline = []

        mock_canvas = MagicMock()
        viz._draw_outline(mock_canvas, canvas_height=600)

        # Should not create any shapes
        mock_canvas.create_polygon.assert_not_called()

    def test_draw_outline_too_few_points(self):
        """Test drawing outline with too few points."""
        extents = BoardExtents()
        viz = Visualizer(extents)
        viz.outline = [(0, 0), (10, 10)]  # Only 2 points

        mock_canvas = MagicMock()
        viz._draw_outline(mock_canvas, canvas_height=600)

        # Should not create polygon (needs at least 3 points)
        mock_canvas.create_polygon.assert_not_called()

    def test_draw_traces(self, temp_gerber_file):
        """Test drawing copper traces."""
        extents = BoardExtents()
        traces = GerberTracesParser(temp_gerber_file, extents)

        viz = Visualizer(extents)
        viz.traces_parser = traces

        mock_canvas = MagicMock()
        viz._draw_traces(mock_canvas, canvas_height=600)

        # Should have drawn lines
        assert mock_canvas.create_line.call_count > 0

    def test_draw_pads_circle(self, tmp_path):
        """Test drawing circular pads."""
        content = dedent("""\
            %FSLAX46Y46*%
            %MOMM*%
            %ADD10C,1.000000*%
            D10*
            X10000000Y10000000D03*
            M02*
        """)
        filepath = tmp_path / "circle_pads.gbr"
        filepath.write_text(content)

        extents = BoardExtents()
        traces = GerberTracesParser(filepath, extents)

        viz = Visualizer(extents)
        viz.traces_parser = traces

        mock_canvas = MagicMock()
        viz._draw_pads(mock_canvas, canvas_height=600)

        # Should have drawn oval
        mock_canvas.create_oval.assert_called_once()

    def test_draw_pads_rectangle(self, tmp_path):
        """Test drawing rectangular pads."""
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
        traces = GerberTracesParser(filepath, extents)

        viz = Visualizer(extents)
        viz.traces_parser = traces

        mock_canvas = MagicMock()
        viz._draw_pads(mock_canvas, canvas_height=600)

        # Should have drawn rectangle
        mock_canvas.create_rectangle.assert_called_once()

    def test_draw_toolpaths(self):
        """Test drawing toolpaths."""
        extents = BoardExtents()

        line1 = LineString([(0, 0), (10, 0), (10, 10)])
        line2 = LineString([(20, 0), (30, 0)])
        toolpaths = MultiLineString([line1, line2])

        viz = Visualizer(extents)
        viz.toolpaths = toolpaths

        mock_canvas = MagicMock()
        viz._draw_toolpaths(mock_canvas, canvas_height=600)

        # Should have drawn 2 lines
        assert mock_canvas.create_line.call_count == 2

    def test_draw_holes(self):
        """Test drawing drill holes."""
        extents = BoardExtents()

        holes = [(10, 10, 0.8), (20, 10, 1.0), (30, 15, 2.5)]

        viz = Visualizer(extents)
        viz.holes = holes

        mock_canvas = MagicMock()
        viz._draw_holes(mock_canvas, canvas_height=600)

        # Should have drawn 3 circles
        assert mock_canvas.create_oval.call_count == 3
