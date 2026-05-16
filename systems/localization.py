"""
Localization System
Manages multi-language support for the game
"""
import json
import os
from typing import Optional, Dict, Any


class LocalizationManager:
    """Manages game text localization"""

    def __init__(self, default_language: str = "en"):
        self.current_language = default_language
        self.languages: Dict[str, Dict[str, Any]] = {}
        self.available_languages = ["en", "vi"]
        self.pref_file = os.path.join(".", "language_preference.txt")

        # Load language preference from file if exists
        self.load_language_preference()
        self.load_all_languages()

    def load_all_languages(self) -> None:
        """Load all available language files"""
        base_path = os.path.join(os.path.dirname(__file__), "..", "data")

        for lang in self.available_languages:
            lang_file = os.path.join(base_path, f"localization_{lang}.json")
            try:
                if os.path.exists(lang_file):
                    with open(lang_file, "r", encoding="utf-8-sig") as f:
                        self.languages[lang] = json.load(f)
                else:
                    print(f"Warning: Language file not found: {lang_file}")
                    self.languages[lang] = {}
            except Exception as e:
                print(f"Error loading language {lang}: {e}")
                self.languages[lang] = {}

    def load_language_preference(self) -> None:
        """Load language preference from file"""
        try:
            if os.path.exists(self.pref_file):
                with open(self.pref_file, "r", encoding="utf-8") as f:
                    lang = f.read().strip()
                    if lang in self.available_languages:
                        self.current_language = lang
        except Exception as e:
            print(f"Error loading language preference: {e}")

    def save_language_preference(self) -> None:
        """Save current language preference to file"""
        try:
            with open(self.pref_file, "w", encoding="utf-8") as f:
                f.write(self.current_language)
        except Exception as e:
            print(f"Error saving language preference: {e}")

    def set_language(self, language: str) -> bool:
        """Set current language and save preference"""
        if language in self.available_languages:
            self.current_language = language
            self.save_language_preference()
            return True
        return False

    def get_language(self) -> str:
        """Get current language code"""
        return self.current_language

    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        names = {
            "en": "English",
            "vi": "Tiếng Việt",
        }
        return names.get(lang_code, lang_code)

    def translate(self, key: str, default: str = "") -> str:
        """
        Translate a key to current language
        Use dot notation for nested keys: "menu.play_button"
        """
        lang_data = self.languages.get(self.current_language, {})

        # Handle nested keys with dot notation
        keys = key.split(".")
        value = lang_data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if isinstance(value, str) else default

    def _(self, key: str, default: str = "") -> str:
        """Shorthand for translate"""
        return self.translate(key, default)


# Global instance
_localization_manager: Optional[LocalizationManager] = None


def get_localization_manager() -> LocalizationManager:
    """Get or create global localization manager"""
    global _localization_manager
    if _localization_manager is None:
        _localization_manager = LocalizationManager()
    return _localization_manager


def _(key: str, default: str = "") -> str:
    """Global translate function"""
    return get_localization_manager().translate(key, default)
