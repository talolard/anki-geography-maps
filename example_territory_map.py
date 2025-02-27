#!/usr/bin/env python
"""
Example script that integrates territory analysis with map drawing.

This script demonstrates how to use the territory_analyzer module
to enhance maps drawn with the draw_map module, adding information
about a country's territory type (continuous, island nation, or with exclaves).
"""

import argparse
import logging
import os
import sys
from dataclasses import asdict
from typing import List, Optional

from draw_map import (
    CountryName,
    DBPath,
    MapColors,
    MapConfiguration,
    create_map,
    load_country_data,
)
from territory_analyzer import (
    CountryGeometryType,
    TerritoryAnalyzer,
    get_country_territory_info,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("example_territory_map")


def create_enhanced_map(
    country_name: str,
    db_path: str = "natural_earth_vector.sqlite",
    output_path: Optional[str] = None,
    threshold: float = 0.8,
    exclude_exclaves: bool = True,
) -> None:
    """
    Create a map enhanced with territory type information.

    This function loads country data, analyzes its territory type,
    and creates a map with enhanced title and visualization.

    Args:
        country_name: Name of the country to map
        db_path: Path to the Natural Earth SQLite database
        output_path: Path for the output map image (default is /tmp/<country>_territory.png)
        threshold: Threshold for determining if a polygon is dominant (default: 0.8)
        exclude_exclaves: Whether to exclude exclaves from the map rendering and bounds calculation (default: True)
    """
    # Determine output path if not provided
    if output_path is None:
        output_path = f"/tmp/{country_name.lower().replace(' ', '_')}_territory.png"

    # Get territory information
    territory_info = get_country_territory_info(country_name, db_path, threshold)
    logger.info(f"Analyzed {country_name}: {territory_info['territory_type']}")

    # Create custom colors based on territory type
    colors = MapColors()

    # Load country data for drawing
    countries, target_country, neighbor_names = load_country_data(country_name, db_path)

    # Create map title based on territory type
    if territory_info["territory_type"] == "continuous":
        title = f"{country_name} (Continuous Territory)"
    elif territory_info["territory_type"] == "island_nation":
        title = f"{country_name} (Island Nation)"
    elif territory_info["territory_type"] == "has_exclave":
        title = f"{country_name} (With Exclaves)"
    else:
        title = f"{country_name}"

    # Create map configuration
    config = MapConfiguration(
        output_path=output_path,
        title=title,
        dpi=300,
        target_percentage=0.6 if territory_info["polygon_count"] > 1 else 0.4,
        exclude_exclaves=exclude_exclaves,
        main_area_threshold=threshold,
    )

    # Generate the map
    create_map(countries, target_country, neighbor_names, config)

    # Report territory information
    logger.info(f"Country: {country_name}")
    logger.info(f"Territory Type: {territory_info['territory_type']}")
    logger.info(f"Polygon Count: {territory_info['polygon_count']}")
    logger.info(f"Main Area Percentage: {territory_info['main_area_percentage']:.2f}%")

    if territory_info["polygon_count"] > 1:
        logger.info(
            f"Maximum Distance Between Polygons: {territory_info['max_distance']:.2f}"
        )

        logger.info("Territories:")
        for i, territory in enumerate(territory_info["territories"]):
            logger.info(
                f"  {i+1}. Area: {territory['area']:.2f} sq units "
                f"({territory['percentage']:.2f}% of total)"
            )

    logger.info(f"Map saved to: {output_path}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Create maps enhanced with territory type information",
    )
    parser.add_argument(
        "countries",
        type=str,
        help="Comma-separated list of countries to analyze and map",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="natural_earth_vector.sqlite",
        help="Path to the Natural Earth SQLite database",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp",
        help="Directory for output map images",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Threshold for determining if a polygon is dominant (0.0-1.0)",
    )
    parser.add_argument(
        "--include-exclaves",
        action="store_true",
        help="Include exclaves in the map rendering and bounds calculation",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to coordinate the program execution."""
    args = parse_args()

    # Verify database exists
    if not os.path.exists(args.db_path):
        logger.error(f"Database file not found: {args.db_path}")
        return

    # Parse countries list
    countries = [c.strip() for c in args.countries.split(",")]
    if not countries:
        logger.error("No countries specified")
        return

    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        logger.error("Threshold must be between 0.0 and 1.0")
        return

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Process each country
    for country_name in countries:
        try:
            output_path = os.path.join(
                args.output_dir,
                f"{country_name.lower().replace(' ', '_')}_territory.png",
            )

            logger.info(f"Processing {country_name}...")
            create_enhanced_map(
                country_name,
                args.db_path,
                output_path,
                args.threshold,
                not args.include_exclaves,  # Exclude exclaves by default unless --include-exclaves is specified
            )

        except Exception as e:
            logger.error(f"Error processing {country_name}: {e}")


if __name__ == "__main__":
    main()
