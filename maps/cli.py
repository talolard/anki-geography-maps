#!/usr/bin/env python
"""
Command-line interface module for the maps package.

This module provides functionality for parsing command-line arguments
and running the command-line interface for the map generation tools.
"""

import argparse
from typing import Optional

from maps.draw_map import load_country_data
from maps.models import MapConfiguration
from maps.renderer import create_map


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
        type=float,
        default=8.0,
        help="Font size for country labels (default: 8.0)",
    )

    parser.add_argument(
        "--label-type",
        type=str,
        choices=["code", "name"],
        default="name",
        help="Type of label to display: 'code' for country codes, 'name' for full names (default: name)",
    )

    parser.add_argument(
        "--border-width",
        type=float,
        default=0.5,
        help="Width of country borders (default: 0.5)",
    )

    # Parse the arguments
    return parser.parse_args(args)


def main() -> None:
    """
    Main function for the map generation command-line interface.

    This function parses command-line arguments, loads country data,
    creates a map configuration, and generates the map.

    Returns:
        None
    """
    # Parse command-line arguments
    parsed_args: argparse.Namespace = parse_args()

    country_name: str = parsed_args.country
    db_path: str = parsed_args.db_path

    # Set output path
    output_path: str = (
        parsed_args.output or f"/tmp/{country_name.lower().replace(' ', '_')}.png"
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
            dpi=parsed_args.dpi,
            target_percentage=parsed_args.target_percentage,
            exclude_exclaves=getattr(parsed_args, "exclude_exclaves", True),
            show_labels=parsed_args.show_labels,
            label_size=parsed_args.label_size,
            label_type=parsed_args.label_type,
            border_width=parsed_args.border_width,
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
