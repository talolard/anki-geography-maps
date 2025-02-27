#!/usr/bin/env python
"""Script to draw a map of a country and its neighbors using Natural Earth data."""

import argparse
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import geopandas as gpd  # type: ignore
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.transforms import Bbox
from pandas import DataFrame
from shapely import wkb
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Point,
    Polygon,
    base,
)
from shapely.ops import unary_union
import numpy as np

# Import functionality from find_neighbors.py
from find_neighbors import (
    CountryName,
    DBPath,
    get_neighboring_countries,
)

# Custom types
ShapelyGeometry = Union[Point, Polygon, MultiPolygon, GeometryCollection, None]


@dataclass(frozen=True)
class MapColors:
    """Colors for different map elements."""

    target_country: str = "#FF5555"  # Red
    neighbor_countries: str = "#5555FF"  # Blue
    other_countries: str = "#DDDDDD"  # Light gray
    border_color: str = "#333333"  # Dark gray
    ocean_color: str = "#AADDFF"  # Light blue
    text_color: str = "#000000"  # Black


@dataclass(frozen=True)
class MapConfiguration:
    """Configuration for map rendering."""

    output_path: str
    title: str
    figsize: tuple[int, int] = (12, 10)
    dpi: int = 300
    colors: MapColors = MapColors()
    include_legend: bool = True
    target_percentage: float = (
        0.4  # Target country takes up 40% of the image by default
    )
    exclude_exclaves: bool = (
        True  # By default, exclude exclaves from map rendering and bounding box
    )
    main_area_threshold: float = (
        0.8  # Threshold for determining what is a main area vs exclave (80% by default)
    )


def load_country_data(
    country_name: CountryName,
    db_path: DBPath = "natural_earth_vector.sqlite",
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, list[str]]:
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
        df["geometry"] = df["GEOMETRY"].apply(
            lambda x: cast(ShapelyGeometry, wkb.loads(x) if x else None)
        )
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


def create_map(
    countries: gpd.GeoDataFrame,
    target_country: gpd.GeoDataFrame,
    neighbor_names: list[str],
    config: MapConfiguration,
) -> None:
    """
    Create a map visualization showing the target country and its neighbors.

    Args:
        countries: GeoDataFrame with all countries
        target_country: GeoDataFrame with just the target country
        neighbor_names: List of neighbor country names
        config: Map configuration settings
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=config.figsize)

    # Get target country geometry and centroid
    original_target_geometry = target_country.geometry.iloc[0]
    target_country_name = target_country.iloc[0]["name"]

    # If we need to exclude exclaves, filter the target country's geometry
    target_geometry = original_target_geometry
    filtered_neighbor_names = neighbor_names.copy()

    if config.exclude_exclaves and isinstance(original_target_geometry, MultiPolygon):
        # Get list of polygons sorted by area (largest first)
        polygons = list(original_target_geometry.geoms)
        areas = [p.area for p in polygons]
        total_area = sum(areas)

        # Sort polygons by area (largest first)
        sorted_idx = sorted(range(len(areas)), key=lambda i: areas[i], reverse=True)

        # Get the main polygon and calculate its percentage of total area
        main_polygon = polygons[sorted_idx[0]]
        main_polygon_pct = (main_polygon.area / total_area) * 100

        # If the main polygon is large enough, use only it for drawing and bounds
        if main_polygon_pct >= (config.main_area_threshold * 100):
            target_geometry = main_polygon
            print(
                f"Excluding exclaves: Using only main landmass ({main_polygon_pct:.2f}% of total area)"
            )

            # Also filter neighbors to only include those that border the main territory
            # First, get list of neighbors that actually border the main territory
            main_territory_neighbors = []

            # Create a temporary GeoDataFrame with just the main territory
            main_territory_gdf = gpd.GeoDataFrame(
                {"name": [target_country_name], "geometry": [main_polygon]},
                crs=target_country.crs,
            )

            # Check each neighbor to see if it borders the main territory
            for neighbor_name in neighbor_names:
                neighbor = countries[countries["name"] == neighbor_name]
                if len(neighbor) == 0:
                    continue

                neighbor_geom = neighbor.geometry.iloc[0]

                # Check if this neighbor touches the main territory
                if neighbor_geom.intersects(main_polygon) or neighbor_geom.touches(
                    main_polygon
                ):
                    main_territory_neighbors.append(neighbor_name)

            # If we found neighbors that only border exclaves, filter them out
            if len(main_territory_neighbors) < len(neighbor_names):
                excluded_neighbors = set(neighbor_names) - set(main_territory_neighbors)
                print(
                    f"Excluding neighbors that only border exclaves: {', '.join(excluded_neighbors)}"
                )
                filtered_neighbor_names = main_territory_neighbors

    # Identify neighbor countries (using filtered list if applicable)
    neighbor_countries = countries[countries["name"].isin(filtered_neighbor_names)]

    # Get centroid of the (possibly filtered) target geometry
    target_centroid = target_geometry.centroid

    # Calculate bounds for visualization
    # First, try to get bounds from the filtered geometry if applicable
    try:
        # Create a temp GeoDataFrame just for bounds calculation
        if target_geometry is not original_target_geometry:
            # Use just the filtered polygon for bounds
            bounds_data = {"name": [target_country_name], "geometry": [target_geometry]}
            bounds_gdf = gpd.GeoDataFrame(bounds_data, crs=target_country.crs)
            target_bounds = bounds_gdf.total_bounds
        else:
            target_bounds = target_country.total_bounds

        x_min, y_min, x_max, y_max = target_bounds

        # Ensure bounds are valid (not NaN or Inf)
        if not all(map(lambda x: np.isfinite(x), [x_min, y_min, x_max, y_max])):
            raise ValueError("Invalid bounds (NaN or Inf values detected)")

        # Ensure bounds have some width and height
        if x_max <= x_min or y_max <= y_min:
            raise ValueError("Invalid bounds (zero or negative width/height)")

        # Calculate center point of target country
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2

        # Calculate target country dimensions
        target_width = x_max - x_min
        target_height = y_max - y_min

        # Use the larger dimension to ensure we capture the whole country
        target_size = max(target_width, target_height)

        # Calculate target percentage to buffer conversion
        buffer_factor = (1 / config.target_percentage - 1) / 2
        target_buffer = target_size * buffer_factor

        # Set initial view bounds focused on target
        view_x_min = center_x - (target_size / 2) - target_buffer
        view_y_min = center_y - (target_size / 2) - target_buffer
        view_x_max = center_x + (target_size / 2) + target_buffer
        view_y_max = center_y + (target_size / 2) + target_buffer

        # Calculate final bounds dimensions
        view_width = view_x_max - view_x_min
        view_height = view_y_max - view_y_min

        # Ensure we maintain the aspect ratio from the figure
        aspect_ratio = config.figsize[0] / config.figsize[1]

        # Adjust bounds to match aspect ratio while keeping centered
        if (view_width / view_height) > aspect_ratio:
            # Too wide - need to increase height
            extra_height = (view_width / aspect_ratio) - view_height
            view_y_min -= extra_height / 2
            view_y_max += extra_height / 2
        else:
            # Too tall - need to increase width
            extra_width = (view_height * aspect_ratio) - view_width
            view_x_min -= extra_width / 2
            view_x_max += extra_width / 2

        # Final bounds
        bounds = [view_x_min, view_y_min, view_x_max, view_y_max]

    except Exception as e:
        print(f"Error calculating bounds from filtered geometry: {e}")
        print("Falling back to using the original geometry for bounds calculation")

        # Fallback to using the original geometry for bounds
        target_bounds = target_country.total_bounds
        x_min, y_min, x_max, y_max = target_bounds

        # Calculate center point of target country
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2

        # Calculate target country dimensions
        target_width = x_max - x_min
        target_height = y_max - y_min

        # Use the larger dimension to ensure we capture the whole country
        target_size = max(target_width, target_height)

        # Calculate target percentage to buffer conversion
        buffer_factor = (1 / config.target_percentage - 1) / 2
        target_buffer = target_size * buffer_factor

        # Set initial view bounds focused on target
        view_x_min = center_x - (target_size / 2) - target_buffer
        view_y_min = center_y - (target_size / 2) - target_buffer
        view_x_max = center_x + (target_size / 2) + target_buffer
        view_y_max = center_y + (target_size / 2) + target_buffer

        # Calculate final bounds dimensions
        view_width = view_x_max - view_x_min
        view_height = view_y_max - view_y_min

        # Ensure we maintain the aspect ratio from the figure
        aspect_ratio = config.figsize[0] / config.figsize[1]

        # Adjust bounds to match aspect ratio while keeping centered
        if (view_width / view_height) > aspect_ratio:
            # Too wide - need to increase height
            extra_height = (view_width / aspect_ratio) - view_height
            view_y_min -= extra_height / 2
            view_y_max += extra_height / 2
        else:
            # Too tall - need to increase width
            extra_width = (view_height * aspect_ratio) - view_width
            view_x_min -= extra_width / 2
            view_x_max += extra_width / 2

        # Final bounds
        bounds = [view_x_min, view_y_min, view_x_max, view_y_max]

    # Set ocean background color
    ax.set_facecolor(config.colors.ocean_color)

    # Plot neighbor countries
    neighbor_countries.plot(
        ax=ax,
        color=config.colors.neighbor_countries,
        edgecolor=config.colors.border_color,
        linewidth=0.8,
    )

    # Plot target country on top (always use original geometry for display)
    target_country.plot(
        ax=ax,
        color=config.colors.target_country,
        edgecolor=config.colors.border_color,
        linewidth=1.0,
    )

    # Add country label for target country
    plt.text(
        target_centroid.x,
        target_centroid.y,
        target_country.iloc[0]["name"],
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        color="white",
        bbox=dict(
            facecolor=config.colors.target_country, alpha=0.7, boxstyle="round,pad=0.3"
        ),
    )

    # Add labels for neighbor countries
    for idx, row in neighbor_countries.iterrows():
        centroid = row.geometry.centroid
        plt.text(
            centroid.x,
            centroid.y,
            f"{row['name']} ({row['display_iso']})",
            fontsize=10,
            ha="center",
            va="center",
            color="white",
            bbox=dict(
                facecolor=config.colors.neighbor_countries,
                alpha=0.7,
                boxstyle="round,pad=0.2",
            ),
        )

    # Set map bounds
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])

    # Remove axis ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])

    # Add title
    plt.title(config.title, fontsize=14, fontweight="bold")

    # Add legend if requested
    if config.include_legend:
        legend_elements = [
            Patch(
                facecolor=config.colors.target_country,
                edgecolor=config.colors.border_color,
                label=f"Target: {target_country.iloc[0]['name']}",
            ),
            Patch(
                facecolor=config.colors.neighbor_countries,
                edgecolor=config.colors.border_color,
                label=f"Neighbors ({len(filtered_neighbor_names)})",
            ),
        ]
        ax.legend(handles=legend_elements, loc="lower left")

    # Save the figure
    plt.savefig(config.output_path, dpi=config.dpi, bbox_inches="tight")
    plt.close(fig)

    print(f"Map saved to {config.output_path}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Create a map visualization of a country and its neighbors",
    )
    parser.add_argument(
        "country",
        type=str,
        help="Name of the country to visualize",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output path for the map image (default: /tmp/<country_name>.png)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="natural_earth_vector.sqlite",
        help="Path to the Natural Earth SQLite database",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution of the output image (default: 300)",
    )
    parser.add_argument(
        "--target-percentage",
        type=float,
        default=0.4,
        help="Percentage of the image the target country should occupy (default: 0.4 or 40%%)",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to coordinate the program execution."""
    args: argparse.Namespace = parse_args()

    country_name: str = args.country
    db_path: str = args.db_path

    # Set output path
    output_path: str = (
        args.output or f"/tmp/{country_name.lower().replace(' ', '_')}.png"
    )

    try:
        # Load country data
        countries, target_country, neighbor_names = load_country_data(
            country_name, db_path
        )

        # Create map configuration
        config = MapConfiguration(
            output_path=output_path,
            title=f"{country_name} and Its Neighbors",
            dpi=args.dpi,
            target_percentage=args.target_percentage,
        )

        # Generate the map
        create_map(countries, target_country, neighbor_names, config)

        # Report success
        print(
            f"Successfully created map for {country_name} with {len(neighbor_names)} neighbors"
        )
        print(f"Map saved to: {output_path}")

    except Exception as e:
        print(f"Error creating map: {e}")
        return


if __name__ == "__main__":
    main()
