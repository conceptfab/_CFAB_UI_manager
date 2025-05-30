import json
import logging
import os
from typing import Dict, List, Optional

from PyQt6.QtWidgets import QWidget

from utils.config_cache import (
    config_cache,
)  # Zmieniono z .config_cache; Zachowujemy, jeśli ConfigCache jest nadal używany do innych celów

logger = logging.getLogger(__name__)


class TranslationManager:
    _instance = None
    # Usunięto _translator, funkcjonalność Translatora zostanie wchłonięta
    _translatable_widgets: List[QWidget] = []
    _config_path: Optional[str] = None  # Zapewnienie, że _config_path może być None
    _translations: Dict[str, Dict] = {}  # Przeniesione z Translatora
    _current_language: str = "pl"  # Domyślny język, przeniesione z Translatora

    def __new__(cls, *args, **kwargs):  # Dodano *args, **kwargs dla elastyczności
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
            # Inicjalizacja atrybutów instancji tutaj, jeśli są specyficzne dla instancji
            # Jednak większość logiki inicjalizacyjnej jest w initialize()
            cls._translatable_widgets = []
            cls._translations = {}
            cls._current_language = (
                "pl"  # Ustawienie domyślnego języka przy tworzeniu instancji
            )
        return cls._instance

    @classmethod
    def initialize(
        cls, config_path: Optional[str] = None, default_language: str = "pl"
    ) -> None:
        """
        Inicjalizuje menedżer tłumaczeń.
        Ładuje język z konfiguracji i wczytuje odpowiednie tłumaczenia.
        """
        if not cls._instance:  # Upewnienie się, że instancja istnieje
            cls.__new__(cls)  # Tworzenie instancji, jeśli nie istnieje

        inst = cls.get_instance()  # Praca na instancji

        inst._config_path = config_path

        # Ustalenie języka początkowego
        # 1. Język przekazany w argumencie (jeśli inny niż domyślny "pl")
        # 2. Język z konfiguracji
        # 3. Domyślny język ("pl")

        initial_language = default_language
        if config_path:
            lang_from_config = (
                inst._load_language_from_config_internal()
            )  # Zmieniono na metodę instancji
            if lang_from_config:
                initial_language = lang_from_config

        inst._current_language = initial_language
        logger.info(  # Zmieniono z debug na info
            f"TranslationManager: zainicjalizowano. Język ustawiony na: {inst._current_language}"
        )
        inst._load_translation_internal(
            inst._current_language
        )  # Zmieniono na metodę instancji

    # Metody przeniesione i dostosowane z Translatora (jako metody instancji)
    def _load_translation_internal(self, language_code: str) -> None:
        """
        Wczytuje tłumaczenia dla określonego języka. (Metoda instancji)
        """
        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations"
        )
        file_path = os.path.join(translations_dir, f"{language_code}.json")

        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self._translations[language_code] = json.load(f)
                logger.debug(
                    f"TranslationManager: załadowano tłumaczenia dla języka {language_code} z {file_path}"
                )
            else:
                logger.warning(
                    f"TranslationManager: Plik tłumaczeń nie istnieje: {file_path}"
                )
                self._translations[language_code] = (
                    {}
                )  # Puste tłumaczenia, jeśli plik nie istnieje
        except Exception as e:
            logger.error(
                f"TranslationManager: błąd ładowania tłumaczeń dla {language_code} z {file_path}: {e}"
            )
            self._translations[language_code] = (
                {}
            )  # Puste tłumaczenia w przypadku błędu

    @classmethod
    def load_translations(
        cls, translations_dir: Optional[str] = None, language_code: Optional[str] = None
    ) -> Dict:
        """
        Publiczna metoda klasowa do ładowania tłumaczeń.
        Może być używana przez ResourceManager lub inne komponenty.
        """
        inst = cls.get_instance()
        lang_to_load = language_code if language_code else inst._current_language

        if translations_dir is None:
            translations_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "translations",
            )

        file_path = os.path.join(translations_dir, f"{lang_to_load}.json")
        loaded_translations = {}

        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    loaded_translations = json.load(f)
                inst._translations[lang_to_load] = loaded_translations
                logger.debug(
                    f"TranslationManager: Załadowano (przez load_translations) tłumaczenia dla języka {lang_to_load} z {file_path}"
                )
            else:
                logger.warning(
                    f"TranslationManager: Plik tłumaczeń (przez load_translations) nie istnieje: {file_path}"
                )
                inst._translations[lang_to_load] = {}
        except Exception as e:
            logger.error(
                f"TranslationManager: Błąd ładowania (przez load_translations) tłumaczeń dla {lang_to_load} z {file_path}: {e}"
            )
            inst._translations[lang_to_load] = {}
        return inst._translations.get(lang_to_load, {})

    def set_language_internal(self, language_code: str) -> bool:
        """
        Ustawia aktualny język. (Metoda instancji)
        """
        if language_code not in self._translations:
            self._load_translation_internal(language_code)

        if self._translations.get(
            language_code
        ):  # Sprawdzenie, czy tłumaczenia istnieją i nie są puste
            logger.debug(f"TranslationManager: zmiana języka na {language_code}")
            self._current_language = language_code
            # Zapisz nowy język do konfiguracji
            self.save_language_to_config_internal(
                language_code
            )  # Zmieniono na metodę instancji
            # Zaktualizuj wszystkie widgety
            self.update_all_widgets_internal()  # Zmieniono na metodę instancji
            return True

        logger.warning(
            f"TranslationManager: nie znaleziono lub puste tłumaczenia dla języka {language_code}"
        )
        return False

    def get_language_internal(self) -> str:
        """
        Zwraca aktualny kod języka. (Metoda instancji)
        """
        return self._current_language

    def get_available_languages_internal(self) -> list[str]:
        """
        Zwraca listę dostępnych języków (na podstawie załadowanych plików). (Metoda instancji)
        """
        # Można by dynamicznie skanować katalog translations
        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations"
        )
        available = []
        if os.path.exists(translations_dir):
            for f_name in os.listdir(translations_dir):
                if f_name.endswith(".json"):
                    available.append(f_name[:-5])
        return available
        # return list(self._translations.keys()) # Stara implementacja, zwraca tylko już załadowane

    def translate_internal(self, key: str, *args) -> str:
        """
        Tłumaczy podany klucz na aktualny język. (Metoda instancji)
        """
        try:
            parts = key.split(".")
            translation_map = self._translations.get(self._current_language, {})

            current_level = translation_map
            for part in parts:
                if isinstance(current_level, dict):
                    current_level = current_level[part]
                else:  # Jeśli ścieżka prowadzi do wartości niebędącej słownikiem przed końcem
                    raise KeyError(f"Niepełna ścieżka klucza: {key}")

            if args and isinstance(current_level, str):
                return current_level.format(*args)

            if not isinstance(current_level, str):
                logger.warning(
                    f"Translation for key '{key}' is not a string: {current_level}"
                )
                return key  # Zwróć klucz, jeśli tłumaczenie nie jest stringiem

            return current_level

        except (KeyError, TypeError) as e:
            logger.warning(
                f"TranslationManager: Nie znaleziono tłumaczenia dla klucza '{key}' w języku '{self._current_language}'. Błąd: {e}"
            )
            return key

    # Metody klasowe do zarządzania instancją (Singleton) i interfejsem publicznym
    @classmethod
    def get_instance(cls) -> "TranslationManager":
        """
        Zwraca instancję TranslationManager (Singleton).
        """
        if cls._instance is None:
            # Inicjalizacja z domyślnymi wartościami, jeśli get_instance jest wywołane przed initialize
            logger.warning(
                "TranslationManager.get_instance() wywołane przed initialize(). Używam domyślnych ustawień."
            )
            cls.initialize()
        return cls._instance

    @classmethod
    def translate(cls, key: str, *args) -> str:
        """
        Publiczna metoda klasowa do tłumaczenia.
        """
        return cls.get_instance().translate_internal(key, *args)

    @classmethod
    def set_language(cls, language_code: str) -> bool:
        """
        Publiczna metoda klasowa do ustawiania języka.
        """
        return cls.get_instance().set_language_internal(language_code)

    @classmethod
    def get_current_language(cls) -> str:
        """
        Publiczna metoda klasowa do pobierania aktualnego języka.
        """
        return cls.get_instance().get_language_internal()

    @classmethod
    def get_available_languages(cls) -> list[str]:
        """
        Publiczna metoda klasowa do pobierania dostępnych języków.
        """
        return cls.get_instance().get_available_languages_internal()

    # Pozostałe metody, dostosowane do bycia metodami instancji lub klasowymi
    def _load_language_from_config_internal(self) -> Optional[str]:
        """
        Wczytuje ustawiony język z pliku konfiguracyjnego. (Metoda instancji)
        """
        if not self._config_path or not os.path.exists(self._config_path):
            logger.info(
                "TranslationManager: brak pliku konfiguracyjnego, nie można wczytać języka."
            )
            return None  # Zwraca None zamiast "pl"

        try:
            # Użycie config_cache, jeśli jest to preferowane i dostosowane
            # config = config_cache.get_config(self._config_path)
            # Na razie bezpośrednie wczytanie dla uproszczenia
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            language = config.get("language")
            if language:
                logger.debug(
                    f"TranslationManager: wczytano język z konfiguracji: {language}"
                )
            else:
                logger.debug(
                    "TranslationManager: brak ustawienia języka w konfiguracji."
                )
            return language
        except Exception as e:
            logger.error(
                f"TranslationManager: błąd wczytywania konfiguracji języka: {e}"
            )
            return None

    def save_language_to_config_internal(self, language_code: str) -> bool:
        """
        Zapisuje ustawiony język do pliku konfiguracyjnego. (Metoda instancji)
        """
        if not self._config_path:
            logger.warning(
                "TranslationManager: brak ścieżki do pliku konfiguracyjnego, nie można zapisać języka."
            )
            return False

        try:
            config = {}
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

            config["language"] = language_code
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.debug(
                f"TranslationManager: zapisano język {language_code} do konfiguracji: {self._config_path}"
            )
            # Inwalidacja cache dla pliku konfiguracyjnego, jeśli używamy config_cache
            if hasattr(config_cache, "invalidate"):
                config_cache.invalidate(self._config_path)
            return True
        except Exception as e:
            logger.error(
                f"TranslationManager: błąd zapisywania konfiguracji języka: {e}"
            )
            return False

    @classmethod
    def register_widget(cls, widget: QWidget) -> None:
        inst = cls.get_instance()
        if widget not in inst._translatable_widgets:
            inst._translatable_widgets.append(widget)

    @classmethod
    def unregister_widget(cls, widget: QWidget) -> None:
        inst = cls.get_instance()
        if widget in inst._translatable_widgets:
            inst._translatable_widgets.remove(widget)

    def update_all_widgets_internal(self) -> None:  # Metoda instancji
        """
        Aktualizuje wszystkie zarejestrowane widgety.
        """
        logger.debug(
            f"TranslationManager: Aktualizacja {len(self._translatable_widgets)} widgetów."
        )
        for widget in self._translatable_widgets:
            if hasattr(widget, "update_translations"):
                try:
                    widget.update_translations()
                except Exception as e:
                    logger.error(
                        f"TranslationManager: Błąd podczas aktualizacji widgetu {widget}: {e}"
                    )
            else:
                logger.warning(
                    f"TranslationManager: Widget {widget} nie ma metody update_translations."
                )


# Usunięcie klasy Translator z tego pliku, jeśli była tu zdefiniowana,
# lub zapewnienie, że nie jest już importowana/używana, jeśli była w osobnym pliku.
# Należy usunąć plik translator.py
