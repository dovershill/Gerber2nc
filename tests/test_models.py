"""
Tests for data models.
"""

import pytest
from gerber2nc.models import BoardExtents, Aperture, MillingParams


class TestBoardExtents:
    """Tests for BoardExtents dataclass."""

    def test_initial_values(self):
        """Test default initial values are extreme."""
        extents = BoardExtents()
        assert extents.x_min == 1e9
        assert extents.x_max == -1e9
        assert extents.y_min == 1e9
        assert extents.y_max == -1e9

    def test_update_single_point(self):
        """Test updating with a single point."""
        extents = BoardExtents()
        extents.update(10.0, 20.0)

        assert extents.x_min == 10.0
        assert extents.x_max == 10.0
        assert extents.y_min == 20.0
        assert extents.y_max == 20.0

    def test_update_with_margin(self):
        """Test updating with margin."""
        extents = BoardExtents()
        extents.update(10.0, 20.0, margin=5.0)

        assert extents.x_min == 5.0
        assert extents.x_max == 15.0
        assert extents.y_min == 15.0
        assert extents.y_max == 25.0

    def test_update_multiple_points(self):
        """Test updating with multiple points."""
        extents = BoardExtents()
        extents.update(0.0, 0.0)
        extents.update(100.0, 50.0)
        extents.update(50.0, 25.0)

        assert extents.x_min == 0.0
        assert extents.x_max == 100.0
        assert extents.y_min == 0.0
        assert extents.y_max == 50.0

    def test_width_and_height(self):
        """Test width and height properties."""
        extents = BoardExtents()
        extents.update(10.0, 20.0)
        extents.update(110.0, 80.0)

        assert extents.width == 100.0
        assert extents.height == 60.0

    def test_is_valid(self):
        """Test validity check."""
        extents = BoardExtents()
        assert not extents.is_valid()

        extents.update(50.0, 50.0)
        assert extents.is_valid()


class TestAperture:
    """Tests for Aperture dataclass."""

    def test_circle_aperture(self):
        """Test circular aperture."""
        ap = Aperture(type='circle', diameter=1.5)
        assert ap.type == 'circle'
        assert ap.diameter == 1.5
        assert ap.width == 0.0
        assert ap.height == 0.0

    def test_rectangle_aperture(self):
        """Test rectangular aperture."""
        ap = Aperture(type='rectangle', width=2.0, height=1.5)
        assert ap.type == 'rectangle'
        assert ap.width == 2.0
        assert ap.height == 1.5


class TestMillingParams:
    """Tests for MillingParams dataclass."""

    def test_default_values(self):
        """Test default milling parameters."""
        params = MillingParams()
        assert params.spindle_speed == 12000
        assert params.cut_depth == -0.1
        assert params.safe_height == 3.0
        assert params.feed_rate == 450

    def test_custom_values(self):
        """Test custom milling parameters."""
        params = MillingParams(
            spindle_speed=10000,
            cut_depth=-0.15,
            feed_rate=300
        )
        assert params.spindle_speed == 10000
        assert params.cut_depth == -0.15
        assert params.feed_rate == 300
