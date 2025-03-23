#!/usr/bin/env python
"""
Models module for the maps package.

This module defines data classes and type aliases used throughout the package
for map generation, styling, and configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, Union, List, Tuple, Dict, Any, Literal
from shapely.geometry.base import BaseGeometry

# Type alias for shapely geometry objects
ShapelyGeometry = BaseGeometry

# Type for label display options
LabelType = Literal["code", "name"]


@dataclass(frozen=True)
class MapColors:
    """
    Configuration for map colors.

    This immutable dataclass defines the color scheme used for rendering maps,
    including colors for the target country, neighbors, other countries, and borders.

    Attributes:
        target_color: Color for the target country (default: light red)
        neighbor_color: Color for neighboring countries (default: light blue)
        other_color: Color for non-target, non-neighbor countries (default: light gray)
        border_color: Color for country borders (default: dark gray)
        ocean_color: Color for ocean areas (default: very light blue)
        highlight_color: Color for highlighted features (default: yellow)
        text_color: Color for text elements (default: black)
    """

    target_color: str = "#ffaaaa"  # Light red
    neighbor_color: str = "#aaaaff"  # Light blue
    other_color: str = "#f5f5f5"  # Light gray
    border_color: str = "#333333"  # Dark gray
    ocean_color: str = "#e6f2ff"  # Very light blue
    highlight_color: str = "#ffff00"  # Yellow
    text_color: str = "#000000"  # Black


@dataclass(frozen=True)
class MapConfiguration:
    """
    Configuration for map generation.

    This immutable dataclass defines the parameters used for rendering maps,
    including output path, title, resolution, and styling options.

    Attributes:
        output_path: Path where the map image will be saved
        title: Title to display on the map
        dpi: Resolution of the output image in dots per inch
        figsize: Size of the figure in inches (width, height)
        target_percentage: Percentage of the map area to be occupied by the target country
        exclude_exclaves: Whether to exclude exclaves (territories separated from the main territory)
        colors: Color scheme for the map
        show_labels: Whether to show country labels on the map
        label_size: Font size for country labels
        label_type: Type of label to display ("code" for country codes, "name" for full names)
        border_width: Width of country borders
    """

    output_path: str
    title: str
    dpi: int = 300
    figsize: Tuple[int, int] = (10, 8)
    target_percentage: float = 0.3
    exclude_exclaves: bool = True
    colors: MapColors = field(default_factory=MapColors)
    show_labels: bool = True
    label_size: float = 8.0
    label_type: LabelType = "name"
    border_width: float = 0.5
