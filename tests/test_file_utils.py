"""
Tests for file detection utilities.
"""

import pytest
from pathlib import Path
from gerber2nc.file_utils import find_gerber_files


class TestFindGerberFiles:
    """Tests for find_gerber_files function."""

    def test_find_kicad_files(self, tmp_path):
        """Test finding KiCad-style Gerber files."""
        # Create test files
        (tmp_path / "myboard-F_Cu.gbr").touch()
        (tmp_path / "myboard-Edge_Cuts.gbr").touch()
        (tmp_path / "myboard-PTH.drl").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "myboard")

        assert copper.name == "myboard-F_Cu.gbr"
        assert edge.name == "myboard-Edge_Cuts.gbr"
        assert drill.name == "myboard-PTH.drl"

    def test_find_kicad_back_copper(self, tmp_path):
        """Test finding KiCad back copper layer."""
        (tmp_path / "myboard-B_Cu.gbr").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "myboard")

        assert copper.name == "myboard-B_Cu.gbr"
        assert edge is None
        assert drill is None

    def test_find_fritzing_files(self, tmp_path):
        """Test finding Fritzing-style files."""
        (tmp_path / "myproject_copperTop.gtl").touch()
        (tmp_path / "myproject_contour.gm1").touch()
        (tmp_path / "myproject_drill.txt").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "myproject")

        assert copper.name == "myproject_copperTop.gtl"
        assert edge.name == "myproject_contour.gm1"
        assert drill.name == "myproject_drill.txt"

    def test_find_fritzing_bottom_copper(self, tmp_path):
        """Test finding Fritzing bottom copper layer."""
        (tmp_path / "myproject_copperBottom.gbl").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "myproject")

        assert copper.name == "myproject_copperBottom.gbl"

    def test_priority_kicad_over_fritzing(self, tmp_path):
        """Test that KiCad files have priority over Fritzing."""
        # Create both styles
        (tmp_path / "board-F_Cu.gbr").touch()
        (tmp_path / "board_copperTop.gtl").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "board")

        # Should pick KiCad file
        assert copper.name == "board-F_Cu.gbr"

    def test_wildcard_copper_match(self, tmp_path):
        """Test wildcard matching for copper files."""
        (tmp_path / "myboard-Inner1_Cu.gbr").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "myboard")

        assert copper.name == "myboard-Inner1_Cu.gbr"

    def test_wildcard_drill_match(self, tmp_path):
        """Test wildcard matching for drill files."""
        (tmp_path / "board-F_Cu.gbr").touch()
        (tmp_path / "board-NPTH.drl").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "board")

        assert drill.name == "board-NPTH.drl"

    def test_edge_cuts_case_variation(self, tmp_path):
        """Test Edge_cuts vs Edge_Cuts case variation."""
        (tmp_path / "board-F_Cu.gbr").touch()
        (tmp_path / "board-Edge_cuts.gbr").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "board")

        assert edge.name == "board-Edge_cuts.gbr"

    def test_plain_drl_file(self, tmp_path):
        """Test finding plain .drl file."""
        (tmp_path / "board-F_Cu.gbr").touch()
        (tmp_path / "board.drl").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "board")

        assert drill.name == "board.drl"

    def test_missing_optional_files(self, tmp_path):
        """Test that missing edge cuts and drill files return None."""
        (tmp_path / "board-F_Cu.gbr").touch()

        copper, edge, drill = find_gerber_files(tmp_path / "board")

        assert copper is not None
        assert edge is None
        assert drill is None

    def test_missing_copper_file_exits(self, tmp_path):
        """Test that missing copper file causes SystemExit."""
        with pytest.raises(SystemExit) as exc_info:
            find_gerber_files(tmp_path / "nonexistent")

        assert exc_info.value.code == 1

    def test_base_path_with_directory(self, tmp_path):
        """Test providing full path to subdirectory."""
        subdir = tmp_path / "gerbers"
        subdir.mkdir()
        (subdir / "pcb-F_Cu.gbr").touch()

        copper, edge, drill = find_gerber_files(subdir / "pcb")

        assert copper.name == "pcb-F_Cu.gbr"

    def test_current_directory_search(self, tmp_path, monkeypatch):
        """Test searching in current directory."""
        # Create files in tmp_path
        (tmp_path / "board-F_Cu.gbr").touch()

        # Change to that directory
        monkeypatch.chdir(tmp_path)

        copper, edge, drill = find_gerber_files("board")

        assert copper.name == "board-F_Cu.gbr"
