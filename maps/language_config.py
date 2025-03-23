"""
Language configuration module for maps package.

This module provides functionality for handling and validating
different language options for map labels.
"""

from typing import Dict, List, Optional

# Map language codes to their corresponding database column names
LANGUAGE_MAPPINGS: Dict[str, str] = {
    "en": "name_en",  # English
    "ar": "name_ar",  # Arabic
    "bn": "name_bn",  # Bengali
    "de": "name_de",  # German
    "es": "name_es",  # Spanish
    "fa": "name_fa",  # Persian/Farsi
    "fr": "name_fr",  # French
    "el": "name_el",  # Greek
    "he": "name_he",  # Hebrew
    "hi": "name_hi",  # Hindi
    "hu": "name_hu",  # Hungarian
    "id": "name_id",  # Indonesian
    "it": "name_it",  # Italian
    "ja": "name_ja",  # Japanese
    "ko": "name_ko",  # Korean
    "nl": "name_nl",  # Dutch
    "pl": "name_pl",  # Polish
    "pt": "name_pt",  # Portuguese
    "ru": "name_ru",  # Russian
    "sv": "name_sv",  # Swedish
    "tr": "name_tr",  # Turkish
    "uk": "name_uk",  # Ukrainian
    "ur": "name_ur",  # Urdu
    "vi": "name_vi",  # Vietnamese
    "zh": "name_zh",  # Chinese (Simplified)
    "zht": "name_zht",  # Chinese (Traditional)
}

# Default language column to use if no language is specified or if a language is not supported
DEFAULT_LANGUAGE_COLUMN: str = "name"


def get_supported_languages() -> List[str]:
    """
    Get a list of supported language codes.

    Returns:
        List of supported language codes (e.g., 'en', 'fr', 'es', etc.)
    """
    return sorted(list(LANGUAGE_MAPPINGS.keys()))


def is_language_supported(language_code: Optional[str]) -> bool:
    """
    Check if a language code is supported.

    Args:
        language_code: Two-letter language code to check

    Returns:
        True if the language is supported, False otherwise
    """
    if not language_code:
        return False
    return language_code in LANGUAGE_MAPPINGS


def get_language_column(language_code: str, fallback: Optional[str] = None) -> str:
    """
    Get the database column name for a language code.

    Args:
        language_code: Two-letter language code
        fallback: Optional fallback column name if the language is not supported
                 If None, DEFAULT_LANGUAGE_COLUMN will be used

    Returns:
        Database column name for the language code (e.g., 'name_en', 'name_fr')
        or the fallback column name if the language is not supported
    """
    if not fallback:
        fallback = DEFAULT_LANGUAGE_COLUMN

    return LANGUAGE_MAPPINGS.get(language_code, fallback)


def get_language_name(language_code: str) -> str:
    """
    Get the full name of a language from its code.

    Args:
        language_code: Two-letter language code

    Returns:
        Full name of the language, or "Unknown" if the language code is not supported
    """
    language_names = {
        "en": "English",
        "ar": "Arabic",
        "bn": "Bengali",
        "de": "German",
        "es": "Spanish",
        "fa": "Persian",
        "fr": "French",
        "el": "Greek",
        "he": "Hebrew",
        "hi": "Hindi",
        "hu": "Hungarian",
        "id": "Indonesian",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "nl": "Dutch",
        "pl": "Polish",
        "pt": "Portuguese",
        "ru": "Russian",
        "sv": "Swedish",
        "tr": "Turkish",
        "uk": "Ukrainian",
        "ur": "Urdu",
        "vi": "Vietnamese",
        "zh": "Chinese (Simplified)",
        "zht": "Chinese (Traditional)",
    }
    return language_names.get(language_code, "Unknown")


def get_display_info() -> List[Dict[str, str]]:
    """
    Get displayable information about supported languages.

    Returns:
        List of dictionaries with 'code' and 'name' keys for each supported language
    """
    return [
        {"code": code, "name": get_language_name(code)}
        for code in get_supported_languages()
    ]
