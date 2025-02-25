"""Shared test fixtures for the maps package."""

import os
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

# Constants for testing
TEST_DB_PATH = "test_natural_earth_vector.sqlite"


@pytest.fixture(scope="session")
def sample_polygons() -> dict[str, Polygon]:
    """Provide sample polygons for testing."""
    return {
        "germany": Polygon([(10, 50), (10, 55), (15, 55), (15, 50)]),
        "france": Polygon([(5, 45), (5, 50), (10, 50), (10, 45)]),
        "poland": Polygon([(15, 50), (15, 55), (20, 55), (20, 50)]),
        "belgium": Polygon([(8, 48), (8, 52), (12, 52), (12, 48)]),
        "netherlands": Polygon([(6, 50), (6, 54), (9, 54), (9, 50)]),
    }


@pytest.fixture
def mock_database_exists() -> Generator[MagicMock, None, None]:
    """Mock os.path.exists to return True for the test database."""
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


@pytest.fixture
def mock_db_connection() -> Generator[MagicMock, None, None]:
    """Mock sqlite3.connect to return a mock connection."""
    with patch("sqlite3.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        yield mock_connect


@pytest.fixture
def sample_countries_dataframe(sample_polygons: dict[str, Polygon]) -> pd.DataFrame:
    """Create a sample countries DataFrame for testing."""
    return pd.DataFrame({
        "name": ["Germany", "France", "Poland", "Belgium", "Netherlands"],
        "name_long": [
            "Federal Republic of Germany",
            "French Republic",
            "Republic of Poland",
            "Kingdom of Belgium",
            "Kingdom of the Netherlands",
        ],
        "iso_a3": ["DEU", "FRA", "POL", "BEL", "NLD"],
        "GEOMETRY": [b"geom1", b"geom2", b"geom3", b"geom4", b"geom5"],
    })


@pytest.fixture
def sample_countries_geodataframe(sample_polygons: dict[str, Polygon]) -> gpd.GeoDataFrame:
    """Create a sample countries GeoDataFrame for testing."""
    return gpd.GeoDataFrame({
        "name": ["Germany", "France", "Poland", "Belgium", "Netherlands"],
        "name_long": [
            "Federal Republic of Germany",
            "French Republic",
            "Republic of Poland",
            "Kingdom of Belgium",
            "Kingdom of the Netherlands",
        ],
        "iso_a3": ["DEU", "FRA", "POL", "BEL", "NLD"],
        "display_iso": ["DEU", "FRA", "POL", "BEL", "NLD"],
        "geometry": [
            sample_polygons["germany"],
            sample_polygons["france"],
            sample_polygons["poland"],
            sample_polygons["belgium"],
            sample_polygons["netherlands"],
        ],
    })


@pytest.fixture
def sample_neighbors_result() -> list[tuple[str, str]]:
    """Provide sample neighbor results for testing."""
    return [
        ("France", "FRA"),
        ("Poland", "POL"),
        ("Belgium", "BEL"),
        ("Netherlands", "NLD"),
    ]


@pytest.fixture
def mock_matplotlib() -> Generator[dict[str, MagicMock], None, None]:
    """Mock matplotlib.pyplot to avoid actual plotting."""
    mocks = {}
    
    with patch("matplotlib.pyplot.subplots") as mock_subplots:
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        mocks["subplots"] = mock_subplots
        mocks["fig"] = mock_fig
        mocks["ax"] = mock_ax
        
        with patch("matplotlib.pyplot.savefig") as mock_savefig:
            mocks["savefig"] = mock_savefig
            
            with patch("matplotlib.pyplot.close") as mock_close:
                mocks["close"] = mock_close
                
                with patch("matplotlib.pyplot.text") as mock_text:
                    mocks["text"] = mock_text
                    
                    with patch("matplotlib.pyplot.title") as mock_title:
                        mocks["title"] = mock_title
                        yield mocks 