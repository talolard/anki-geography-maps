# Maps Visualization Tool

A Python package for creating simple, informative maps showing countries and their neighbors.

<div align="center">
  <img src="docs/static/germany_map.png" alt="Germany Map" width="32%" />
  <img src="docs/static/israel_map.png" alt="Israel Map" width="32%" />
  <img src="docs/static/mexico_map.png" alt="Mexico Map" width="32%" />
  <p><i>Example maps showing Germany (9 neighbors), Israel (5 neighbors), and Mexico (3 neighbors) with their neighboring countries highlighted.</i></p>
</div>

## Features

- Generate country maps with clear visualization
- Highlight target countries and their neighbors
- Optimized drawing with automatic bounds calculation
- SQLite-based geographic data storage

## Installation

### Prerequisites

- Python 3.9 or higher
- SQLite database with geographic data (included)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/username/maps.git
   cd maps
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

4. Install development dependencies (optional):
   ```bash
   pip install -e ".[dev]"
   ```

## Usage

### Basic Example

Generate a map of Germany with default settings:

```python
from draw_map import create_map, MapConfiguration, load_country_data

# Create the map
config = MapConfiguration(output_path="germany_map.png", title="Germany and Its Neighbors")
countries, target_country, neighbor_names = load_country_data("Germany")
create_map(countries, target_country, neighbor_names, config)
```

### Command Line Usage

```bash
# Generate a map for Germany
python draw_map.py Germany

# Generate a map for Israel with custom output path and resolution
python draw_map.py Israel -o israel_map.png --dpi 300

# Generate a map for Mexico
python draw_map.py Mexico
```

### Find Neighbors Tool

You can also use the neighbors tool to get information about country borders:

```bash
# List neighboring countries for France
python find_neighbors.py France

# List available countries (limited to 20)
python find_neighbors.py --list

# List all available countries
python find_neighbors.py --list-all
```

## Project Structure

```
maps/
├── docs/
│   └── static/                # Example maps and images
│       ├── germany_map.png
│       ├── israel_map.png
│       └── mexico_map.png
├── tests/
│   ├── conftest.py            # Shared test fixtures
│   └── maps/
│       ├── __init__.py
│       ├── test_draw_map.py   # Tests for drawing functions
│       └── test_find_neighbors.py # Tests for neighbor lookup
├── __init__.py                # Package initialization
├── draw_map.py                # Main map drawing functionality
├── find_neighbors.py          # Country neighbor lookup
├── natural_earth_vector.sqlite # Geographic database
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## Testing

Run the tests with pytest:

```bash
pytest
```

For test coverage report:

```bash
pytest --cov=. --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
