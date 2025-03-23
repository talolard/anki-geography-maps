#!/usr/bin/env python
"""
Script to test the territory analyzer with real data from Natural Earth database.

This script analyzes the geometries of several countries to demonstrate
the classification of countries into continuous landmass, island nations,
and countries with exclaves.
"""

import argparse
import logging
import os
import sys
from typing import List, Optional

from maps.territory_analyzer import CountryGeometryType, TerritoryAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_country_types")


def analyze_countries(
    countries: List[str], db_path: str, threshold: float = 0.8
) -> None:
    """
    Analyze a list of countries and print the results.

    Args:
        countries: List of country names to analyze
        db_path: Path to the Natural Earth SQLite database
        threshold: Threshold for determining if a polygon is dominant (default: 0.8)
    """
    analyzer = TerritoryAnalyzer(main_area_threshold=threshold)
    logger.info(f"Using main area threshold: {threshold}")

    for country_name in countries:
        try:
            logger.info(f"Analyzing {country_name}...")
            result = analyzer.analyze_from_db(country_name, db_path)

            # Print summary
            logger.info(f"Country: {result.country_name}")
            logger.info(f"Classification: {result.geometry_type.value}")
            logger.info(f"Total area: {result.total_area:.2f} square units")
            logger.info(f"Number of polygons: {result.polygon_count}")

            if result.polygon_count > 1:
                logger.info(
                    f"Largest polygon: {result.main_polygon_percentage:.2f}% of total area"
                )
                logger.info(
                    f"Max distance between polygons: {result.max_distance_between_polygons:.2f} units"
                )

                # Print details of each territory
                logger.info("Territories:")
                for i, territory in enumerate(result.separate_territories):
                    logger.info(
                        f"  {i+1}. Area: {territory['area']:.2f} sq units "
                        f"({territory['percentage']:.2f}% of total), "
                        f"Centroid: {territory['centroid']}"
                    )

            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Error analyzing {country_name}: {e}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Analyze country geometries and classify them",
    )
    parser.add_argument(
        "--countries",
        type=str,
        default="Israel,Russia,Indonesia",
        help="Comma-separated list of countries to analyze",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="natural_earth_vector.sqlite",
        help="Path to the Natural Earth SQLite database",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Threshold for determining if a polygon is dominant (0.0-1.0)",
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

    # Run analysis
    analyze_countries(countries, args.db_path, args.threshold)


if __name__ == "__main__":
    main()
