#!/usr/bin/env python
"""Script to draw a map of a country and its neighbors using Natural Earth data."""

import argparse
import os
import sqlite3
from dataclasses import dataclass

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
from pandas import DataFrame
from shapely import wkb

# Import functionality from find_neighbors.py
from find_neighbors import (
    CountryName,
    DBPath,
    get_neighboring_countries,
)


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
        df["geometry"] = df["GEOMETRY"].apply(lambda x: wkb.loads(x) if x else None) 
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

    # Identify neighbor countries
    neighbor_countries = countries[countries["name"].isin(neighbor_names)]

    # Get target country geometry and centroid
    target_geometry = target_country.geometry.iloc[0]
    target_centroid = target_geometry.centroid

    # Calculate bounds based on target country
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
    # If we want the target to take up target_percentage (e.g., 0.4 or 40%) of the image,
    # then the buffer should scale the view inversely
    # Buffer factor is calculated as: (1/target_percentage - 1) / 2
    # For example, if target_percentage = 0.4:
    # buffer_factor = (1/0.4 - 1) / 2 = (2.5 - 1) / 2 = 0.75
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

    # Plot target country on top
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
                label=f"Neighbors ({len(neighbor_names)})",
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
