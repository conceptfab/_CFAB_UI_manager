"""
Moduł zarządzania konfiguracją aplikacji.

Ten moduł oferuje jednolite API do zarządzania konfiguracją aplikacji,
zapewniając spójny dostęp, walidację, cachowanie oraz backup konfiguracji.
"""

import json
import logging
import os
import time
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.exceptions import CacheError, ConfigurationError, ErrorCode, ValidationError
from utils.validators import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Klasa zarządzająca konfiguracją aplikacji.

    Implementuje wzorzec Singleton oraz oferuje jednolite API do operacji na konfiguracji.
    Integruje funkcjonalność ładowania, walidacji, cachowania i zapisywania konfiguracji.
    """

    _instance = None
    _CONFIG_BACKUP_EXTENSION = ".bak"
    _DEFAULT_CONFIG_PATH = "config.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicjalizuje menedżer konfiguracji."""
        self.config_cache = {}
        self.config_path = None
        self.dirty = False  # Flaga wskazująca, że konfiguracja została zmieniona
        self.transaction_stack = []  # Stos transakcji do zarządzania zmianami
        self.logger = logging.getLogger(__name__)
        self.validator = ConfigValidator()

    def load_config(
        self, file_path: str = None, use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Ładuje konfigurację z pliku.

        Args:
            file_path: Ścieżka do pliku konfiguracyjnego. Jeśli None, używa domyślnej ścieżki.
            use_cache: Czy używać pamięci podręcznej, jeśli konfiguracja już była ładowana.

        Returns:
            Słownik z konfiguracją.

        Raises:
            ConfigurationError: Gdy wystąpi błąd podczas ładowania konfiguracji.
        """
        # Użyj domyślnej ścieżki, jeśli nie podano
        if file_path is None:
            if self.config_path is None:
                file_path = self._DEFAULT_CONFIG_PATH
            else:
                file_path = self.config_path

        # Zapisz ścieżkę dla późniejszych operacji
        self.config_path = file_path

        # Sprawdź, czy mamy już tę konfigurację w cache i czy cache jest aktualne
        if use_cache and self.config_cache and not self._is_config_file_modified():
            self.logger.debug(f"Using cached configuration from {file_path}")
            return (
                self.config_cache.copy()
            )  # Zwróć kopię, aby uniknąć przypadkowej modyfikacji

        try:
            # Sprawdź, czy plik istnieje
            if not os.path.exists(file_path):
                self.logger.warning(
                    f"Config file not found: {file_path}. Creating default config."
                )
                self._create_default_config(file_path)

            # Ładowanie i walidacja konfiguracji
            self.config_cache = ConfigValidator.validate_config_file(file_path)
            self.dirty = False
            self.logger.info(f"Configuration loaded from {file_path}")

            return self.config_cache

        except (ValidationError, ConfigurationError) as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {e}")
            raise ConfigurationError(
                f"Failed to load configuration: {str(e)}",
                error_code=ErrorCode.CONFIG,
                details={"file_path": file_path},
                original_exception=e,
            )

    def save_config(self, file_path: str = None) -> None:
        """
        Zapisuje konfigurację do pliku.

        Args:
            file_path: Ścieżka do pliku konfiguracyjnego. Jeśli None, używa ścieżki z load_config.

        Raises:
            ConfigurationError: Gdy wystąpi błąd podczas zapisywania konfiguracji.
        """
        if not self.dirty and not self.transaction_stack:
            self.logger.debug("No changes to configuration, skipping save.")
            return

        # Użyj zapisanej ścieżki, jeśli nie podano innej
        if file_path is None:
            if self.config_path is None:
                file_path = self._DEFAULT_CONFIG_PATH
                self.config_path = file_path
            else:
                file_path = self.config_path

        try:
            # Utwórz kopię zapasową przed zapisem
            self._create_backup(file_path)

            # Zapisz konfigurację do pliku
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.config_cache, f, indent=2, ensure_ascii=False)

            self.dirty = False
            self.logger.info(f"Configuration saved to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(
                f"Failed to save configuration: {str(e)}",
                error_code=ErrorCode.CONFIG,
                details={"file_path": file_path},
                original_exception=e,
            )

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Pobiera wartość konfiguracji.

        Args:
            key: Klucz konfiguracji. Może zawierać zagnieżdżone klucze rozdzielone kropką, np. "language.default"
            default: Wartość domyślna zwracana, gdy klucz nie istnieje.

        Returns:
            Wartość konfiguracji lub wartość domyślna.
        """
        if not self.config_cache:
            self.logger.warning(
                "Configuration not loaded, attempting to load default config."
            )
            try:
                self.load_config()
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                return default

        # Obsługa kluczy zagnieżdżonych (np. "language.default")
        if "." in key:
            keys = key.split(".")
            value = self.config_cache
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        else:
            return self.config_cache.get(key, default)

    def set_config_value(self, key: str, value: Any, save: bool = False) -> None:
        """
        Ustawia wartość konfiguracji.

        Args:
            key: Klucz konfiguracji. Może zawierać zagnieżdżone klucze rozdzielone kropką.
            value: Nowa wartość.
            save: Czy od razu zapisać konfigurację do pliku.
        """
        if not self.config_cache:
            self.logger.warning(
                "Configuration not loaded, attempting to load default config."
            )
            try:
                self.load_config()
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                self.config_cache = {}

        # Obsługa kluczy zagnieżdżonych (np. "language.default")
        if "." in key:
            keys = key.split(".")
            target = self.config_cache

            # Nawiguj do najgłębszego poziomu zagnieżdżenia
            for k in keys[:-1]:  # wszystkie oprócz ostatniego
                if k not in target:
                    target[k] = {}
                target = target[k]

            # Ustaw wartość na ostatnim poziomie
            target[keys[-1]] = value
        else:
            self.config_cache[key] = value

        self.dirty = True

        if save:
            self.save_config()

    def _is_config_file_modified(self) -> bool:
        """
        Sprawdza, czy plik konfiguracyjny został zmodyfikowany od czasu ostatniego ładowania.

        Returns:
            True, jeśli plik został zmodyfikowany, False w przeciwnym przypadku.
        """
        if not self.config_path or not os.path.exists(self.config_path):
            return True

        # Sprawdź, czy mamy zapisany timestamp ostatniej modyfikacji
        last_modified = os.path.getmtime(self.config_path)
        if not hasattr(self, "_last_modified_time"):
            self._last_modified_time = last_modified
            return True

        # Porównaj aktualny timestamp z zapisanym
        if last_modified > self._last_modified_time:
            self._last_modified_time = last_modified
            return True

        # Jeśli używamy cache, zwracamy False (plik nie został zmodyfikowany)
        # Test test_load_config_use_cache polega na tym założeniu
        return False

    def _create_default_config(self, file_path: str) -> None:
        """
        Tworzy domyślny plik konfiguracyjny.

        Args:
            file_path: Ścieżka do pliku konfiguracyjnego.
        """
        # Podstawowa konfiguracja domyślna
        default_config = {
            "language": "pl",
            "show_splash": True,
            "log_to_file": False,
            "log_to_system_console": False,
            "window_size": {"width": 1024, "height": 768},
            "window_position": {"x": 100, "y": 100},
            "remember_window_size": True,
            "log_level": "INFO",
        }

        # Zapisz domyślną konfigurację
        try:
            # Upewnij się, że katalog istnieje
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            self.config_cache = default_config
            self.logger.info(f"Created default configuration at {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
            raise ConfigurationError(
                f"Failed to create default configuration: {str(e)}",
                error_code=ErrorCode.CONFIG,
                details={"file_path": file_path},
                original_exception=e,
            )

    def _create_backup(self, file_path: str) -> None:
        """
        Tworzy kopię zapasową pliku konfiguracyjnego.

        Args:
            file_path: Ścieżka do pliku konfiguracyjnego.
        """
        if not os.path.exists(file_path):
            return

        backup_path = f"{file_path}{self._CONFIG_BACKUP_EXTENSION}"
        try:
            import shutil

            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"Created backup of configuration at {backup_path}")
        except Exception as e:
            self.logger.warning(f"Failed to create backup of configuration: {e}")
            # Kontynuuj bez tworzenia kopii zapasowej, to nie jest krytyczny błąd

    @contextmanager
    def transaction(self):
        """
        Kontekstowy menedżer dla transakcji konfiguracyjnych.
        Umożliwia grupowanie zmian konfiguracji i zatwierdzanie lub wycofywanie ich jako całość.

        Usage:
            with config_manager.transaction():
                config_manager.set_config_value("key1", "value1")
                config_manager.set_config_value("key2", "value2")
                # Zmiany zostaną zapisane dopiero po wyjściu z bloku with
                # Jeśli wystąpi wyjątek, zmiany zostaną wycofane
        """
        # Zapisz kopię konfiguracji przed rozpoczęciem transakcji
        config_snapshot = deepcopy(self.config_cache)
        self.transaction_stack.append(config_snapshot)

        try:
            yield
            # Gdy blok with kończy się bez wyjątku, usuń snapshot (zatwierdzenie transakcji)
            self.transaction_stack.pop()
            if (
                self.dirty and not self.transaction_stack
            ):  # jeśli to była ostatnia transakcja
                self.save_config()
        except Exception as e:
            # W przypadku wyjątku, przywróć konfigurację do stanu przed transakcją
            if self.transaction_stack:
                self.config_cache = self.transaction_stack.pop()
                self.dirty = False
            self.logger.warning(f"Transaction aborted due to error: {e}")
            raise

    def get_language_setting(self) -> str:
        """
        Pobiera ustawienie języka z konfiguracji.

        Returns:
            Kod języka (np. "pl", "en").
        """
        return self.get_config_value("language", "pl")

    def set_language_setting(self, language_code: str, save: bool = True):
        """
        Ustawia język w konfiguracji.

        Args:
            language_code: Kod języka (np. "pl", "en").
            save: Czy od razu zapisać konfigurację do pliku.
        """
        # Opcjonalnie: walidacja kodu języka
        valid_languages = ["pl", "en"]
        if language_code not in valid_languages:
            self.logger.warning(
                f"Invalid language code: {language_code}. Using default: pl"
            )
            language_code = "pl"

        self.set_config_value("language", language_code, save=save)

    def get_hardware_config(self, file_path: str = "hardware.json") -> Dict[str, Any]:
        """
        Ładuje i zwraca konfigurację sprzętową z oddzielnego pliku.

        Args:
            file_path: Ścieżka do pliku konfiguracji sprzętowej.

        Returns:
            Słownik z konfiguracją sprzętową.
        """
        try:
            # Przeprowadź walidację i ładowanie podobnie jak w przypadku głównej konfiguracji
            hardware_config = ConfigValidator.validate_config_file(file_path)
            return hardware_config
        except Exception as e:
            self.logger.error(f"Failed to load hardware configuration: {e}")
            raise ConfigurationError(
                f"Failed to load hardware configuration: {str(e)}",
                error_code=ErrorCode.CONFIG,
                details={"file_path": file_path},
                original_exception=e,
            )

    def reset_to_defaults(self, save: bool = True) -> None:
        """
        Resetuje konfigurację do wartości domyślnych.

        Args:
            save: Czy zapisać zmiany do pliku.
        """
        # Utwórz tymczasowo domyślną konfigurację
        temp_path = os.path.join(
            os.path.dirname(
                os.path.abspath(self.config_path or self._DEFAULT_CONFIG_PATH)
            ),
            ".temp_default_config.json",
        )
        self._create_default_config(temp_path)

        try:
            # Załaduj domyślną konfigurację
            with open(temp_path, "r", encoding="utf-8") as f:
                self.config_cache = json.load(f)

            self.dirty = True

            if save:
                self.save_config()

            self.logger.info("Configuration reset to defaults")
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            raise ConfigurationError(
                "Failed to reset configuration to defaults",
                error_code=ErrorCode.CONFIG,
                original_exception=e,
            )
        finally:
            # Usuń tymczasowy plik
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def validate_current_config(self) -> bool:
        """
        Waliduje aktualną konfigurację.

        Returns:
            True, jeśli konfiguracja jest poprawna, False w przeciwnym przypadku.
        """
        try:
            if not self.config_cache:
                self.load_config()

            self.validator.config = self.config_cache
            self.validator.validate()
            return True
        except ValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def merge_config(self, new_config: Dict[str, Any], save: bool = True) -> None:
        """
        Scala nową konfigurację z istniejącą.

        Args:
            new_config: Nowa konfiguracja do scalenia.
            save: Czy zapisać zmiany do pliku.

        Note:
            Ta metoda wykonuje rekurencyjne scalanie dla zagnieżdżonych słowników.
        """
        if not self.config_cache:
            self.load_config()

        def _deep_merge(target: Dict, source: Dict) -> Dict:
            """Rekurencyjnie scala dwa słowniki."""
            for key, value in source.items():
                if (
                    key in target
                    and isinstance(target[key], dict)
                    and isinstance(value, dict)
                ):
                    _deep_merge(target[key], value)
                else:
                    target[key] = value
            return target

        self.config_cache = _deep_merge(self.config_cache, new_config)
        self.dirty = True

        if save:
            self.save_config()


# Przykład użycia:
"""
# Inicjalizacja
config_manager = ConfigManager()
config_manager.load_config("config.json")

# Podstawowe operacje
lang = config_manager.get_language_setting()
print(f"Current language: {lang}")
config_manager.set_language_setting("pl", save=True)

# Używanie transakcji dla grupowania zmian
with config_manager.transaction():
    config_manager.set_config_value("window_size.width", 1024)
    config_manager.set_config_value("window_size.height", 768)
    # Zmiany zostaną zapisane automatycznie po wyjściu z bloku

# Resetowanie do domyślnych ustawień 
# config_manager.reset_to_defaults()

# Scalanie konfiguracji
new_settings = {
    "window_size": {"width": 1280},
    "debug_mode": True
}
config_manager.merge_config(new_settings)
"""

# Należy również zaktualizować wszystkie miejsca w kodzie,
# które obecnie korzystają ze starych mechanizmów konfiguracji.
