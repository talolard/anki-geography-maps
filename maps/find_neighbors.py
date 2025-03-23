#!/usr/bin/env python
"""Script to find neighboring countries using Natural Earth data."""

import argparse
import os
import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Union, cast

import geopandas as gpd
import pandas as pd
from pandas import DataFrame
from shapely import wkb
from shapely.geometry.base import BaseGeometry


# Custom types
@dataclass(frozen=True)
class CountryRecord:
    """Represents a country record with essential information."""

    name: str
    name_long: str
    iso_code: str

    @property
    def display_iso(self) -> str:
        """Return formatted ISO code, showing N/A for missing values."""
        return "N/A" if self.iso_code == "-99" or not self.iso_code else self.iso_code


# Type aliases
CountryName = str
DBPath = str
NeighborsList = list[tuple[str, str]]  # List of (name, iso_code) tuples
ErrorMessage = str
CountryList = list[CountryRecord]
NeighborsResult = Union[NeighborsList, ErrorMessage]


def list_country_names(
    db_path: DBPath = "natural_earth_vector.sqlite", limit: Optional[int] = 20
) -> List[List[str]]:
    """
    List all country names in the database.

    Args:
        db_path: Path to the Natural Earth SQLite database
        limit: Maximum number of countries to return (defaults to 20, use None for all)

    Returns:
        A sorted list of country names, long names, and ISO codes
    """
    try:
        # Connect to the SQLite database
        conn: sqlite3.Connection = sqlite3.connect(db_path)

        # Query country names
        query: str = (
            "SELECT name, name_long, iso_a3 FROM ne_10m_admin_0_countries ORDER BY name"
        )
        df: DataFrame = pd.read_sql(query, conn)

        # Return the sorted list of names, limited if specified
        result: List[List[str]] = (
            df[["name", "name_long", "iso_a3"]].to_numpy().tolist()
        )
        if limit is not None:
            return result[:limit]
        else:
            return result
    except Exception as e:
        print(f"Error listing countries: {e!s}")
        return cast(List[List[str]], [])
    finally:
        if "conn" in locals():
            conn.close()


def get_countries_df(
    db_path: DBPath, cache_path: str = "countries_df.parquet"
) -> DataFrame:
    """
    Load countries DataFrame from SQLite database or cached parquet file.

    Args:
        db_path: Path to the Natural Earth SQLite database
        cache_path: Path to save/load cached DataFrame

    Returns:
        DataFrame containing country data with shapely geometries
    """
    # Try loading from cache first
    if os.path.exists(cache_path):
        print("Loading countries from cache...")
        df = pd.read_parquet(cache_path)
        # Convert the cached WKB geometry strings back to shapely objects
        df["geometry"] = df["geometry"].apply(wkb.loads)
        return df

    print("Loading countries from database...")
    # Connect to the SQLite database
    conn: sqlite3.Connection = sqlite3.connect(db_path)

    # Load countries as a DataFrame using pandas
    query: str = "SELECT ogc_fid, name, name_long, iso_a3, GEOMETRY FROM ne_10m_admin_0_countries"
    print(f"Executing query: {query}")

    df: DataFrame = pd.read_sql(query, conn)
    print(f"Loaded {len(df)} countries")

    # Convert the BLOB geometry to shapely geometries
    print("Converting BLOB geometries to shapely objects...")
    df["geometry"] = df["GEOMETRY"].apply(lambda x: wkb.loads(x) if x else None)
    df = df.drop("GEOMETRY", axis=1)

    # Fix missing ISO codes
    df["display_iso"] = df["iso_a3"].apply(
        lambda x: "N/A" if x == "-99" or not x else x
    )

    # Cache the DataFrame
    # Convert geometries to WKB for storage
    df_to_cache = df.copy()
    df_to_cache["geometry"] = df_to_cache["geometry"].apply(
        lambda x: x.wkb if x else None
    )
    df_to_cache.to_parquet(cache_path)

    conn.close()
    return df


def get_neighboring_countries(
    country_name: CountryName,
    db_path: DBPath = "natural_earth_vector.sqlite",
) -> NeighborsResult:
    """Get all neighboring countries for a given country."""
    print(f"Looking for neighbors of {country_name}...")

    # Verify database exists
    if not os.path.exists(db_path):
        return f"Database file not found: {db_path}"

    try:
        # Load countries DataFrame
        df = get_countries_df(db_path)

        # Convert to GeoDataFrame
        countries: gpd.GeoDataFrame = gpd.GeoDataFrame(df, geometry="geometry")

        # Set coordinate reference system (CRS)
        countries.crs = "EPSG:4326"
        # Set coordinate reference system (CRS)
        countries.crs = "EPSG:4326"

        # Get the target country
        target_country: gpd.GeoDataFrame = countries[countries["name"] == country_name]

        if len(target_country) == 0:
            # Print a sample of country names to help debug
            sample_countries: list[str] = (
                countries["name"].sample(min(10, len(countries))).tolist()
            )
            print(f"Sample of available country names: {sample_countries}")
            return f"Country '{country_name}' not found"

        print(
            f"Found target country: {target_country.iloc[0]['name']} ({target_country.iloc[0]['display_iso']})"
        )

        # Find all countries that touch the target country
        print("Finding neighbors...")
        target_geometry: BaseGeometry = target_country.iloc[0].geometry
        neighbors: gpd.GeoDataFrame = countries[
            countries.geometry.touches(target_geometry)
        ]

        if len(neighbors) == 0:
            print("No neighbors found using 'touches'. Trying with buffer...")
            # If no neighbors found, try with a small buffer to account for precision issues
            target_geom: BaseGeometry = target_country.iloc[0].geometry
            buffered: BaseGeometry = target_geom.buffer(0.01)  # ~1km buffer
            neighbors = countries[
                (countries["ogc_fid"] != target_country.iloc[0]["ogc_fid"])
                & (countries.geometry.intersects(buffered))
                & ~(countries.geometry.covers(target_geom))
            ]

        # Return the names and ISO codes of neighboring countries
        result: NeighborsList = [
            (str(row["name"]), str(row["display_iso"]))
            for idx, row in neighbors.iterrows()
        ]
        print(f"Found {len(result)} neighbors")
        return result

    except Exception as e:
        print(f"Error: {e!s}")
        return f"Error: {e!s}"
    finally:
        if "conn" in locals():
            conn.close()  # type: ignore # noqa: F821


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Find neighboring countries using Natural Earth data",
    )
    parser.add_argument(
        "country",
        nargs="?",
        default="Germany",
        help="Name of the country to find neighbors for (default: Germany)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List sample country names available in the database",
    )
    parser.add_argument(
        "--list-all",
        action="store_true",
        help="List all country names available in the database",
    )
    return parser.parse_args()


def format_iso_code(iso_code: str) -> str:
    """
    Format ISO code for display, showing N/A for missing values.

    Args:
        iso_code: ISO code to format

    Returns:
        Formatted ISO code
    """
    return "N/A" if iso_code == "-99" or not iso_code else iso_code


def main() -> None:
    """Main function to coordinate the program execution."""
    args: argparse.Namespace = parse_args()

    # If --list or --list-all flag is provided, show country names and exit
    if args.list or args.list_all:
        print("\nCountries in the database:")
        country_list: list[list[str]] = list_country_names(
            limit=None if args.list_all else 20
        )
        for name, long_name, iso in country_list:
            iso_display_val: str = format_iso_code(iso)
            print(f"- {name} ({iso_display_val})")
        exit(0)

    # Find neighbors for the specified country
    country: str = args.country
    neighbors: NeighborsResult = get_neighboring_countries(country)

    if isinstance(neighbors, str):
        # Error message
        print(f"\n{neighbors}\n")
    else:
        print(f"\n{country}'s neighbors:")
        for name, iso_code in sorted(neighbors):
            print(f"- {name} ({iso_code})")
        print()

    # Show sample of countries in the database if no neighbors were found
    if isinstance(neighbors, str):
        print("\nSample of countries in the database (first 20):")
        sample_countries: list[list[str]] = list_country_names(limit=20)
        for name, long_name, iso in sample_countries:
            sample_iso_display: str = format_iso_code(iso)
            print(f"- {name} ({sample_iso_display})")


if __name__ == "__main__":
    main()
