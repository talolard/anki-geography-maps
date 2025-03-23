# Territory Analyzer Integration Plan

## Current State

1. `exclave_handler.py` exists but is empty
2. `territory_analyzer.py` contains logic for analyzing country territories and has its own CLI functionality
3. `cli.py` is the main CLI entry point but doesn't utilize the territory analysis functionality

## Goals

1. Delete the empty `exclave_handler.py` file
2. Move the CLI-related functionality from `territory_analyzer.py` to `cli.py` 
3. Ensure `territory_analyzer.py` cannot be called directly from the shell
4. Integrate territory analysis functionality into the main CLI

## Implementation Plan

### Phase 1: Cleanup

1. Delete the empty `exclave_handler.py` file
2. Examine `territory_analyzer.py` to understand its functionality and CLI implementation

### Phase 2: Refactor territory_analyzer.py

1. Remove the CLI-specific code (argument parsing, main function) from `territory_analyzer.py`
2. Ensure all territory analysis functionality remains intact and accessible
3. Add proper docstrings to all functions to clarify their purpose and usage

### Phase 3: Enhance cli.py

1. Add territory analysis functionality to `cli.py`
2. Add new CLI arguments related to territory analysis
3. Integrate with existing map generation functionality

### Phase 4: Testing

1. Test the territory analysis functionality through the main CLI
2. Ensure that the original functionality works as expected
3. Verify that `territory_analyzer.py` cannot be called directly

### Phase 5: Documentation

1. Update documentation to reflect the changes
2. Include examples of how to use the territory analysis functionality

## Expected Outcome

- A streamlined codebase with clear separation of concerns
- `territory_analyzer.py` focused solely on territory analysis logic
- `cli.py` as the single entry point for all CLI functionality
- Improved user experience with consistent command structure 