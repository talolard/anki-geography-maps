# CLI Implementation Plan

This document outlines the plan for implementing the CLI functionality for the maps package.

## Overview

The CLI module in `maps/cli.py` defines the argument parser and the implementation is now complete. The CLI can be used to generate maps of countries and their neighbors with various customization options.

## Current Status

- ✅ The argument parser is fully implemented in `cli.py` with various arguments for configuring the map generation.
- ✅ The `parse_args` function is implemented and all arguments are correctly used in the main function.
- ✅ `draw_map.py` contains the `main()` function which properly uses the parsed arguments to create a `MapConfiguration` object.
- ✅ Comprehensive test cases for all functionality are implemented in `tests/maps/test_draw_map.py`.
- ✅ Documentation for CLI usage is provided in `docs/cli_usage.md`.

## Implementation Findings

After examining and completing the code:

1. All CLI arguments are defined in `cli.py`
2. All arguments are now correctly passed to the `MapConfiguration` object in `main()`
3. The `border_width` argument was previously defined in `cli.py` but not used in `main()` - this has been fixed
4. All arguments now have comprehensive tests to ensure they're correctly passed to `MapConfiguration`

## Implementation Steps

### Phase 1: Basic Functionality

- [x] Review current argument parser implementation in `cli.py`
- [x] Review main function in `draw_map.py` 
- [x] Verify basic functionality works with country name and output path (tests exist)
- [x] Write test for basic CLI functionality (tests exist in `TestParseArgs` and `TestMainFunction` classes)

### Phase 2: Complete Missing Implementation

- [x] Add support for the `border_width` argument in the `main()` function
   - [x] Update the `MapConfiguration` creation to include `border_width`
   - [x] Add a test for this parameter

### Phase 3: Implement Tests for Remaining Arguments

For each argument in the CLI, we needed to test that it's correctly passed to the `MapConfiguration` object:

- [x] `--db-path` - Path to the Natural Earth SQLite database
   - [x] Test that custom DB path works (test exists in `test_custom_values`)

- [x] `--output` / `-o` - Output path for the map image
   - [x] Test custom output path (test exists in `test_main_custom_output`)

- [x] `--dpi` - Resolution of the output image
   - [x] Test custom DPI setting (test exists in `test_custom_values`)

- [x] `--target-percentage` - Percentage of map area for target country
   - [x] Test that target_percentage is correctly passed to MapConfiguration

- [x] `--exclude-exclaves` / `--include-exclaves` - Handling of exclaves
   - [x] Test that exclude_exclaves is correctly passed to MapConfiguration
   - [x] Test that include_exclaves option works correctly

- [x] `--no-labels` - Flag to hide country labels
   - [x] Test that show_labels is correctly passed to MapConfiguration

- [x] `--label-size` - Font size for country labels
   - [x] Test that label_size is correctly passed to MapConfiguration

- [x] `--label-type` - Type of label to display (code/name)
   - [x] Test that label_type is correctly passed to MapConfiguration

- [x] `--border-width` - Width of country borders
   - [x] Test that border_width is correctly passed to MapConfiguration

### Phase 4: Integration and Documentation

- [x] Write comprehensive integration tests for all CLI arguments together
   - [x] Added `test_main_all_options` to test all arguments at once
- [x] Create examples of usage in documentation
   - [x] Created `docs/cli_usage.md` with examples for each argument
- [x] Update docstrings and comments

## Summary of Changes

1. Added the missing `border_width` parameter to the `MapConfiguration` creation in the `main()` function
2. Created individual tests for each CLI argument to verify they're passed correctly to the `MapConfiguration` object
3. Created an integration test that verifies all parameters work together correctly
4. Created comprehensive documentation with examples of CLI usage
5. All tests are passing, confirming that the CLI is fully functional

## Test Design Pattern Used

For each argument test, we followed this pattern:
```python
@patch("maps.draw_map.load_country_data")
@patch("maps.draw_map.create_map")
def test_main_with_parameter(
    self,
    mock_create_map: MagicMock,
    mock_load_country_data: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test parameter is correctly passed to MapConfiguration."""
    # Mock command line arguments with the parameter
    monkeypatch.setattr(
        "sys.argv", 
        ["maps/draw_map.py", "Germany", "--parameter-name", "parameter_value"]
    )

    # Mock the return value of load_country_data
    mock_load_country_data.return_value = (MagicMock(), MagicMock(), [])

    # Run main function
    main()

    # Verify that create_map was called with the right parameter
    args, kwargs = mock_create_map.call_args
    assert args[3].parameter_name == parameter_value
```

## Conclusion

The CLI implementation is now complete and fully tested. Users can generate maps of countries and their neighbors with various customization options. The command-line interface provides a flexible and powerful way to use the map generation functionality without writing Python code.

Future enhancements could include:
1. Adding support for custom colors
2. Adding options for figure size
3. Adding support for saving maps in different formats
4. Adding options for additional map elements like scale bar or compass rose 