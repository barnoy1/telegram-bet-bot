"""Language detection and translation service."""

import yaml
import os
from pathlib import Path
from typing import Dict, Optional
import logging
import random
import arabic_reshaper
from bidi.algorithm import get_display

logger = logging.getLogger(__name__)


class LanguageService:
    """Service for detecting group language and loading translations."""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'he': 'Hebrew',
        'ru': 'Russian',
    }

    def __init__(self, storage):
        self.storage = storage
        self._translations_cache: Dict[str, Dict] = {}
        self._language_meta: Dict[str, Dict] = {}  # Store metadata like direction
        self._load_translations()

    def _load_translations(self):
        """Load all translation files from persona/lang directory."""
        lang_dir = Path(__file__).parent.parent.parent / 'persona' / 'lang'

        for lang_code in self.SUPPORTED_LANGUAGES:
            lang_file = lang_dir / f'{lang_code}.yaml'
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        self._translations_cache[lang_code] = data
                        # Store metadata if available
                        if 'meta' in data:
                            self._language_meta[lang_code] = data['meta']
                    logger.info(f"Loaded translations for {lang_code}")
                except Exception as e:
                    logger.error(f"Failed to load translations for {lang_code}: {e}")
            else:
                logger.warning(f"Translation file not found: {lang_file}")

    def detect_group_language(self, group_id: int, fallback_language: str = 'en') -> str:
        """Detect the most common language for a group."""
        stats = self.storage.get_language_stats(group_id)
        
        logger.info(f"Language stats for group {group_id}: {stats}")
        
        if not stats:
            logger.info(f"No language stats for group {group_id}, using fallback: {fallback_language}")
            return fallback_language
        
        # Find language with highest count
        detected_lang = max(stats, key=stats.get)
        logger.info(f"Detected language for group {group_id}: {detected_lang} (stats: {stats})")
        
        # Ensure detected language is supported
        if detected_lang not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Detected language {detected_lang} not supported, using fallback: {fallback_language}")
            return fallback_language
        
        return detected_lang

    def get_translation(self, group_id: int, key_path: str, fallback_language: str = 'en') -> str:
        """Get a translated string for a group.
        
        Args:
            group_id: The group ID
            key_path: Dot-separated path to translation key (e.g., 'start.header')
            fallback_language: Language to use if detection fails
        
        Returns:
            The translated string
        """
        lang = self.detect_group_language(group_id, fallback_language)
        return self.get_translation_by_lang(lang, key_path)

    def get_translation_by_lang(self, lang: str, key_path: str) -> str:
        """Get a translation by language code.
        
        Args:
            lang: Language code (e.g., 'en', 'he')
            key_path: Dot-separated path to translation key (e.g., 'start.header')
        
        Returns:
            The translated string, or the key path if not found
        """
        if lang not in self._translations_cache:
            logger.warning(f"Translations not loaded for language: {lang}")
            return key_path
        
        translations = self._translations_cache[lang]
        keys = key_path.split('.')
        
        try:
            value = translations
            for key in keys:
                value = value[key]
            # Handle lists by selecting a random element
            if isinstance(value, list):
                value = random.choice(value)
            return str(value)
        except (KeyError, TypeError):
            logger.warning(f"Translation key not found: {key_path} for language {lang}")
            return key_path

    def is_rtl(self, lang: str) -> bool:
        """Check if a language is right-to-left based on metadata."""
        if lang in self._language_meta:
            return self._language_meta[lang].get('direction', 'ltr') == 'rtl'
        # Fallback to hardcoded check for backward compatibility
        return lang == 'he'

    def format_message(self, group_id: int, message: str, fallback_language: str = 'en') -> str:
        """Format a message with appropriate direction based on language.

        Args:
            group_id: The group ID
            message: The message to format
            fallback_language: Language to use if detection fails

        Returns:
            Formatted message with proper RTL/LTR handling
        """
        lang = self.detect_group_language(group_id, fallback_language)

        if self.is_rtl(lang):
            # Use arabic-reshaper and python-bidi for proper Hebrew display
            try:
                reshaped_text = arabic_reshaper.reshape(message)
                bidi_text = get_display(reshaped_text)
                return bidi_text
            except Exception as e:
                logger.warning(f"Failed to reshape Hebrew text: {e}, falling back to basic RTL")
                return f'\u202B{message}\u202C'
        return message
