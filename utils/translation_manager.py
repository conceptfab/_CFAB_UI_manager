import json
import logging
import os
from typing import Dict, List, Optional

from PyQt6.QtWidgets import QWidget

from utils.config_cache import config_cache

logger = logging.getLogger(__name__)


class TranslationManager:
    _instance = None
    _translatable_widgets: List[QWidget] = []
    _config_path: Optional[str] = None
    _translations: Dict[str, Dict] = {}
    _current_language: str = "pl"
    _translation_cache: Dict[str, Dict[str, str]] = (
        {}
    )  # Cache dla przetłumaczonych kluczy
    _available_languages_cache: Optional[List[str]] = (
        None  # Cache dla dostępnych języków
    )

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
            cls._translatable_widgets = []
            cls._translations = {}
            cls._current_language = "pl"
            cls._translation_cache = {}
            cls._available_languages_cache = None
        return cls._instance

    @classmethod
    def initialize(
        cls,
        config_path: Optional[str] = None,
        default_language: str = "pl",
        app_logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Inicjalizuje menedżer tłumaczeń.
        Ładuje język z konfiguracji i wczytuje odpowiednie tłumaczenia.
        """
        if not cls._instance:
            cls.__new__(cls)

        inst = cls.get_instance()

        # Użyj przekazanego loggera lub globalnego, jeśli nie został dostarczony
        effective_logger = app_logger if app_logger else logger

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
        inst._clear_caches()  # Wyczyszczenie cache przy inicjalizacji
        effective_logger.debug(  # Zmieniono z info na debug
            f"TranslationManager: zainicjalizowano. Język ustawiony na: {inst._current_language}"
        )
        inst._load_translation_internal(
            inst._current_language
        )  # Zmieniono na metodę instancji

    # Metody przeniesione i dostosowane z Translatora (jako metody instancji)
    def _load_translation_internal(self, language_code: str) -> None:
        """
        Wczytuje tłumaczenia dla określonego języka. (Metoda instancji)
        Ulepszone cachowanie i walidacja.
        """
        if language_code in self._translations and self._translations[language_code]:
            logger.debug(
                f"TranslationManager: Tłumaczenia dla {language_code} już załadowane i niepuste."
            )
            return

        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations"
        )
        file_path = os.path.join(translations_dir, f"{language_code}.json")

        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    if not isinstance(loaded_data, dict):
                        logger.error(
                            f"TranslationManager: Plik tłumaczeń dla {language_code} nie zawiera obiektu JSON na najwyższym poziomie: {file_path}"
                        )
                        self._translations[language_code] = {}
                    else:
                        self._translations[language_code] = loaded_data
                        self._translation_cache[language_code] = (
                            {}
                        )  # Inicjalizacja cache dla tego języka
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
        except json.JSONDecodeError as e:
            logger.error(
                f"TranslationManager: błąd dekodowania JSON dla {language_code} z {file_path}: {e}"
            )
            self._translations[language_code] = {}
        except Exception as e:
            logger.error(
                f"TranslationManager: błąd ładowania tłumaczeń dla {language_code} z {file_path}: {e}"
            )
            self._translations[language_code] = {}

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
        if self._current_language == language_code and self._translations.get(
            language_code
        ):
            logger.debug(
                f"TranslationManager: Język {language_code} jest już ustawiony i załadowany."
            )
            return True

        # self._load_translation_internal(language_code) # Ładowanie jest teraz bardziej leniwe, jeśli potrzeba
        # Sprawdzenie, czy plik tłumaczeń istnieje, zanim spróbujemy go załadować
        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations"
        )
        file_path = os.path.join(translations_dir, f"{language_code}.json")
        if not os.path.exists(file_path):
            logger.warning(
                f"TranslationManager: Plik tłumaczeń dla języka {language_code} nie istnieje w {file_path}. Nie można zmienić języka."
            )
            return False

        self._load_translation_internal(
            language_code
        )  # Upewnij się, że jest załadowany

        if self._translations.get(language_code):
            logger.debug(f"TranslationManager: zmiana języka na {language_code}")
            self._current_language = language_code
            self._clear_caches(
                specific_language=language_code, clear_available_languages=False
            )  # Czyścimy cache dla nowego języka
            self.save_language_to_config_internal(language_code)
            self.update_all_widgets_internal()
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
        Zwraca listę dostępnych języków (na podstawie załadowanych plików).
        Używa cache.
        """
        if self._available_languages_cache is not None:
            return self._available_languages_cache

        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations"
        )
        available = []
        if os.path.exists(translations_dir):
            for f_name in os.listdir(translations_dir):
                if f_name.endswith(".json") and os.path.isfile(
                    os.path.join(translations_dir, f_name)
                ):
                    lang_code = f_name[:-5]
                    # Prosta walidacja nazwy pliku (np. czy składa się z 2 liter)
                    if len(lang_code) == 2 and lang_code.isalpha():
                        available.append(lang_code)
                    else:
                        logger.warning(
                            f"TranslationManager: Pomięto plik o niestandardowej nazwie: {f_name}"
                        )

        self._available_languages_cache = sorted(
            list(set(available))
        )  # Usuń duplikaty i posortuj
        return self._available_languages_cache

    def translate_internal(self, key: str, *args, **kwargs) -> str:
        """
        Tłumaczy podany klucz na aktualny język. (Metoda instancji)
        Użycie zoptymalizowanego cache dla tłumaczeń.
        """
        default_value = kwargs.get("default", key)

        # Optymalizacja: szybkie sprawdzenie cache bez zagnieżdżonych if-ów
        cache_dict = self._translation_cache.get(self._current_language, {})
        cached_translation = cache_dict.get(key)

        if cached_translation:
            if args and isinstance(cached_translation, str):
                try:
                    return cached_translation.format(*args)
                except Exception:
                    pass  # W przypadku błędu formatowania, kontynuuj bez cache
            elif not args and isinstance(cached_translation, str):
                return cached_translation

        # Jeśli nie ma w cache lub formatowanie zawiodło, normalne tłumaczenie
        try:
            parts = key.split(".")
            # Upewnij się, że tłumaczenia dla bieżącego języka są załadowane
            if self._current_language not in self._translations:
                self._load_translation_internal(self._current_language)

            translation_map = self._translations.get(self._current_language, {})

            current_level = translation_map
            for part in parts:
                if isinstance(current_level, dict):
                    current_level = current_level.get(
                        part
                    )  # Użyj .get() dla bezpieczeństwa
                    if current_level is None:
                        raise KeyError(f"Część klucza '{part}' nie znaleziona.")
                else:
                    raise KeyError(
                        f"Niepełna ścieżka klucza: {key}, napotkano wartość niebędącą słownikiem."
                    )

            if not isinstance(current_level, str):
                logger.warning(
                    f"Translation for key '{key}' is not a string: {current_level}. Returning default."
                )
                # Zapisz nie-stringową wartość do cache, aby uniknąć powtarzania logów
                if self._current_language not in self._translation_cache:
                    self._translation_cache[self._current_language] = {}
                self._translation_cache[self._current_language][
                    key
                ] = default_value  # Lub specjalny marker
                return default_value

            # Zapisz do cache przed formatowaniem
            if self._current_language not in self._translation_cache:
                self._translation_cache[self._current_language] = {}
            self._translation_cache[self._current_language][key] = current_level

            if args:
                return current_level.format(*args)
            return current_level

        except (KeyError, TypeError, IndexError) as e:  # Dodano IndexError
            logger.warning(
                f"TranslationManager: Nie znaleziono tłumaczenia lub błąd formatowania dla klucza '{key}' w języku '{self._current_language}'. Błąd: {e}. Zwracam: {default_value}"
            )
            # Zapisz klucz do cache jako nieprzetłumaczony, aby uniknąć powtarzania logów
            if self._current_language not in self._translation_cache:
                self._translation_cache[self._current_language] = {}
            self._translation_cache[self._current_language][key] = default_value
            return default_value

    def _clear_caches(
        self,
        specific_language: Optional[str] = None,
        clear_available_languages: bool = True,
    ) -> None:
        """Wyczyść wewnętrzne cache tłumaczeń."""
        if specific_language:
            if specific_language in self._translation_cache:
                self._translation_cache[specific_language] = {}
                logger.debug(
                    f"TranslationManager: Wyczyszczono cache tłumaczeń dla języka: {specific_language}"
                )
        else:
            self._translation_cache = {}
            logger.debug("TranslationManager: Wyczyszczono cały cache tłumaczeń.")

        if clear_available_languages:
            self._available_languages_cache = None
            logger.debug("TranslationManager: Wyczyszczono cache dostępnych języków.")

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
            logger.debug(
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
