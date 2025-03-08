#!/usr/bin/env python
"""
Command-line interface module for the maps package.

This module provides functionality for parsing command-line arguments
for the map generation tools.
"""

import argparse
from typing import Optional


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the map generation tool.

    This function defines and parses the command-line arguments for the map generation
    tool, including the target country, database path, output path, and various
    rendering options.

    Args:
        args: Optional list of command-line arguments to parse. If None, sys.argv is used.

    Returns:
        Namespace containing the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate a map of a country and its neighbors."
    )

    # Required arguments
    parser.add_argument(
        "country",
        type=str,
        help="Name of the country to map (e.g., 'United States')",
    )

    # Optional arguments
    parser.add_argument(
        "--db-path",
        type=str,
        default="natural_earth_vector.sqlite",
        help="Path to the Natural Earth SQLite database (default: natural_earth_vector.sqlite)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output path for the map image (default: /tmp/<country_name>.png)",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution of the output image in DPI (default: 300)",
    )

    parser.add_argument(
        "--target-percentage",
        type=float,
        default=0.3,
        help="Percentage of the map area to be occupied by the target country (default: 0.3)",
    )

    parser.add_argument(
        "--exclude-exclaves",
        action="store_true",
        default=True,
        help="Exclude exclaves (territories separated from the main territory) (default: True)",
    )

    parser.add_argument(
        "--include-exclaves",
        action="store_false",
        dest="exclude_exclaves",
        help="Include exclaves (territories separated from the main territory)",
    )

    parser.add_argument(
        "--no-labels",
        action="store_false",
        dest="show_labels",
        help="Do not show country labels on the map",
    )

    parser.add_argument(
        "--label-size",
        type=int,
        default=8,
        help="Font size for country labels (default: 8)",
    )

    parser.add_argument(
        "--border-width",
        type=float,
        default=0.5,
        help="Width of country borders (default: 0.5)",
    )

    # Parse the arguments
    return parser.parse_args(args)
