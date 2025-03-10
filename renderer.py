#!/usr/bin/env python
"""
Renderer module for the maps package.

This module provides functionality for rendering maps of countries and their neighbors
using matplotlib and geopandas.
"""

from typing import List, Tuple, Optional, Dict, Any, cast
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import box, MultiPolygon, Polygon, Point
import numpy as np
import math

from models import MapConfiguration, ShapelyGeometry


def create_map(
    countries: gpd.GeoDataFrame,
    target_country: gpd.GeoDataFrame,
    neighbor_names: List[str],
    config: MapConfiguration,
) -> None:
    """
    Create a map of a country and its neighbors.

    This function generates a map highlighting the target country and its neighbors,
    and saves it to the specified output path. The map view is forced to be square
    regardless of the figure's dimensions.

    Args:
        countries: GeoDataFrame containing all countries
        target_country: GeoDataFrame containing only the target country
        neighbor_names: List of names of neighboring countries
        config: Configuration for the map

    Returns:
        None. The map is saved to the path specified in config.output_path
    """
    # Create a new figure
    fig, ax = plt.subplots(figsize=config.figsize)

    # Set the title
    ax.set_title(config.title, fontsize=14, fontweight="bold")

    # Get the target country geometry
    target_geom = target_country.geometry.iloc[0]

    # Handle exclaves if requested
    if config.exclude_exclaves and isinstance(target_geom, MultiPolygon):
        # Find the largest polygon (main territory)
        main_territory = max(target_geom.geoms, key=lambda p: p.area)
        # Create a new geometry with just the main territory
        target_geom = main_territory

    # Calculate the bounding box of the target geometry
    bounds = target_geom.bounds  # (minx, miny, maxx, maxy)
    target_width = bounds[2] - bounds[0]
    target_height = bounds[3] - bounds[1]

    # Force a square aspect ratio for the map view
    # Use the larger dimension to ensure the entire target country is visible
    target_size = max(target_width, target_height)

    # Calculate the center point of the target country
    center_x = (bounds[0] + bounds[2]) / 2
    center_y = (bounds[1] + bounds[3]) / 2

    # Determine the scaling factor to achieve the desired target percentage
    # For a square view, the target percentage is based on area
    # If target should occupy 30% of the area, the side length ratio is sqrt(0.3)
    scale_factor = 1.0 / math.sqrt(config.target_percentage)

    # Calculate the total size needed
    total_size = target_size * scale_factor

    # Calculate the buffer needed on each side to center the target
    buffer_x = (total_size - target_width) / 2
    buffer_y = (total_size - target_height) / 2

    # Create the new bounds with buffer, ensuring a square aspect ratio
    new_bounds = (
        center_x - total_size / 2,  # left
        center_y - total_size / 2,  # bottom
        center_x + total_size / 2,  # right
        center_y + total_size / 2,  # top
    )

    # Create a mask for the map view
    view_box = box(*new_bounds)

    # Create a copy of the countries GeoDataFrame to avoid modifying the original
    countries_copy = countries.copy()

    # Add a column to identify country types
    countries_copy["country_type"] = "other"
    countries_copy.loc[countries_copy["name"].isin(neighbor_names), "country_type"] = (
        "neighbor"
    )
    countries_copy.loc[
        countries_copy["name"] == target_country["name"].iloc[0], "country_type"
    ] = "target"

    # Create a color mapping
    color_mapping = {
        "target": config.colors.target_color,
        "neighbor": config.colors.neighbor_color,
        "other": config.colors.other_color,
    }

    # Plot the countries
    countries_copy.plot(
        ax=ax,
        color=countries_copy["country_type"].map(color_mapping),
        edgecolor=config.colors.border_color,
        linewidth=config.border_width,
    )

    # Set the background color (ocean)
    ax.set_facecolor(config.colors.ocean_color)

    # Set the map extent to our calculated view
    ax.set_xlim((new_bounds[0], new_bounds[2]))
    ax.set_ylim((new_bounds[1], new_bounds[3]))

    # Force the aspect ratio to be equal (square)
    ax.set_aspect("equal")

    # Add country labels if requested
    if config.show_labels:
        # Get countries in the view
        countries_in_view = countries_copy[countries_copy.geometry.intersects(view_box)]

        # Add labels for countries in view
        for idx, country in countries_in_view.iterrows():
            # Skip countries with no geometry
            if country.geometry is None:
                continue

            # Find a suitable label position
            # Try to use the centroid first
            centroid = country.geometry.centroid

            # Check if the centroid is within the country's geometry
            # If not, try to find a point within the geometry
            if not country.geometry.contains(centroid):
                # Try to use a point on the surface that's guaranteed to be within the geometry
                try:
                    # Get a point that's guaranteed to be within the geometry
                    point_within = country.geometry.representative_point()
                    centroid = point_within
                except Exception:
                    # If that fails, skip this country's label
                    continue

            # Check if the label position is within the view box
            label_point = Point(centroid.x, centroid.y)
            if not view_box.contains(label_point):
                # Skip labels that would be outside the view
                continue

            # Add the label
            ax.text(
                centroid.x,
                centroid.y,
                country["display_iso"],
                fontsize=config.label_size,
                ha="center",
                va="center",
                color=config.colors.text_color,
                fontweight="bold" if country["country_type"] == "target" else "normal",
                bbox=dict(
                    facecolor="white",
                    alpha=0.7,
                    edgecolor="none",
                    boxstyle="round,pad=0.2",
                ),
            )

    # Remove axes
    ax.set_axis_off()

    # Save the figure
    plt.savefig(config.output_path, dpi=config.dpi, bbox_inches="tight")

    # Close the figure to free memory
    plt.close(fig)
