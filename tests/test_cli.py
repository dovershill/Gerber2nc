"""
Tests for command-line interface.
"""

import pytest
import logging
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch, MagicMock
from gerber2nc.cli import setup_logging, create_parser, main


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_default_logging(self):
        """Test default logging level."""
        # Clear existing handlers
        logging.root.handlers = []
        setup_logging()
        logger = logging.getLogger()
        assert logger.level == logging.INFO

    def test_verbose_logging(self):
        """Test verbose logging."""
        # Clear existing handlers
        logging.root.handlers = []
        setup_logging(verbose=True)
        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

    def test_quiet_logging(self):
        """Test quiet logging."""
        # Clear existing handlers
        logging.root.handlers = []
        setup_logging(quiet=True)
        logger = logging.getLogger()
        assert logger.level == logging.ERROR


class TestCreateParser:
    """Tests for create_parser function."""

    def test_creates_parser(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == 'gerber2nc'

    def test_parser_has_required_arguments(self):
        """Test that parser has all required arguments."""
        parser = create_parser()
        # Should have project argument
        args = parser.parse_args(['myproject'])
        assert args.project == Path('myproject')

    def test_parser_defaults(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args(['myproject'])

        assert args.output is None
        assert args.no_gui is False
        assert args.offset == 0.22
        assert args.passes == 3
        assert args.spacing == 0.2
        assert args.spindle_speed == 12000
        assert args.cut_depth == -0.1
        assert args.feed_rate == 450
        assert args.verbose is False
        assert args.quiet is False

    def test_parser_custom_arguments(self):
        """Test parsing custom arguments."""
        parser = create_parser()
        args = parser.parse_args([
            'myproject',
            '-o', 'custom.nc',
            '--no-gui',
            '--offset', '0.5',
            '--passes', '5',
            '--spacing', '0.3',
            '--spindle-speed', '10000',
            '--cut-depth', '-0.2',
            '--feed-rate', '300',
            '--verbose'
        ])

        assert args.output == Path('custom.nc')
        assert args.no_gui is True
        assert args.offset == 0.5
        assert args.passes == 5
        assert args.spacing == 0.3
        assert args.spindle_speed == 10000
        assert args.cut_depth == -0.2
        assert args.feed_rate == 300
        assert args.verbose is True


class TestMain:
    """Tests for main function."""

    @pytest.fixture
    def mock_gerber_files(self, tmp_path):
        """Create mock Gerber files for testing."""
        # Create copper file
        copper_content = dedent("""\
            %FSLAX46Y46*%
            %MOMM*%
            %ADD10C,0.200000*%
            D10*
            X10000000Y10000000D02*
            X20000000Y10000000D01*
            M02*
        """)
        copper_file = tmp_path / "test-F_Cu.gbr"
        copper_file.write_text(copper_content)

        # Create edge cuts file
        edge_content = dedent("""\
            %MOMM*%
            X0Y0D02*
            X30000000Y0D01*
            X30000000Y20000000D01*
            X0Y20000000D01*
            X0Y0D01*
            M02*
        """)
        edge_file = tmp_path / "test-Edge_Cuts.gbr"
        edge_file.write_text(edge_content)

        # Create drill file
        drill_content = dedent("""\
            M48
            METRIC
            T1C0.800
            %
            T1
            X10.0Y10.0
            M30
        """)
        drill_file = tmp_path / "test-PTH.drl"
        drill_file.write_text(drill_content)

        return tmp_path

    def test_main_basic_execution(self, mock_gerber_files, monkeypatch):
        """Test basic main execution with minimal arguments."""
        # Change to temp directory so output file is created there
        monkeypatch.chdir(mock_gerber_files)

        with patch('gerber2nc.cli.Visualizer') as mock_viz:
            # Mock the visualizer to avoid GUI
            mock_viz_instance = MagicMock()
            mock_viz.return_value = mock_viz_instance

            result = main(['test', '--no-gui'])

            assert result == 0
            # Output file should be created
            output_file = mock_gerber_files / "test.nc"
            assert output_file.exists()

    def test_main_with_custom_output(self, mock_gerber_files):
        """Test main with custom output filename."""
        result = main([
            str(mock_gerber_files / "test"),
            '--no-gui',
            '-o', str(mock_gerber_files / "custom.nc")
        ])

        assert result == 0
        output_file = mock_gerber_files / "custom.nc"
        assert output_file.exists()

    def test_main_with_verbose(self, mock_gerber_files):
        """Test main with verbose logging."""
        result = main([
            str(mock_gerber_files / "test"),
            '--no-gui',
            '--verbose'
        ])

        assert result == 0

    def test_main_with_quiet(self, mock_gerber_files):
        """Test main with quiet logging."""
        result = main([
            str(mock_gerber_files / "test"),
            '--no-gui',
            '--quiet'
        ])

        assert result == 0

    def test_main_positive_cut_depth_conversion(self, mock_gerber_files):
        """Test that positive cut depth is converted to negative."""
        result = main([
            str(mock_gerber_files / "test"),
            '--no-gui',
            '--cut-depth', '0.15'
        ])

        assert result == 0
        # Should have converted 0.15 to -0.15

    def test_main_with_toolpath_params(self, mock_gerber_files):
        """Test main with custom toolpath parameters."""
        result = main([
            str(mock_gerber_files / "test"),
            '--no-gui',
            '--offset', '0.5',
            '--passes', '5',
            '--spacing', '0.3'
        ])

        assert result == 0

    def test_main_with_milling_params(self, mock_gerber_files):
        """Test main with custom milling parameters."""
        result = main([
            str(mock_gerber_files / "test"),
            '--no-gui',
            '--spindle-speed', '10000',
            '--cut-depth', '-0.15',
            '--feed-rate', '300'
        ])

        assert result == 0

    def test_main_with_visualization(self, mock_gerber_files):
        """Test main with visualization (mocked)."""
        with patch('gerber2nc.cli.Visualizer') as mock_viz:
            mock_viz_instance = MagicMock()
            mock_viz.return_value = mock_viz_instance

            result = main([str(mock_gerber_files / "test")])

            assert result == 0
            # Visualizer should have been created and shown
            mock_viz.assert_called_once()
            mock_viz_instance.load_data.assert_called_once()
            mock_viz_instance.show.assert_called_once()

    def test_main_no_args_uses_sys_argv(self, mock_gerber_files):
        """Test that main with no args uses sys.argv."""
        with patch('sys.argv', ['gerber2nc', str(mock_gerber_files / "test"), '--no-gui']):
            result = main()
            assert result == 0
