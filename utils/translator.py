import json
import logging
import os
from typing import Dict, Optional

from .config_cache import config_cache

logger = logging.getLogger(__name__)


class Translator:
    """
    Klasa odpowiedzialna za obsługę tłumaczeń w aplikacji.
    """

    def __init__(self, default_language: str = "pl"):
        """
        Inicjalizuje translator.

        Args:
            default_language (str): Domyślny kod języka (np. 'pl', 'en')
        """
        self._translations: Dict[str, Dict] = {}
        self._current_language = default_language
        logger.debug(f"Translator: inicjalizacja z językiem {default_language}")
        self._load_translation(default_language)

    def _load_translation(self, language_code: str) -> None:
        """
        Wczytuje tłumaczenia dla określonego języka.

        Args:
            language_code (str): Kod języka do wczytania
        """
        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations"
        )

        file_path = os.path.join(translations_dir, f"{language_code}.json")

        try:
            # Use cached translation loading
            self._translations[language_code] = config_cache.get_translations(file_path)
            logger.debug(
                f"Translator: załadowano tłumaczenia dla języka {language_code} (cached)"
            )
        except Exception as e:
            logger.error(
                f"Translator: błąd ładowania tłumaczeń dla {language_code}: {e}"
            )

    def set_language(self, language_code: str) -> bool:
        """
        Ustawia aktualny język.

        Args:
            language_code (str): Kod języka (np. 'pl', 'en')

        Returns:
            bool: True jeśli język został zmieniony, False jeśli nie znaleziono tłumaczeń
        """
        # Jeśli nie mamy jeszcze wczytanych tłumaczeń dla tego języka, spróbuj je wczytać
        if language_code not in self._translations:
            self._load_translation(language_code)

        if language_code in self._translations:
            logger.debug(f"Translator: zmiana języka na {language_code}")
            self._current_language = language_code
            return True

        logger.warning(
            f"Translator: nie znaleziono tłumaczeń dla języka {language_code}"
        )
        return False

    def get_language(self) -> str:
        """
        Zwraca aktualny kod języka.

        Returns:
            str: Kod aktualnego języka
        """
        return self._current_language

    def get_available_languages(self) -> list[str]:
        """
        Zwraca listę dostępnych języków.

        Returns:
            list[str]: Lista kodów dostępnych języków
        """
        return list(self._translations.keys())

    def translate(self, key: str, *args) -> str:
        """
        Tłumaczy podany klucz na aktualny język.

        Args:
            key (str): Klucz do przetłumaczenia (np. 'app.menu.file')
            *args: Argumenty do formatowania tekstu

        Returns:
            str: Przetłumaczony tekst lub klucz jeśli nie znaleziono tłumaczenia
        """
        try:
            # Dzielimy klucz na części (np. 'app.menu.file' -> ['app', 'menu', 'file'])
            parts = key.split(".")

            # Pobieramy tłumaczenie dla aktualnego języka
            translation = self._translations[self._current_language]

            # Przechodzimy przez wszystkie części klucza
            for part in parts:
                translation = translation[part]

            # Jeśli są argumenty, formatujemy tekst
            if args:
                return translation.format(*args)
            return translation

        except (KeyError, TypeError):
            # Jeśli nie znaleziono tłumaczenia, zwracamy klucz
            return key

    def get_translation(self, key: str, language_code: Optional[str] = None) -> str:
        """
        Pobiera tłumaczenie dla konkretnego języka.

        Args:
            key (str): Klucz do przetłumaczenia
            language_code (str, optional): Kod języka. Jeśli None, używa aktualnego języka.

        Returns:
            str: Przetłumaczony tekst lub klucz jeśli nie znaleziono tłumaczenia
        """
        if language_code is None:
            language_code = self._current_language

        try:
            parts = key.split(".")
            translation = self._translations[language_code]
            for part in parts:
                translation = translation[part]
            return translation
        except (KeyError, TypeError):
            return key
