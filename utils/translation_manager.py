import json
import logging
import os
from typing import Dict, List, Optional

from PyQt6.QtWidgets import QWidget

from .config_cache import config_cache
from .translator import Translator

logger = logging.getLogger(__name__)


class TranslationManager:
    _instance = None
    _translator: Optional[Translator] = None
    _translatable_widgets: List[QWidget] = []
    _config_path: str = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config_path: str = None) -> None:
        """
        Inicjalizuje menedżer tłumaczeń.

        Args:
            config_path (str, optional): Ścieżka do pliku konfiguracyjnego
        """
        if cls._translator is None:
            cls._config_path = config_path
            default_language = cls._load_language_from_config()
            logger.debug(
                f"TranslationManager: inicjalizacja z językiem {default_language}"
            )
            cls._translator = Translator(default_language)

    @classmethod
    def _load_language_from_config(cls) -> str:
        """
        Wczytuje ustawiony język z pliku konfiguracyjnego.
        Jeśli nie znaleziono pliku lub ustawienia, zwraca domyślny język (pl).

        Returns:
            str: Kod języka (pl/en)
        """
        if not cls._config_path or not os.path.exists(cls._config_path):
            logger.info(
                "TranslationManager: brak pliku konfiguracyjnego, używam domyślnego języka (pl)"
            )
            return "pl"

        try:
            # Use cached configuration loading
            config = config_cache.get_config(cls._config_path)
            language = config.get("language", "pl")
            logger.debug(
                f"TranslationManager: wczytano język z konfiguracji (cached): {language}"
            )
            return language
        except Exception as e:
            logger.error(
                f"TranslationManager: błąd wczytywania konfiguracji: {e}, używam domyślnego języka (pl)"
            )
            return "pl"

    @classmethod
    def save_language_to_config(cls, language_code: str) -> bool:
        """
        Zapisuje ustawiony język do pliku konfiguracyjnego.

        Args:
            language_code (str): Kod języka do zapisania

        Returns:
            bool: True jeśli zapisano pomyślnie, False w przeciwnym razie
        """
        if not cls._config_path:
            logger.warning("TranslationManager: brak ścieżki do pliku konfiguracyjnego")
            return False

        try:
            # Wczytaj istniejącą konfigurację
            config = {}
            if os.path.exists(cls._config_path):
                with open(cls._config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

            # Zaktualizuj język
            config["language"] = language_code  # Zapisz zaktualizowaną konfigurację
            with open(cls._config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.debug(
                f"TranslationManager: zapisano język {language_code} do konfiguracji"
            )
            return True
        except Exception as e:
            logger.error(f"TranslationManager: błąd zapisywania konfiguracji: {e}")
            return False

    @classmethod
    def get_translator(cls) -> Translator:
        """
        Zwraca instancję translatora.
        """
        if cls._translator is None:
            cls.initialize()
        return cls._translator

    @classmethod
    def set_language(cls, language_code: str) -> bool:
        """
        Ustawia język dla całej aplikacji.
        """
        if cls._translator is None:
            cls.initialize()

        if cls._translator.set_language(language_code):
            # Zapisz nowy język do konfiguracji
            cls.save_language_to_config(language_code)
            # Zaktualizuj wszystkie widgety
            cls.update_all_widgets()
            return True
        return False

    @classmethod
    def get_current_language(cls) -> str:
        """
        Zwraca aktualny kod języka.
        """
        if cls._translator is None:
            cls.initialize()
        return cls._translator.get_language()

    @classmethod
    def register_widget(cls, widget: QWidget) -> None:
        """
        Rejestruje widget do automatycznej aktualizacji tłumaczeń.
        """
        if widget not in cls._translatable_widgets:
            cls._translatable_widgets.append(widget)

    @classmethod
    def unregister_widget(cls, widget: QWidget) -> None:
        """
        Usuwa widget z listy automatycznej aktualizacji tłumaczeń.
        """
        if widget in cls._translatable_widgets:
            cls._translatable_widgets.remove(widget)

    @classmethod
    def update_all_widgets(cls) -> None:
        """
        Aktualizuje wszystkie zarejestrowane widgety.
        """
        for widget in cls._translatable_widgets:
            if hasattr(widget, "update_translations"):
                widget.update_translations()

    @classmethod
    def get_config(cls) -> dict:
        """
        Pobiera aktualną konfigurację aplikacji.

        Returns:
            dict: Konfiguracja aplikacji
        """
        if not cls._config_path or not os.path.exists(cls._config_path):
            logger.warning("TranslationManager: brak pliku konfiguracyjnego")
            return {}

        try:
            return config_cache.get_config(cls._config_path)
        except Exception as e:
            logger.error(f"TranslationManager: błąd pobierania konfiguracji: {e}")
            return {}
