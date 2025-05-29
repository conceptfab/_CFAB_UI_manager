import json
import os
from typing import Dict, Optional


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
        self._load_translations()

    def _load_translations(self) -> None:
        """
        Wczytuje wszystkie dostępne tłumaczenia.
        """
        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations"
        )

        for filename in os.listdir(translations_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]  # Usuwamy .json
                try:
                    file_path = os.path.join(translations_dir, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._translations[lang_code] = json.load(f)
                except Exception:
                    pass

    def set_language(self, language_code: str) -> bool:
        """
        Ustawia aktualny język.

        Args:
            language_code (str): Kod języka (np. 'pl', 'en')

        Returns:
            bool: True jeśli język został zmieniony, False jeśli nie znaleziono tłumaczeń
        """
        if language_code in self._translations:
            self._current_language = language_code
            return True
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
