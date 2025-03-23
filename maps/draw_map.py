#!/usr/bin/env python
"""Script to draw a map of a country and its neighbors using Natural Earth data."""

import os
import sqlite3
from typing import Any, List, Optional, Tuple

import geopandas as gpd  # type: ignore
import pandas as pd
from pandas import DataFrame
from shapely import wkb

# Import functionality from find_neighbors.py
from maps.find_neighbors import (
    CountryName,
    DBPath,
    get_neighboring_countries,
)

# Import from our refactored code
from maps.models import ShapelyGeometry

# Use the module-level imported functions for backward compatibility with tests


# We need to provide our own version of load_country_data for the tests
def load_country_data(
    country_name: CountryName,
    db_path: DBPath = "natural_earth_vector.sqlite",
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, List[str]]:
    """
    Load country data from Natural Earth database.

    Args:
        country_name: Name of the target country
        db_path: Path to the database file

    Returns:
        Tuple containing:
            - GeoDataFrame with all countries
            - GeoDataFrame with just the target country
            - List of neighbor country names
    """
    # Verify database exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # Get neighboring countries
    neighbors_result = get_neighboring_countries(country_name, db_path)

    if isinstance(neighbors_result, str):
        # If we got an error message
        raise ValueError(f"Error finding neighbors: {neighbors_result}")

    neighbor_names: list[str] = [name for name, _ in neighbors_result]

    try:
        # Connect to the SQLite database
        query: str = "SELECT name, iso_a3, GEOMETRY FROM ne_10m_admin_0_countries"

        conn: sqlite3.Connection = sqlite3.connect(db_path)

        # Load all countries with geometries
        df: DataFrame = pd.read_sql(query, conn)

        # Convert the BLOB geometry to shapely geometries
        def convert_geometry(blob: Any) -> Optional[ShapelyGeometry]:
            if blob is None:
                return None
            try:
                return wkb.loads(blob)
            except Exception:
                return None

        df["geometry"] = df["GEOMETRY"].apply(convert_geometry)  # type: ignore
        df = df.drop("GEOMETRY", axis=1)

        # Convert to GeoDataFrame
        countries: gpd.GeoDataFrame = gpd.GeoDataFrame(df, geometry="geometry")
        countries.crs = "EPSG:4326"  # Set coordinate reference system

        # Fix missing ISO codes
        countries["display_iso"] = countries["iso_a3"].apply(
            lambda x: "N/A" if x == "-99" or not x else x,
        )

        # Get the target country
        target_country: gpd.GeoDataFrame = countries[countries["name"] == country_name]

        if len(target_country) == 0:
            sample_countries: list[str] = (
                countries["name"].sample(min(10, len(countries))).tolist()
            )
            raise ValueError(
                f"Country '{country_name}' not found. Sample countries: {', '.join(sample_countries)}",
            )

        return countries, target_country, neighbor_names

    finally:
        if "conn" in locals():
            conn.close()
