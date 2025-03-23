"""Tests for CLI module functionality."""

from unittest.mock import MagicMock, patch

import geopandas as gpd
import pytest
from shapely.geometry import MultiPolygon, Polygon

from maps.cli import filter_exclaves, generate_map


class TestFilterExclaves:
    """Test suite for the filter_exclaves function."""

    def test_filter_with_multipolygon(self) -> None:
        """Test filtering exclaves with a MultiPolygon geometry."""
        # Create a mock target country with a MultiPolygon geometry
        main_polygon = Polygon([(0, 0), (0, 10), (10, 10), (10, 0)])
        small_polygon = Polygon([(20, 20), (20, 21), (21, 21), (21, 20)])
        multi_polygon = MultiPolygon([main_polygon, small_polygon])

        # Create mock GeoDataFrame
        target_country = gpd.GeoDataFrame(
            {"name": ["TestCountry"], "geometry": [multi_polygon]}
        )

        # Create mock territory info
        territory_info = {
            "territories": [
                {"percentage": 99.0},  # Main polygon is 99% of total area
                {"percentage": 1.0},  # Small polygon is 1% of total area
            ]
        }

        # Call the function
        filtered_country, percentage = filter_exclaves(target_country, territory_info)

        # Verify the results
        assert percentage == 99.0
        assert isinstance(filtered_country, gpd.GeoDataFrame)
        assert isinstance(filtered_country.geometry.iloc[0], Polygon)
        assert filtered_country.geometry.iloc[0].equals(main_polygon)

    def test_filter_with_single_polygon(self) -> None:
        """Test that a single Polygon is returned unchanged."""
        # Create a mock target country with a single Polygon
        polygon = Polygon([(0, 0), (0, 10), (10, 10), (10, 0)])

        # Create mock GeoDataFrame
        target_country = gpd.GeoDataFrame(
            {"name": ["TestCountry"], "geometry": [polygon]}
        )

        # Create mock territory info (not actually used in this case)
        territory_info = {
            "territories": [
                {"percentage": 100.0}  # Single polygon is 100% of total area
            ]
        }

        # Call the function
        filtered_country, percentage = filter_exclaves(target_country, territory_info)

        # Verify the results - should return the original target_country and None percentage
        assert (
            percentage == 100.0
        )  # When there's a single polygon, percentage is still returned
        assert filtered_country is target_country
        assert filtered_country.geometry.iloc[0].equals(polygon)


class TestGenerateMap:
    """Test suite for the generate_map function."""

    @patch("maps.cli.filter_exclaves")
    @patch("maps.cli.get_country_territory_info")
    @patch("maps.cli.load_country_data")
    @patch("maps.cli.create_map")
    def test_filter_exclaves_called_when_flag_set(
        self,
        mock_create_map: MagicMock,
        mock_load_country_data: MagicMock,
        mock_get_territory_info: MagicMock,
        mock_filter_exclaves: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that filter_exclaves is called when the exclude_exclaves flag is set."""
        # Mock command line arguments with exclude_exclaves flag set to true
        monkeypatch.setattr(
            "sys.argv", ["maps/cli.py", "Russia", "--exclude-exclaves", "true"]
        )

        # Create mock data
        mock_countries = MagicMock()
        mock_target_country = MagicMock()
        mock_neighbor_names = ["Finland", "Norway"]

        # Setup mock territory info to trigger the exclave handling
        mock_territory_info = {
            "has_exclaves": True,
            "is_island_nation": False,
            "territories": [{"percentage": 95.0}],
            "territory_type": "has_exclave",
        }

        # Setup mock filter_exclaves to return modified data
        filtered_country = MagicMock()
        mock_filter_exclaves.return_value = (filtered_country, 95.0)

        # Setup return values for mocks
        mock_load_country_data.return_value = (
            mock_countries,
            mock_target_country,
            mock_neighbor_names,
        )
        mock_get_territory_info.return_value = mock_territory_info

        # Create a mock args object
        class MockArgs:
            country = "Russia"
            db_path = "natural_earth_vector.sqlite"
            exclude_exclaves = True
            output = "/tmp/test_map.png"
            dpi = 300
            target_percentage = 0.3
            show_labels = True
            label_size = 8.0
            label_type = "name"
            border_width = 0.5
            show_territory_info = False

        # Call generate_map with mock args
        generate_map(MockArgs())

        # Verify filter_exclaves was called with correct arguments
        mock_filter_exclaves.assert_called_once_with(
            mock_target_country, mock_territory_info
        )

        # Verify create_map was called with the filtered country
        mock_create_map.assert_called_once()
        args, kwargs = mock_create_map.call_args
        assert args[0] == mock_countries
        assert (
            args[1] == filtered_country
        )  # Should be the filtered country, not the original

    @patch("maps.cli.filter_exclaves")
    @patch("maps.cli.get_country_territory_info")
    @patch("maps.cli.load_country_data")
    @patch("maps.cli.create_map")
    def test_filter_exclaves_not_called_when_flag_not_set(
        self,
        mock_create_map: MagicMock,
        mock_load_country_data: MagicMock,
        mock_get_territory_info: MagicMock,
        mock_filter_exclaves: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that filter_exclaves is not called when the exclude_exclaves flag is not set."""
        # Mock command line arguments without exclude_exclaves flag
        monkeypatch.setattr("sys.argv", ["maps/cli.py", "Russia"])

        # Create mock data
        mock_countries = MagicMock()
        mock_target_country = MagicMock()
        mock_neighbor_names = ["Finland", "Norway"]

        # Setup mock territory info
        mock_territory_info = {
            "has_exclaves": True,
            "is_island_nation": False,
            "territories": [{"percentage": 95.0}],
            "territory_type": "has_exclave",
        }

        # Setup return values for mocks
        mock_load_country_data.return_value = (
            mock_countries,
            mock_target_country,
            mock_neighbor_names,
        )
        mock_get_territory_info.return_value = mock_territory_info

        # Create a mock args object
        class MockArgs:
            country = "Russia"
            db_path = "natural_earth_vector.sqlite"
            exclude_exclaves = False  # Flag not set
            output = "/tmp/test_map.png"
            dpi = 300
            target_percentage = 0.3
            show_labels = True
            label_size = 8.0
            label_type = "name"
            border_width = 0.5
            show_territory_info = False

        # Call generate_map with mock args
        generate_map(MockArgs())

        # Verify filter_exclaves was not called
        mock_filter_exclaves.assert_not_called()

        # Verify create_map was called with the original country
        mock_create_map.assert_called_once()
        args, kwargs = mock_create_map.call_args
        assert args[0] == mock_countries
        assert args[1] == mock_target_country  # Should be the original country
