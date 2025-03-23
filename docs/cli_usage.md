# Map Generator CLI Usage Guide

This guide provides instructions on how to use the command-line interface for generating maps of countries and their neighbors, as well as analyzing country territories.

## Command Structure

The CLI now supports two main commands:

- `map`: Generate a map of a country and its neighbors (default)
- `analyze`: Analyze a country's territory

For backward compatibility, you can omit the `map` command and directly specify a country name.

## Map Generation

### Basic Usage

The most basic usage requires only specifying a country name:

```bash
python -m maps "United States"
```

Or with the explicit command:

```bash
python -m maps map "United States"
```

This will generate a map of the United States and its neighbors, saving it to `/tmp/united_states.png` by default.

### Specifying Output Path

You can specify a custom output path using the `-o` or `--output` option:

```bash
python -m maps "Germany" -o "/path/to/germany_map.png"
```

### Database Path

By default, the tool uses a database file named `natural_earth_vector.sqlite` in the current directory. You can specify a different path:

```bash
python -m maps "France" --db-path "/path/to/database.sqlite"
```

### Map Styling Options

#### Resolution (DPI)

Set the resolution of the output image:

```bash
python -m maps "Japan" --dpi 600
```

#### Target Country Size

Control how much of the map is occupied by the target country (value between 0.0 and 1.0):

```bash
python -m maps "China" --target-percentage 0.5
```

#### Exclaves

By default, exclaves (territories separated from the main landmass) are excluded. You can include them:

```bash
python -m maps "Russia" --include-exclaves
```

Or explicitly exclude them:

```bash
python -m maps "Russia" --exclude-exclaves
```

#### Labels

Show or hide country labels:

```bash
python -m maps "Brazil" --no-labels  # Hide labels
```

Adjust label size:

```bash
python -m maps "Brazil" --label-size 10.0
```

Choose label type (country name or country code):

```bash
python -m maps "Brazil" --label-type code  # Show country codes (BRA, ARG, etc.)
python -m maps "Brazil" --label-type name  # Show full country names (default)
```

#### Border Width

Adjust the width of country borders:

```bash
python -m maps "Italy" --border-width 1.0
```

### Territory Information

Include territory information in the map title:

```bash
python -m maps "Russia" --show-territory-info
```

This will add information about the country's territory type to the map title, such as "(Continuous Territory)", "(Island Nation)", or "(With Exclaves)".

### Combining Options

You can combine multiple options:

```bash
python -m maps "Germany" \
  -o "/path/to/germany_map.png" \
  --dpi 600 \
  --target-percentage 0.4 \
  --include-exclaves \
  --label-type code \
  --label-size 9.0 \
  --border-width 0.7 \
  --show-territory-info
```

## Territory Analysis

Analyze a country's territory without generating a map:

```bash
python -m maps analyze "Russia"
```

This will display information about the country's territory, including:
- Territory type (continuous, island nation, or has exclaves)
- Number of polygons (separate landmasses)
- Area statistics
- Distance between polygons

### Customizing Analysis

Specify a custom database path:

```bash
python -m maps analyze "France" --db-path "/path/to/database.sqlite"
```

Adjust the threshold for determining if a polygon is dominant (default: 0.8):

```bash
python -m maps analyze "United States" --threshold 0.7
```

### JSON Output

Get the territory information in JSON format:

```bash
python -m maps analyze "Japan" --json
```

This is useful for programmatic access to the territory data.

## Getting Help

Display help information:

```bash
python -m maps --help
```

For help on a specific command:

```bash
python -m maps map --help
python -m maps analyze --help
```

This will show all available options with their descriptions and default values. 