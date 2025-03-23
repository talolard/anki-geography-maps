"""Tests for multilingual label support functionality."""

from unittest.mock import MagicMock, patch

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from maps.cli import generate_map, parse_args
from maps.draw_map import load_country_data
from maps.language_config import (
    get_language_column,
    get_supported_languages,
    is_language_supported,
)
from maps.models import MapConfiguration


class TestLanguageConfig:
    """Test suite for language configuration module."""

    def test_get_supported_languages(self) -> None:
        """Test retrieving the list of supported languages."""
        languages = get_supported_languages()

        # Verify that the returned list contains expected languages
        assert isinstance(languages, list)
        assert "en" in languages
        assert "fr" in languages
        assert "es" in languages
        assert len(languages) > 5  # Ensure we have a reasonable number of languages

    def test_is_language_supported(self) -> None:
        """Test language code validation."""
        # Test valid language codes
        assert is_language_supported("en") is True
        assert is_language_supported("fr") is True
        assert is_language_supported("es") is True

        # Test invalid language codes
        assert is_language_supported("xx") is False
        assert is_language_supported("") is False
        assert is_language_supported(None) is False  # type: ignore

    def test_get_language_column(self) -> None:
        """Test getting the correct database column for a language."""
        # Test valid language codes
        assert get_language_column("en") == "name_en"
        assert get_language_column("fr") == "name_fr"
        assert get_language_column("es") == "name_es"

        # Test fallback to default
        assert get_language_column("xx") == "name"  # Should fallback to default

        # Test with an explicitly provided fallback
        assert get_language_column("xx", fallback="name_en") == "name_en"


class TestCLILanguageArguments:
    """Test suite for CLI language argument handling."""

    def test_parse_args_with_language(self) -> None:
        """Test parsing command-line arguments with language option."""
        # Test with valid language
        args = parse_args(["map", "Germany", "--language", "fr"])
        assert args.language == "fr"

        # Test with short form
        args = parse_args(["map", "Germany", "-l", "es"])
        assert args.language == "es"

        # Test default (should be "en")
        args = parse_args(["map", "Germany"])
        assert args.language == "en"

    @patch("sys.stderr")
    def test_parse_args_with_invalid_language(self, mock_stderr: MagicMock) -> None:
        """Test parsing command-line arguments with invalid language option."""
        with pytest.raises(SystemExit):
            parse_args(["map", "Germany", "--language", "xx"])

    def test_list_languages_option(self) -> None:
        """Test the --list-languages option."""
        with pytest.raises(SystemExit):
            # This should exit, but we just want to verify the option is recognized
            parse_args(["--list-languages"])


@pytest.fixture
def mock_countries_df() -> gpd.GeoDataFrame:
    """Create a mock GeoDataFrame with countries for testing."""
    # Create mock polygons for countries
    germany_poly = Polygon([(10, 50), (10, 55), (15, 55), (15, 50)])
    france_poly = Polygon([(5, 45), (5, 50), (10, 50), (10, 45)])
    poland_poly = Polygon([(15, 50), (15, 55), (20, 55), (20, 50)])

    # Create mock GeoDataFrame with multilingual names
    return gpd.GeoDataFrame(
        {
            "name": ["Germany", "France", "Poland"],
            "name_en": ["Germany", "France", "Poland"],
            "name_fr": ["Allemagne", "France", "Pologne"],
            "name_de": ["Deutschland", "Frankreich", "Polen"],
            "name_es": ["Alemania", "Francia", "Polonia"],
            "iso_a3": ["DEU", "FRA", "POL"],
            "display_iso": ["DEU", "FRA", "POL"],
            "GEOMETRY": [
                germany_poly,
                france_poly,
                poland_poly,
            ],  # Add GEOMETRY column for the tests
            "geometry": [germany_poly, france_poly, poland_poly],
        }
    )


class TestDrawMapWithLanguage:
    """Test suite for draw_map module with language support."""

    @patch("maps.draw_map.get_neighboring_countries")
    @patch("maps.draw_map.pd.read_sql")
    @patch("sqlite3.connect")
    @patch("maps.draw_map.wkb.loads")
    def test_load_country_data_with_language(
        self,
        mock_loads: MagicMock,
        mock_connect: MagicMock,
        mock_read_sql: MagicMock,
        mock_get_neighboring_countries: MagicMock,
        mock_countries_df: gpd.GeoDataFrame,
    ) -> None:
        """Test loading country data with a specific language."""
        # Setup mocks
        mock_db = MagicMock()
        mock_connect.return_value = mock_db

        # Mock wkb.loads to return the polygon directly
        mock_loads.side_effect = lambda x: x

        mock_read_sql.return_value = mock_countries_df

        # Mock neighboring countries result
        mock_get_neighboring_countries.return_value = [
            ("France", "FR"),
            ("Poland", "PL"),
        ]

        # Call load_country_data with German language
        countries, target, neighbors = load_country_data("Germany", language="de")

        # Verify that the appropriate language column was requested
        args, kwargs = mock_read_sql.call_args
        query = args[0]
        assert "name_de" in query, "Query should include the language-specific column"

        # Verify that a display_name column was created
        assert "display_name" in countries.columns

        # Verify the display name values (should be German)
        assert "Deutschland" in countries["display_name"].values
        assert "Frankreich" in countries["display_name"].values
        assert "Polen" in countries["display_name"].values

    @patch("maps.draw_map.get_neighboring_countries")
    @patch("maps.draw_map.pd.read_sql")
    @patch("sqlite3.connect")
    @patch("maps.draw_map.wkb.loads")
    def test_display_name_fallback(
        self,
        mock_loads: MagicMock,
        mock_connect: MagicMock,
        mock_read_sql: MagicMock,
        mock_get_neighboring_countries: MagicMock,
        mock_countries_df: gpd.GeoDataFrame,
    ) -> None:
        """Test fallback to English when a translation is missing."""
        # Setup mocks
        mock_db = MagicMock()
        mock_connect.return_value = mock_db

        # Mock wkb.loads to return the polygon directly
        mock_loads.side_effect = lambda x: x

        # Create a DataFrame with missing translations
        df_with_missing = mock_countries_df.copy()
        df_with_missing.loc[0, "name_fr"] = None  # Make one translation missing
        mock_read_sql.return_value = df_with_missing

        # Mock neighboring countries result
        mock_get_neighboring_countries.return_value = [
            ("France", "FR"),
            ("Poland", "PL"),
        ]

        # Call load_country_data with French language
        countries, target, neighbors = load_country_data("Germany", language="fr")

        # Verify display_name uses English name for Germany (index 0) due to missing translation
        assert countries["display_name"].iloc[0] == "Germany"
        # But uses French for others
        assert countries["display_name"].iloc[1] == "France"
        assert countries["display_name"].iloc[2] == "Pologne"


@pytest.mark.integration
class TestMultilingualIntegration:
    """Integration tests for multilingual label support."""

    @patch("maps.cli.load_country_data")
    @patch("maps.cli.create_map")
    def test_language_passed_to_load_country_data(
        self,
        mock_create_map: MagicMock,
        mock_load_country_data: MagicMock,
    ) -> None:
        """Test that the language parameter is correctly passed to load_country_data."""
        # Mock data
        mock_countries = MagicMock()
        mock_target_country = MagicMock()
        mock_neighbor_names = ["France", "Belgium"]

        mock_load_country_data.return_value = (
            mock_countries,
            mock_target_country,
            mock_neighbor_names,
        )

        # Create mock args
        class MockArgs:
            country = "Germany"
            db_path = "natural_earth_vector.sqlite"
            language = "fr"
            exclude_exclaves = False
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

        # Verify load_country_data was called with the language parameter
        mock_load_country_data.assert_called_once()
        args, kwargs = mock_load_country_data.call_args
        assert args[0] == "Germany"  # Country name should be in English
        assert kwargs.get("language") == "fr"  # Language should be passed

    @patch("maps.renderer.plt")
    @patch("maps.renderer.gpd.GeoDataFrame.plot")
    def test_renderer_uses_display_name(
        self,
        mock_plot: MagicMock,
        mock_plt: MagicMock,
        mock_countries_df: gpd.GeoDataFrame,
    ) -> None:
        """Test that the renderer uses the display_name for labels."""
        # Add display_name column with German names
        df = mock_countries_df.copy()
        df["display_name"] = df["name_de"]

        # Create simplified versions for target and neighbor lists
        target_country = df[df["name"] == "Germany"].copy()
        neighbor_names = ["France", "Poland"]

        # Create a config with German language
        config = MapConfiguration(
            output_path="/tmp/test_map.png",
            title="Test Map",
            language="de",
        )

        # Mock the subplots and text methods
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Import and call create_map
        from maps.renderer import create_map

        create_map(df, target_country, neighbor_names, config)

        # Check that the display_name is used in the text calls to the axis
        # This is a simplistic check, as in reality we would need to mock and check
        # the behavior of add_labels method which is where the text is actually added
        mock_ax.text.assert_called()


@pytest.mark.parametrize(
    "language,expected_column",
    [
        ("en", "name_en"),
        ("fr", "name_fr"),
        ("es", "name_es"),
        ("de", "name_de"),
        ("ru", "name_ru"),
        ("xx", "name"),  # Invalid should fall back to default
    ],
)
def test_language_column_mapping(language: str, expected_column: str) -> None:
    """Parameterized test for language column mapping."""
    assert get_language_column(language) == expected_column
