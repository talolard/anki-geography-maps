# Maps Visualization Tool

A Python package for creating simple, informative maps showing countries and their neighbors.

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
from src.maps.draw_map import create_map

create_map("Germany", output_file="germany_map.png")
```

### Customized Map

Generate a map with custom configuration:

```python
from src.maps.draw_map import create_map, MapConfiguration

# Create custom configuration
config = MapConfiguration(
    width=1200,
    height=800,
    show_map_labels=True,
    show_neighbors=True,
    target_percentage=60
)

# Create the map
create_map("France", output_file="france_map.png", config=config)
```

### Command Line Usage

```bash
python -m src.maps.draw_map Germany --width=1200 --height=800
```

## Project Structure

```
maps/
├── src/
│   └── maps/
│       ├── __init__.py
│       ├── draw_map.py         # Main map drawing functionality
│       └── find_neighbors.py   # Country neighbor lookup
├── tests/
│   ├── conftest.py             # Shared test fixtures
│   └── maps/
│       ├── __init__.py
│       ├── test_draw_map.py    # Tests for drawing functions
│       └── test_find_neighbors.py # Tests for neighbor lookup
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
pytest --cov=src --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
