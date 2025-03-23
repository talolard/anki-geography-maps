# Multilingual Labels Implementation Plan

## Overview

The goal is to enhance the maps CLI to support multilingual country labels on generated maps. Based on the Natural Earth database schema, we have access to country names in multiple languages through columns like `name_ar`, `name_fr`, `name_ru`, etc. This plan outlines how to implement language selection in the CLI, retrieve the appropriate labels, and display them on the maps.

## Available Languages

From the database schema inspection, we have the following language columns:

- `name` (default English name)
- `name_en` (English)
- `name_ar` (Arabic)
- `name_bn` (Bengali)
- `name_de` (German)
- `name_es` (Spanish)
- `name_fa` (Persian/Farsi)
- `name_fr` (French)
- `name_el` (Greek)
- `name_he` (Hebrew)
- `name_hi` (Hindi)
- `name_hu` (Hungarian)
- `name_id` (Indonesian)
- `name_it` (Italian)
- `name_ja` (Japanese)
- `name_ko` (Korean)
- `name_nl` (Dutch)
- `name_pl` (Polish)
- `name_pt` (Portuguese)
- `name_ru` (Russian)
- `name_sv` (Swedish)
- `name_tr` (Turkish)
- `name_uk` (Ukrainian)
- `name_ur` (Urdu)
- `name_vi` (Vietnamese)
- `name_zh` (Chinese - Simplified)
- `name_zht` (Chinese - Traditional)

## Implementation Steps

### 1. Language Support Configuration

1. Create a language configuration module `maps/language_config.py`:
   - Define a dictionary mapping language codes to database column names
   - Provide functions to validate language codes
   - Define a function to get the list of supported languages

### 2. CLI Interface Updates

1. Modify `maps/cli.py`:
   - Add a `--language` or `-l` parameter to the map command
   - The parameter should accept a language code (e.g., "en", "fr", "es")
   - Provide validation to ensure the language code is supported
   - Default to "en" (English) if not specified
   - Add option to list supported languages (`--list-languages`)

### 3. Data Retrieval Modifications

1. Update `maps/draw_map.py`:
   - Modify `load_country_data()` to accept a language parameter
   - Ensure the appropriate language column is included in the queries
   - Create a mapping between English country names and localized names
   - Add a fallback to English if a translation is missing

2. Update `maps/find_neighbors.py`:
   - Modify `get_neighboring_countries()` to support localized names
   - Ensure the target country search still uses English name

### 4. Label Rendering Updates

1. Update `maps/renderer.py` or equivalent:
   - Modify the map creation function to use localized names for labels
   - Ensure consistency with the label_type parameter (code or name)

### 5. Documentation

1. Update the help text and documentation to reflect the new language options
2. Provide examples of using the language parameter

## Feature Interactions

### Interaction with find_neighbors.py

- **Input**: Country names will still be provided in English for searching
- **Output**: When retrieving neighbor countries, we'll need to fetch both English names (for reference) and the localized names (for display)

### Interaction with draw_map.py

- The function should retrieve the appropriate language column
- We need to ensure we maintain a mapping between English names (used for lookups) and localized names (used for display)

## Potential Edge Cases and Challenges

1. **Missing translations**: Some countries might not have names in all languages
   - Solution: Fall back to English names when a translation is missing

2. **Character encoding issues**: Some languages (Arabic, Chinese, etc.) might require special handling
   - Solution: Ensure proper font support in the renderer

3. **Text directionality**: Languages like Arabic and Hebrew are right-to-left
   - Solution: Consider text layout direction when positioning labels

4. **Label sizing**: Different languages may require different label sizes
   - Solution: Consider dynamic sizing based on text length

5. **Country name disambiguation**: Some countries might have similar names in certain languages
   - Solution: Maintain unique identifiers (like ISO codes) independent of display name

6. **Database inconsistencies**: The database might have inconsistent naming conventions
   - Solution: Add validation and normalization of data

## Test Cases

The following test cases should be implemented:

1. Basic language selection test:
   - Verify that the correct language column is selected based on the language parameter

2. Language validation test:
   - Verify that invalid language codes are rejected with appropriate error messages
   - Verify that the default language (English) is used when no language is specified

3. Missing translation test:
   - Verify fallback to English when a translation is missing

4. Character encoding test:
   - Verify that non-Latin characters are properly displayed

5. Integration test:
   - Verify that the end-to-end process works with different languages

## Implementation Order

1. Create the language configuration module
2. Update the CLI argument parsing
3. Modify data retrieval functions
4. Update label rendering
5. Write tests
6. Update documentation

This implementation plan provides a structured approach to adding multilingual support to the maps CLI while addressing potential challenges and edge cases. 