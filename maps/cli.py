#!/usr/bin/env python
"""
Command-line interface module for the maps package.

This module provides functionality for parsing command-line arguments
and running the command-line interface for the map generation tools
and territory analysis.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional, Tuple

import geopandas as gpd
from shapely.geometry import MultiPolygon

from maps.draw_map import load_country_data
from maps.language_config import (
    get_display_info,
    get_supported_languages,
    is_language_supported,
)
from maps.models import MapConfiguration
from maps.renderer import create_map
from maps.territory_analyzer import (
    TerritoryAnalyzer,
    get_country_territory_info,
)


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the map generation and territory analysis tools.

    This function defines and parses the command-line arguments for the map generation
    and territory analysis tools, including the target country, database path, output path,
    and various rendering and analysis options.

    Args:
        args: Optional list of command-line arguments to parse. If None, sys.argv is used.

    Returns:
        Namespace containing the parsed arguments
    """
    # Get the arguments if not provided
    if args is None:
        args = sys.argv[1:]

    # Check if the first argument is a command or a country name
    if args and args[0] not in ["map", "analyze"] and not args[0].startswith("-"):
        # If it's not a command and not an option, it's a country name
        # Insert the default "map" command
        args.insert(0, "map")

    parser = argparse.ArgumentParser(
        description="Generate maps and analyze territories of countries."
    )

    # Add option to list supported languages
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all supported languages for map labels",
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

    # Create the 'map' sub-command
    map_parser = subparsers.add_parser(
        "map", help="Generate a map of a country and its neighbors"
    )
    _add_map_arguments(map_parser)

    # Create the 'analyze' sub-command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze territory of a country"
    )
    _add_analyze_arguments(analyze_parser)

    # Parse the arguments
    parsed_args = parser.parse_args(args)

    # Default command is 'map' if no command specified (should not happen with our logic above)
    if not parsed_args.command and not parsed_args.list_languages:
        parsed_args.command = "map"

    # Handle list-languages option
    if parsed_args.list_languages:
        _print_supported_languages()
        sys.exit(0)

    # Validate language parameter if provided
    if hasattr(parsed_args, "language") and parsed_args.language:
        if not is_language_supported(parsed_args.language):
            supported_langs = ", ".join(get_supported_languages())
            sys.stderr.write(
                f"Error: Unsupported language code '{parsed_args.language}'. "
                f"Supported languages are: {supported_langs}\n"
            )
            sys.exit(1)

    return parsed_args


def _print_supported_languages() -> None:
    """Print a list of supported languages to stdout."""
    languages = get_display_info()
    print("\nSupported languages for map labels:")
    print("-" * 40)
    for lang in languages:
        print(f"{lang['code']:<5} - {lang['name']}")
    print("\nUse --language CODE to specify a language (e.g., --language fr)")


def _add_map_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add map generation arguments to a parser.

    Args:
        parser: ArgumentParser to add arguments to
    """
    # Required arguments
    parser.add_argument(
        "country",
        type=str,
        help="Name of the country to map in English (e.g., 'United States')",
    )

    # Optional arguments
    parser.add_argument(
        "--db-path",
        type=str,
        default="natural_earth_vector.sqlite",
        help="Path to the Natural Earth SQLite database (default: natural_earth_vector.sqlite)",
    )

    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default="en",
        help="Language code for country labels (default: en). Use --list-languages to see available options.",
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
        dest="exclude_exclaves",
        type=lambda x: x.lower() == "true",
        default=True,
        help="Exclude exclaves (territories separated from the main territory) (default: True)",
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

    parser.add_argument(
        "--show-territory-info",
        action="store_true",
        help="Include territory information in the map title",
    )


def _add_analyze_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add territory analysis arguments to a parser.

    Args:
        parser: ArgumentParser to add arguments to
    """
    # Required argument
    parser.add_argument(
        "country",
        type=str,
        help="Name of the country to analyze (e.g., 'United States')",
    )

    # Optional arguments
    parser.add_argument(
        "--db-path",
        type=str,
        default="natural_earth_vector.sqlite",
        help="Path to the Natural Earth SQLite database (default: natural_earth_vector.sqlite)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Threshold for determining if a polygon is dominant (0.0-1.0) (default: 0.8)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output territory information in JSON format",
    )


def filter_exclaves(
    target_country: gpd.GeoDataFrame, territory_info: Dict[str, Any]
) -> Tuple[gpd.GeoDataFrame, Optional[float]]:
    """
    Filter out exclaves from a country's geometry, keeping only the main landmass.

    Args:
        target_country: GeoDataFrame containing the target country
        territory_info: Dictionary with territory information from territory_analyzer

    Returns:
        Tuple containing:
            - Modified GeoDataFrame with only the main landmass
            - Percentage of the total area represented by the main landmass, or None if no filtering was done
    """
    # Get the main polygon (largest by area)
    main_territory_info = territory_info["territories"][0]
    percentage = main_territory_info["percentage"]

    # Get the target country geometry
    target_geom = target_country.geometry.iloc[0]

    if isinstance(target_geom, MultiPolygon):
        # Find the largest polygon (main territory) based on territory analysis
        main_polygon = max(target_geom.geoms, key=lambda p: p.area)

        # Create a new geometry with just the main territory
        filtered_country = target_country.copy()
        filtered_country.loc[filtered_country.index[0], "geometry"] = main_polygon

        return filtered_country, percentage

    # For single Polygon, return the original country and the percentage
    # (which should be 100% for a single polygon)
    return target_country, percentage


def generate_map(args: argparse.Namespace) -> None:
    """
    Generate a map based on the provided arguments.

    Args:
        args: Namespace containing the parsed arguments
    """
    country_name: str = args.country
    db_path: str = args.db_path
    exclude_exclaves: bool = (
        args.exclude_exclaves if hasattr(args, "exclude_exclaves") else False
    )
    language: str = args.language if hasattr(args, "language") else "en"

    # Set output path
    output_path: str = (
        args.output or f"/tmp/{country_name.lower().replace(' ', '_')}.png"
    )

    try:
        # Load country data with language parameter
        countries, target_country, neighbor_names = load_country_data(
            country_name, db_path, language=language
        )

        # Prepare the map title
        title = f"{country_name} and Its Neighbors"

        # Add territory information if requested or if excluding exclaves
        territory_info = None
        if getattr(args, "show_territory_info", False) or exclude_exclaves:
            territory_info = get_country_territory_info(country_name, db_path)
            territory_type = territory_info["territory_type"]

            # Update title if showing territory info
            if getattr(args, "show_territory_info", False):
                if territory_type == "continuous":
                    title = f"{country_name} and Its Neighbors (Continuous Territory)"
                elif territory_type == "island_nation":
                    title = f"{country_name} and Its Neighbors (Island Nation)"
                elif territory_type == "has_exclave":
                    title = f"{country_name} and Its Neighbors (With Exclaves)"

        # Create map configuration
        config = MapConfiguration(
            output_path=output_path,
            title=title,
            dpi=args.dpi,
            target_percentage=args.target_percentage,
            exclude_exclaves=exclude_exclaves,
            show_labels=args.show_labels,
            label_size=args.label_size,
            label_type=args.label_type,
            border_width=args.border_width,
            language=language,  # Add language to the config
        )

        # If we're excluding exclaves and the country has exclaves or is an island nation,
        # modify the target country geometry to only include the main landmass
        if (
            exclude_exclaves
            and territory_info
            and (territory_info["has_exclaves"] or territory_info["is_island_nation"])
        ):
            # Filter out exclaves
            target_country, percentage = filter_exclaves(target_country, territory_info)

            # Print information about excluded exclaves if filtering was done
            if percentage is not None:
                print(
                    f"Excluding exclaves: Only showing the main landmass ({percentage:.1f}% of total area)"
                )

        # Generate the map
        create_map(countries, target_country, neighbor_names, config)

        # Report success
        print(
            f"Successfully created map for {country_name} with {len(neighbor_names)} neighbors"
        )
        print(f"Map saved to: {output_path}")
        print(f"Labels language: {language}")

    except Exception as e:
        print(f"Error creating map: {e}")
        return


def analyze_territory(args: argparse.Namespace) -> None:
    """
    Analyze a country's territory and display the results.

    Args:
        args: Namespace containing the parsed arguments
    """
    try:
        if args.json:
            # Output in JSON format
            territory_info = get_country_territory_info(
                args.country, args.db_path, args.threshold
            )
            print(json.dumps(territory_info, indent=2))
        else:
            # Run analysis and print human-readable results
            analyzer = TerritoryAnalyzer(main_area_threshold=args.threshold)
            result = analyzer.analyze_from_db(args.country, args.db_path)

            print(f"Country: {result.country_name}")
            print(f"Territory Type: {result.geometry_type.value}")
            print(f"Polygon Count: {result.polygon_count}")
            print(f"Total Area: {result.total_area:.2f} square units")

            if result.polygon_count > 1:
                print(
                    f"Largest Polygon: {result.main_polygon_percentage:.2f}% of total area"
                )
                print(
                    f"Max Distance Between Polygons: {result.max_distance_between_polygons:.2f} units"
                )

                print("\nTerritories:")
                for i, territory in enumerate(result.separate_territories):
                    print(
                        f"  {i+1}. Area: {territory['area']:.2f} sq units "
                        f"({territory['percentage']:.2f}% of total), "
                        f"Centroid: {territory['centroid']}"
                    )

    except Exception as e:
        print(f"Error analyzing territory: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main function for the CLI.

    This function parses command-line arguments and calls the appropriate
    sub-command function.
    """
    parsed_args: argparse.Namespace = parse_args()

    if parsed_args.command == "analyze":
        analyze_territory(parsed_args)
    else:  # Default to 'map' command
        generate_map(parsed_args)


if __name__ == "__main__":
    main()
