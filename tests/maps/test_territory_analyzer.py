"""Tests for the territory_analyzer module."""

from unittest.mock import MagicMock, patch

import pytest
from shapely.geometry import MultiPolygon, Polygon

from maps.territory_analyzer import (
    CountryGeometryType,
    TerritoryAnalysisResult,
    TerritoryAnalyzer,
    load_country_geometry,
)


class TestCountryGeometryType:
    """Test suite for the CountryGeometryType enum."""

    def test_enum_values(self) -> None:
        """Test that the enum has the expected values."""
        assert CountryGeometryType.CONTINUOUS.value == "continuous"
        assert CountryGeometryType.ISLAND_NATION.value == "island_nation"
        assert CountryGeometryType.HAS_EXCLAVE.value == "has_exclave"


class TestTerritoryAnalysisResult:
    """Test suite for the TerritoryAnalysisResult dataclass."""

    def test_default_values(self) -> None:
        """Test the default values of TerritoryAnalysisResult."""
        result = TerritoryAnalysisResult(
            country_name="Test Country",
            geometry_type=CountryGeometryType.CONTINUOUS,
            total_area=1000.0,
        )

        assert result.country_name == "Test Country"
        assert result.geometry_type == CountryGeometryType.CONTINUOUS
        assert result.total_area == 1000.0
        assert result.main_polygon_area == 1000.0
        assert result.main_polygon_percentage == 100.0
        assert result.polygon_count == 1
        assert result.max_distance_between_polygons == 0.0
        assert result.separate_territories == []

    def test_custom_values(self) -> None:
        """Test custom values for TerritoryAnalysisResult."""
        territories = [
            {"area": 800.0, "percentage": 80.0, "centroid": (10.0, 50.0)},
            {"area": 200.0, "percentage": 20.0, "centroid": (20.0, 60.0)},
        ]

        result = TerritoryAnalysisResult(
            country_name="Test Country",
            geometry_type=CountryGeometryType.HAS_EXCLAVE,
            total_area=1000.0,
            main_polygon_area=800.0,
            main_polygon_percentage=80.0,
            polygon_count=2,
            max_distance_between_polygons=15.0,
            separate_territories=territories,
        )

        assert result.country_name == "Test Country"
        assert result.geometry_type == CountryGeometryType.HAS_EXCLAVE
        assert result.total_area == 1000.0
        assert result.main_polygon_area == 800.0
        assert result.main_polygon_percentage == 80.0
        assert result.polygon_count == 2
        assert result.max_distance_between_polygons == 15.0
        assert len(result.separate_territories) == 2
        assert result.separate_territories[0]["area"] == 800.0
        assert result.separate_territories[1]["percentage"] == 20.0


class TestLoadCountryGeometry:
    """Test suite for the load_country_geometry function."""

    @patch("os.path.exists")
    def test_database_not_found(self, mock_exists: MagicMock) -> None:
        """Test that FileNotFoundError is raised when the database doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError, match="Database file not found"):
            load_country_geometry("Israel", "nonexistent.db")

    @patch("os.path.exists")
    @patch("sqlite3.connect")
    def test_country_not_found(
        self,
        mock_connect: MagicMock,
        mock_exists: MagicMock,
    ) -> None:
        """Test that ValueError is raised when the country isn't in the database."""
        mock_exists.return_value = True

        # Mock database connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Simulate country not found

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with pytest.raises(ValueError, match="Country 'NonexistentCountry' not found"):
            load_country_geometry("NonexistentCountry", "test.db")

    @patch("os.path.exists")
    @patch("sqlite3.connect")
    @patch("pandas.read_sql")
    @patch("shapely.wkb.loads")
    def test_successful_load_single_polygon(
        self,
        mock_loads: MagicMock,
        mock_read_sql: MagicMock,
        mock_connect: MagicMock,
        mock_exists: MagicMock,
    ) -> None:
        """Test successful loading of a country with a single polygon."""
        mock_exists.return_value = True

        # Mock database connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Create mock result with Israel as single polygon
        israel_polygon = Polygon([(34, 29), (34, 33), (36, 33), (36, 29)])
        mock_loads.return_value = israel_polygon

        # Create mock DataFrame
        from pandas import DataFrame

        mock_df = DataFrame(
            {
                "name": ["Israel"],
                "GEOMETRY": [b"mock_geometry"],
            }
        )
        mock_read_sql.return_value = mock_df

        # Call the function
        geometry = load_country_geometry("Israel", "test.db")

        # Verify the result
        assert geometry is not None
        assert isinstance(geometry, Polygon)
        assert geometry == israel_polygon


class TestTerritoryAnalyzer:
    """Test suite for the TerritoryAnalyzer class."""

    def test_init(self) -> None:
        """Test TerritoryAnalyzer initialization."""
        analyzer = TerritoryAnalyzer()
        assert analyzer.main_area_threshold == 0.8

        custom_analyzer = TerritoryAnalyzer(main_area_threshold=0.7)
        assert custom_analyzer.main_area_threshold == 0.7

    def test_analyze_single_polygon(self) -> None:
        """Test analysis of a country with a single polygon (Israel)."""
        # Create a simple polygon for Israel
        israel_polygon = Polygon([(34, 29), (34, 33), (36, 33), (36, 29)])

        analyzer = TerritoryAnalyzer()
        result = analyzer.analyze("Israel", israel_polygon)

        assert result.country_name == "Israel"
        assert result.geometry_type == CountryGeometryType.CONTINUOUS
        assert result.polygon_count == 1
        assert result.main_polygon_percentage == 100.0
        assert result.max_distance_between_polygons == 0.0
        assert len(result.separate_territories) == 1

    def test_analyze_with_exclave(self) -> None:
        """Test analysis of a country with an exclave (Russia with Kaliningrad)."""
        # Create a simple MultiPolygon for Russia with mainland and Kaliningrad
        russia_mainland = Polygon([(30, 50), (30, 70), (180, 70), (180, 50)])
        kaliningrad = Polygon([(19, 54), (19, 56), (23, 56), (23, 54)])
        russia_geometry = MultiPolygon([russia_mainland, kaliningrad])

        analyzer = TerritoryAnalyzer()
        result = analyzer.analyze("Russia", russia_geometry)

        assert result.country_name == "Russia"
        assert result.geometry_type == CountryGeometryType.HAS_EXCLAVE
        assert result.polygon_count == 2
        assert result.main_polygon_percentage > 90.0  # Mainland should be > 90%
        assert result.max_distance_between_polygons > 0.0
        assert len(result.separate_territories) == 2

    def test_analyze_island_nation(self) -> None:
        """Test analysis of an island nation (Indonesia)."""
        # Create several polygons representing Indonesian islands
        java = Polygon([(105, -8), (105, -6), (115, -6), (115, -8)])
        sumatra = Polygon([(95, -5), (95, 0), (105, 0), (105, -5)])
        borneo = Polygon([(109, -4), (109, 2), (119, 2), (119, -4)])
        sulawesi = Polygon([(118, -6), (118, 2), (125, 2), (125, -6)])
        papua = Polygon([(130, -9), (130, -2), (141, -2), (141, -9)])

        # Create MultiPolygon for Indonesia
        indonesia_geometry = MultiPolygon([java, sumatra, borneo, sulawesi, papua])

        analyzer = TerritoryAnalyzer()
        result = analyzer.analyze("Indonesia", indonesia_geometry)

        assert result.country_name == "Indonesia"
        assert result.geometry_type == CountryGeometryType.ISLAND_NATION
        assert result.polygon_count == 5
        assert result.main_polygon_percentage < 80.0  # No island should be > 80%
        assert result.max_distance_between_polygons > 0.0
        assert len(result.separate_territories) == 5

    def test_custom_threshold(self) -> None:
        """Test analysis with a custom main area threshold."""
        # Create a MultiPolygon with one large and one small polygon
        large = Polygon([(0, 0), (0, 10), (10, 10), (10, 0)])  # Area = 100
        small = Polygon([(20, 0), (20, 5), (25, 5), (25, 0)])  # Area = 25

        geometry = MultiPolygon([large, small])

        # With 0.8 threshold, should be HAS_EXCLAVE (large is 80% of total)
        analyzer_default = TerritoryAnalyzer()
        result_default = analyzer_default.analyze("TestCountry", geometry)
        assert result_default.geometry_type == CountryGeometryType.HAS_EXCLAVE

        # With 0.7 threshold, should be HAS_EXCLAVE (large is 80% of total)
        analyzer_70 = TerritoryAnalyzer(main_area_threshold=0.7)
        result_70 = analyzer_70.analyze("TestCountry", geometry)
        assert result_70.geometry_type == CountryGeometryType.HAS_EXCLAVE

        # With 0.9 threshold, should be ISLAND_NATION (large is not 90% of total)
        analyzer_90 = TerritoryAnalyzer(main_area_threshold=0.9)
        result_90 = analyzer_90.analyze("TestCountry", geometry)
        assert result_90.geometry_type == CountryGeometryType.ISLAND_NATION

    def test_analyze_with_db(self) -> None:
        """Test analyze_from_db method."""
        # Mock load_country_geometry
        with patch("maps.territory_analyzer.load_country_geometry") as mock_load:
            # Create a simple polygon for Israel
            israel_polygon = Polygon([(34, 29), (34, 33), (36, 33), (36, 29)])
            mock_load.return_value = israel_polygon

            analyzer = TerritoryAnalyzer()
            result = analyzer.analyze_from_db("Israel", "test.db")

            assert result.country_name == "Israel"
            assert result.geometry_type == CountryGeometryType.CONTINUOUS
            mock_load.assert_called_once_with("Israel", "test.db")
