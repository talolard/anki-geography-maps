"""Tests for the refactored maps package."""

import os
import sys
from unittest.mock import MagicMock, patch

import geopandas as gpd
import pytest
from matplotlib.figure import Figure
from pandas import DataFrame
from shapely.geometry import Polygon

# Import from the original module
from olddraw_map import (
    MapColors,
    MapConfiguration,
    create_map,
    load_country_data,
    parse_args,
)

# Import from the refactored modules
from maps.models import MapColors as NewMapColors
from maps.models import MapConfiguration as NewMapConfiguration
from maps.data_loader import load_country_data as new_load_country_data
from maps.renderer import create_map as new_create_map
from maps.cli import parse_args as new_parse_args


class TestRefactoringEquivalence:
    """Test that the refactored code is equivalent to the original code."""

    def test_mapcolors_equivalence(self) -> None:
        """Test that the MapColors class has the same attributes in both versions."""
        orig_colors = MapColors()
        new_colors = NewMapColors()

        assert orig_colors.target_country == new_colors.target_country
        assert orig_colors.neighbor_countries == new_colors.neighbor_countries
        assert orig_colors.other_countries == new_colors.other_countries
        assert orig_colors.border_color == new_colors.border_color
        assert orig_colors.ocean_color == new_colors.ocean_color
        assert orig_colors.text_color == new_colors.text_color

    def test_mapconfiguration_equivalence(self) -> None:
        """Test that the MapConfiguration class has the same attributes in both versions."""
        orig_config = MapConfiguration(output_path="/tmp/test.png", title="Test Map")
        new_config = NewMapConfiguration(output_path="/tmp/test.png", title="Test Map")

        assert orig_config.output_path == new_config.output_path
        assert orig_config.title == new_config.title
        assert orig_config.figsize == new_config.figsize
        assert orig_config.dpi == new_config.dpi
        assert orig_config.include_legend == new_config.include_legend
        assert orig_config.target_percentage == new_config.target_percentage
        assert orig_config.exclude_exclaves == new_config.exclude_exclaves
        assert orig_config.main_area_threshold == new_config.main_area_threshold

    @patch("sys.argv", ["draw_map.py", "France"])
    def test_parse_args_equivalence(self) -> None:
        """Test that parse_args returns the same values in both versions."""
        # Use the same arguments for both
        test_args = ["France", "--db-path", "test.sqlite", "--dpi", "600"]

        orig_args = parse_args(test_args)
        new_args = new_parse_args(test_args)

        assert orig_args.country == new_args.country
        assert orig_args.db_path == new_args.db_path
        assert orig_args.dpi == new_args.dpi
        assert orig_args.target_percentage == new_args.target_percentage

        # New version has additional options
        assert hasattr(new_args, "exclude_exclaves")
