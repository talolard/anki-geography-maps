#!/usr/bin/env python
"""
Module for analyzing country territories to determine their geometric characteristics.

This module provides functionality to analyze country geometries from the Natural Earth
database and classify them based on their geometric characteristics:
- Continuous: A country with a single continuous landmass
- Island nation: A country composed of multiple significant islands
- Has exclave: A country with a main landmass and one or more separate territories

Examples include:
- Israel: Continuous landmass
- Russia: Has exclave (Kaliningrad)
- Indonesia: Island nation
"""

import os
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Union, cast

import numpy as np
import shapely.wkb as wkb
from shapely.geometry import MultiPolygon, Polygon

# Type aliases
CountryName = str
DBPath = str
GeometryType = Union[Polygon, MultiPolygon]
TerritoryInfo = Dict[str, Any]


class CountryGeometryType(Enum):
    """Enum representing different types of country geometries."""

    CONTINUOUS = "continuous"
    ISLAND_NATION = "island_nation"
    HAS_EXCLAVE = "has_exclave"


@dataclass
class TerritoryAnalysisResult:
    """
    Class to hold the results of territory analysis.

    Attributes:
        country_name: Name of the analyzed country
        geometry_type: Classification of the country's geometry (continuous, island nation, etc.)
        total_area: Total area of all country polygons
        main_polygon_area: Area of the largest polygon
        main_polygon_percentage: Percentage of total area covered by the largest polygon
        polygon_count: Number of separate polygons
        max_distance_between_polygons: Maximum distance between any two polygons
        separate_territories: List of dictionaries containing information about each territory
    """

    country_name: str
    geometry_type: CountryGeometryType
    total_area: float
    main_polygon_area: float = field(
        default=0.0
    )  # Default value needed for type checking
    main_polygon_percentage: float = field(default=100.0)
    polygon_count: int = field(default=1)
    max_distance_between_polygons: float = field(default=0.0)
    separate_territories: List[TerritoryInfo] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize dependent fields after instance creation."""
        # If main_polygon_area is 0.0 (default), use total_area
        if self.main_polygon_area == 0.0:
            self.main_polygon_area = self.total_area


def load_country_geometry(
    country_name: CountryName,
    db_path: DBPath = "natural_earth_vector.sqlite",
) -> GeometryType:
    """
    Load a country's geometry from the Natural Earth database.

    Args:
        country_name: Name of the country to load
        db_path: Path to the Natural Earth SQLite database

    Returns:
        Shapely geometry (Polygon or MultiPolygon) representing the country

    Raises:
        FileNotFoundError: If the database file doesn't exist
        ValueError: If the country isn't found in the database
        TypeError: If the geometry is not a Polygon or MultiPolygon
    """
    # Verify database exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query with parameter
        cursor.execute(
            "SELECT GEOMETRY FROM ne_10m_admin_0_countries WHERE name = ?",
            (country_name,),
        )

        # Fetch the result
        result = cursor.fetchone()

        # Check if country was found
        if result is None:
            raise ValueError(f"Country '{country_name}' not found in the database")

        # Convert the BLOB geometry to shapely geometry
        geometry = wkb.loads(result[0])

        # Ensure the geometry is of the expected type
        if not isinstance(geometry, (Polygon, MultiPolygon)):
            raise TypeError(
                f"Expected Polygon or MultiPolygon, got {type(geometry).__name__}"
            )

        return cast(GeometryType, geometry)

    finally:
        if conn is not None:
            conn.close()


class TerritoryAnalyzer:
    """
    Class for analyzing country territories and classifying them based on geometric characteristics.

    This analyzer can identify:
    - Continuous countries: Single landmass or where one landmass represents most of the area
    - Island nations: Multiple significant islands with no dominant landmass
    - Countries with exclaves: Countries with a main landmass and one or more separate territories

    The classification is based on the proportion of the largest polygon's area to total area
    and the distances between polygons.
    """

    def __init__(self, main_area_threshold: float = 0.8) -> None:
        """
        Initialize the TerritoryAnalyzer.

        Args:
            main_area_threshold: Threshold for determining if a polygon is dominant.
                                 Default is 0.8 (80% of total area)
        """
        self.main_area_threshold = main_area_threshold

    def analyze(
        self, country_name: str, geometry: GeometryType
    ) -> TerritoryAnalysisResult:
        """
        Analyze a country's geometry and classify it.

        Args:
            country_name: Name of the country
            geometry: Shapely geometry (Polygon or MultiPolygon) of the country

        Returns:
            TerritoryAnalysisResult with analysis data
        """
        # Handle single polygon case
        if isinstance(geometry, Polygon):
            area = geometry.area
            return TerritoryAnalysisResult(
                country_name=country_name,
                geometry_type=CountryGeometryType.CONTINUOUS,
                total_area=area,
                main_polygon_area=area,
                main_polygon_percentage=100.0,
                polygon_count=1,
                max_distance_between_polygons=0.0,
                separate_territories=[
                    {
                        "area": area,
                        "percentage": 100.0,
                        "centroid": (geometry.centroid.x, geometry.centroid.y),
                    }
                ],
            )

        # For MultiPolygon case
        polygons = list(geometry.geoms)
        polygon_count = len(polygons)

        # Calculate areas and sort polygons by area (largest first)
        areas = [p.area for p in polygons]
        total_area = sum(areas)
        sorted_indices = np.argsort(areas)[::-1]  # Descending order

        # Get the main polygon (largest by area)
        main_polygon = polygons[sorted_indices[0]]
        main_polygon_area = main_polygon.area
        main_polygon_percentage = (main_polygon_area / total_area) * 100.0

        # Calculate territory information
        territories: List[TerritoryInfo] = []
        for i in sorted_indices:
            polygon = polygons[i]
            area = polygon.area
            percentage = (area / total_area) * 100.0
            centroid = polygon.centroid

            territories.append(
                {
                    "area": area,
                    "percentage": percentage,
                    "centroid": (centroid.x, centroid.y),
                }
            )

        # Calculate maximum distance between polygons
        max_distance = 0.0
        if polygon_count > 1:
            for i in range(polygon_count):
                for j in range(i + 1, polygon_count):
                    # Use distance between centroids for simplicity and efficiency
                    # More sophisticated approaches would use the actual minimum distance between polygons
                    p1_centroid = polygons[i].centroid
                    p2_centroid = polygons[j].centroid
                    distance = p1_centroid.distance(p2_centroid)
                    max_distance = max(max_distance, distance)

        # Determine geometry type
        geometry_type: CountryGeometryType
        if polygon_count == 1:
            geometry_type = CountryGeometryType.CONTINUOUS
        elif main_polygon_percentage >= (self.main_area_threshold * 100):
            # If the main landmass is significant (e.g. >80% of area)
            geometry_type = CountryGeometryType.HAS_EXCLAVE
        else:
            # If no single landmass is dominant (like an island nation)
            geometry_type = CountryGeometryType.ISLAND_NATION

        # Create and return result
        return TerritoryAnalysisResult(
            country_name=country_name,
            geometry_type=geometry_type,
            total_area=total_area,
            main_polygon_area=main_polygon_area,
            main_polygon_percentage=main_polygon_percentage,
            polygon_count=polygon_count,
            max_distance_between_polygons=max_distance,
            separate_territories=territories,
        )

    def analyze_from_db(
        self, country_name: str, db_path: str = "natural_earth_vector.sqlite"
    ) -> TerritoryAnalysisResult:
        """
        Load a country's geometry from the database and analyze it.

        Args:
            country_name: Name of the country to analyze
            db_path: Path to the Natural Earth SQLite database

        Returns:
            TerritoryAnalysisResult with analysis data
        """
        geometry = load_country_geometry(country_name, db_path)
        return self.analyze(country_name, geometry)


def get_country_territory_info(
    country_name: str,
    db_path: str = "natural_earth_vector.sqlite",
    threshold: float = 0.8,
) -> dict:
    """
    Analyze a country's territory and return a dictionary with territory information.

    This function can be used to enhance maps with additional information about
    country territory types.

    Args:
        country_name: Name of the country to analyze
        db_path: Path to the Natural Earth SQLite database
        threshold: Threshold for determining if a polygon is dominant (default: 0.8)

    Returns:
        Dictionary with territory information including:
        - territory_type: 'continuous', 'island_nation', or 'has_exclave'
        - polygon_count: Number of separate polygons
        - main_area_percentage: Percentage of total area covered by the largest polygon
        - has_exclaves: Boolean indicating if the country has exclaves
        - is_island_nation: Boolean indicating if the country is an island nation
        - max_distance: Maximum distance between any two polygons
    """
    analyzer = TerritoryAnalyzer(main_area_threshold=threshold)
    result = analyzer.analyze_from_db(country_name, db_path)

    territory_info = {
        "territory_type": result.geometry_type.value,
        "polygon_count": result.polygon_count,
        "main_area_percentage": result.main_polygon_percentage,
        "has_exclaves": result.geometry_type == CountryGeometryType.HAS_EXCLAVE,
        "is_island_nation": result.geometry_type == CountryGeometryType.ISLAND_NATION,
        "max_distance": result.max_distance_between_polygons,
        "territories": [
            {
                "area": t["area"],
                "percentage": t["percentage"],
                "coordinates": t["centroid"],
            }
            for t in result.separate_territories
        ],
    }

    return territory_info


def add_territory_info_to_map_config(
    map_config: dict, country_name: str, db_path: str = "natural_earth_vector.sqlite"
) -> dict:
    """
    Add territory information to a map configuration dictionary.

    This function is designed to integrate with draw_map.py by enhancing
    the map configuration with territory information.

    Args:
        map_config: Dictionary containing map configuration
        country_name: Name of the country to analyze
        db_path: Path to the Natural Earth SQLite database

    Returns:
        Updated map configuration dictionary with territory information
    """
    territory_info = get_country_territory_info(country_name, db_path)

    # Create a deep copy to avoid modifying the original
    import copy

    config = copy.deepcopy(map_config)

    # Add territory information
    config["territory_info"] = territory_info

    # Add custom title based on territory type
    territory_type = territory_info["territory_type"]
    base_title = config.get("title", f"{country_name}")

    if territory_type == "continuous":
        config["title"] = f"{base_title} (Continuous Territory)"
    elif territory_type == "island_nation":
        config["title"] = f"{base_title} (Island Nation)"
    elif territory_type == "has_exclave":
        config["title"] = f"{base_title} (With Exclaves)"

    return config
