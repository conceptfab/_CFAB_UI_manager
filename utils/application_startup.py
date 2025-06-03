"""
Moduł do uproszczonej i scentralizowanej sekwencji startowej aplikacji.
"""

import json
import logging
import os
import platform
import time

from PyQt6.QtCore import QObject, pyqtSignal

from utils.exceptions import (
    ConfigurationError,
    FileOperationError,
    ValidationError,
    handle_error_gracefully,
)
from utils.improved_thread_manager import ThreadManager
from utils.logger import AppLogger
from utils.performance_optimizer import performance_monitor
from utils.resource_manager import ResourceManager
from utils.system_info import get_stable_uuid
from utils.validators import ConfigValidator

logger = logging.getLogger(__name__)


class ApplicationStartup(QObject):
    """
    Klasa odpowiedzialna za scentralizowane uruchomienie aplikacji.
    """

    startup_completed = pyqtSignal(object)
    startup_failed = pyqtSignal(Exception)
    config_loaded = pyqtSignal(dict)

    def __init__(self, base_dir):
        """
        Inicjalizacja sekwencji startowej aplikacji.

        Args:
            base_dir: Ścieżka bazowa do głównego katalogu aplikacji
        """
        super().__init__()
        self.base_dir = base_dir
        self.config = None
        self.thread_manager = ThreadManager()
        self.resource_manager = None
        self.logger = None
        self._hardware_verification_attempted = False

    @performance_monitor.measure_execution_time("app_startup")
    def initialize(self):
        """
        Uruchamia scentralizowaną sekwencję startową aplikacji.
        """
        try:
            # 1. Setup logging
            self.setup_logging()

            # 2. Load config
            self.load_config()

            # Initialize TranslationManager with the loaded config path
            config_path = os.path.join(self.base_dir, "config.json")
            from utils.translation_manager import TranslationManager

            TranslationManager.initialize(
                config_path=config_path, app_logger=self.logger
            )

            # 3. Initialize resource manager
            self.setup_resource_manager()

            # 4. Verify hardware
            self.thread_manager.run_in_thread(self.verify_hardware)

            # 5. Emituj sygnał ukończenia startupu z instancją loggera
            self.startup_completed.emit(self.logger)

            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Błąd podczas inicjalizacji aplikacji: {e}")
            else:
                print(
                    f"KRYTYCZNY BŁĄD (logger niedostępny): Błąd podczas inicjalizacji aplikacji: {e}"
                )
            self.startup_failed.emit(e)
            return False

    def setup_logging(self):
        """
        Konfiguracja loggera aplikacji.
        """
        log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Utwórz instancję AppLogger z konfiguracją
        # Zakładamy, że self.config jest już dostępne lub zostanie załadowane przed tą metodą
        if not self.config:
            # Próba załadowania konfiguracji, jeśli jeszcze nie istnieje
            # To jest uproszczenie, w rzeczywistości kolejność powinna być zagwarantowana
            # przez logikę initialize()
            try:
                self.load_config()
            except Exception as e:
                # Użyj domyślnej konfiguracji, jeśli ładowanie zawiedzie
                # lub rzuć błąd krytyczny, jeśli konfiguracja jest niezbędna do logowania
                # Używamy globalnego loggera tylko do tego komunikatu, bo self.logger jeszcze nie istnieje
                logger.error(f"Nie udało się załadować konfiguracji dla loggera: {e}")
                # Można tu ustawić domyślną konfigurację lub przerwać
                # Dla uproszczenia, kontynuujemy z potencjalnym brakiem konfiguracji
                # co może prowadzić do domyślnych ustawień w AppLogger

        # Sprawdź, czy self.config zostało poprawnie załadowane
        if self.config:
            # Konwersja poziomu logowania z stringa na stałą logging
            log_level_str = self.config.get("log_level", "INFO")
            log_level = getattr(logging, log_level_str.upper(), logging.INFO)

            # Inicjalizacja loggera z odpowiednimi parametrami z konfiguracji
            self.logger = AppLogger(
                log_dir=log_dir,
                app_name="CFAB",
                log_level=log_level,
                enable_console=self.config.get("log_to_system_console", True),
                enable_file_logging=self.config.get("log_to_file", False),
                max_queue_size=1000,
            )

            # Ustawienie trybu debug dla loggera jeśli skonfigurowany
            if self.config.get("logger_debug_mode", False):
                self.logger.async_logger.set_debug_mode(True)
        else:
            # Obsługa przypadku, gdy konfiguracja nie jest dostępna
            self.logger = AppLogger(
                log_dir=log_dir,
                app_name="CFAB",
                log_level=logging.INFO,
                enable_console=True,
                enable_file_logging=False,
            )
            # Używamy globalnego loggera tylko do tego komunikatu, bo self.logger jeszcze nie istnieje
            logger.warning(
                "Użyto domyślnej konfiguracji loggera, ponieważ główna konfiguracja nie była dostępna."
            )

        self.logger.info("Logger skonfigurowany")

    @handle_error_gracefully
    def load_config(self):
        """
        Wczytuje konfigurację z pliku config.json.
        """
        config_path = os.path.join(self.base_dir, "config.json")

        # self.logger może jeszcze nie być zainicjalizowany, jeśli load_config jest wywoływane z setup_logging
        # przed inicjalizacją self.logger. W takim przypadku użyj globalnego loggera.
        effective_logger = self.logger if self.logger else logger
        effective_logger.debug(f"Loading configuration from: {config_path}")

        if not os.path.exists(config_path):
            raise FileOperationError(
                f"Configuration file not found: {config_path}",
                file_path=config_path,
                operation="read",
            )

        try:
            # Użyj ConfigValidator do walidacji
            config = ConfigValidator.validate_config_file(config_path)

            # self.logger może jeszcze nie być zainicjalizowany
            effective_logger = self.logger if self.logger else logger
            effective_logger.info("Configuration loaded and validated successfully")
            self.config = config
            self.config_loaded.emit(config)

            return config
        except (ConfigurationError, ValidationError) as e:
            # Re-raise dla błędów konfiguracji
            raise e
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {e}", config_path=config_path
            )
        except Exception as e:
            raise FileOperationError(
                f"Failed to read configuration file: {e}",
                file_path=config_path,
                operation="read",
            )

    def setup_resource_manager(self):
        """
        Inicjalizuje i konfiguruje ResourceManager.
        """
        self.resource_manager = ResourceManager(
            self.base_dir, self.logger
        )  # Przekaż logger

        # Załaduj zasoby asynchronicznie
        self.resource_manager.load_all_resources()
        if self.logger:
            self.logger.info("ResourceManager skonfigurowany")
        return self.resource_manager

    @handle_error_gracefully
    def verify_hardware(self):
        """
        Weryfikuje profil sprzętowy. Wykonuje się tylko raz.
        """
        if self._hardware_verification_attempted:
            if self.logger:
                self.logger.info(
                    "Weryfikacja sprzętu została już wcześniej zainicjowana/wykonana. Pomijanie."
                )
            else:
                # Fallback, gdyby logger nie był jeszcze dostępny
                print(
                    "Weryfikacja sprzętu została już wcześniej zainicjowana/wykonana. Pomijanie."
                )
            return True  # Lub odpowiednia wartość wskazująca na pominięcie

        self._hardware_verification_attempted = True

        hardware_path = os.path.join(self.base_dir, "hardware.json")

        current_uuid = get_stable_uuid()
        self.logger.info(f"Aktualny UUID systemu: {current_uuid}")

        try:
            if os.path.exists(hardware_path):
                profile = ConfigValidator.validate_hardware_profile(hardware_path)
                stored_uuid = profile.get("uuid")
                self.logger.info(f"UUID zapisany w profilu: {stored_uuid}")

                system_changed = self._check_system_changes(profile)

                if stored_uuid != current_uuid:
                    if system_changed:
                        self.logger.warning(
                            "Wykryto niezgodność UUID sprzętowego i zmianę parametrów systemu. Tworzenie nowego profilu."
                        )
                        os.remove(hardware_path)
                        new_profile = self._create_new_hardware_profile()
                        with open(hardware_path, "w") as f:
                            json.dump(new_profile, f, indent=4)
                        self.logger.info(
                            f"Utworzono nowy profil sprzętowy: {current_uuid}"
                        )
                    else:
                        self.logger.warning(
                            "Niewielka niezgodność UUID bez zmiany parametrów systemu. Aktualizacja UUID w profilu."
                        )
                        profile["uuid"] = current_uuid
                        with open(hardware_path, "w") as f:
                            json.dump(profile, f, indent=4)
                        self.logger.info(
                            f"Zaktualizowano UUID w profilu sprzętowym: {current_uuid}"
                        )
            else:
                self.logger.warning(
                    "Nie znaleziono profilu sprzętowego. Tworzenie nowego profilu."
                )
                new_profile = self._create_new_hardware_profile()
                with open(hardware_path, "w") as f:
                    json.dump(new_profile, f, indent=4)
                self.logger.info(f"Utworzono nowy profil sprzętowy: {current_uuid}")

            self.logger.info("Weryfikacja profilu sprzętowego zakończona pomyślnie")
            return True
        except Exception as e:
            self.logger.error(f"Błąd weryfikacji profilu sprzętowego: {e}")
            return False

    def _log_uuid_debug(self, uuid_value):
        """
        Zapisuje informacje o UUID do logów i pliku debug, jeśli poziom logowania to DEBUG.

        Args:
            uuid_value: Wartość UUID do zalogowania
        """
        if self.logger and self.logger.handlers:
            # Sprawdź, czy poziom logowania jest ustawiony na DEBUG
            # To jest uproszczenie; idealnie AppLogger miałby metodę do sprawdzania poziomu
            is_debug_level = any(
                handler.level <= logging.DEBUG
                for handler in self.logger.handlers
                if hasattr(handler, "level")
            )
            # Lub, jeśli AppLogger ma bezpośredni dostęp do swojego poziomu:
            # is_debug_level = self.logger.level <= logging.DEBUG

            # Jeśli nie możemy łatwo sprawdzić poziomu, logujemy warunkowo lub zawsze,
            # zakładając, że konfiguracja loggera filtruje komunikaty.
            # Dla tego przykładu, załóżmy, że chcemy to logować tylko jeśli logger jest skonfigurowany na DEBUG.
            # Ponieważ bezpośrednie sprawdzenie poziomu loggera może być skomplikowane bez modyfikacji AppLogger,
            # możemy po prostu użyć self.logger.debug() i pozwolić konfiguracji loggera zdecydować.

            self.logger.debug(
                f"====== UUID DEBUG INFO (zapis do pliku uuid_debug.txt) ======"
            )
            self.logger.debug(f"System: {platform.system()}")
            self.logger.debug(f"Node: {platform.node()}")
            self.logger.debug(f"Machine: {platform.machine()}")
            self.logger.debug(f"UUID (cached): {uuid_value}")
            self.logger.debug(
                f"==========================================================="
            )

            # Zapisz na dysku do analizy - to działanie powinno być rzadsze, np. tylko przy konkretnych błędach
            # lub jeśli tryb debug jest bardzo szczegółowy.
            # Rozważ usunięcie tego lub uczynienie go bardziej warunkowym.
            try:
                with open(
                    os.path.join(self.base_dir, "uuid_debug.txt"),
                    "a",
                ) as f:
                    f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"UUID (cached): {uuid_value}\n")
                    f.write("-" * 50 + "\n")
            except Exception as e:
                self.logger.error(
                    f"Nie udało się zapisać debugowania UUID do pliku: {e}"
                )
        else:
            # Fallback, jeśli logger nie jest jeszcze w pełni skonfigurowany
            print(f"[DEBUG FALLBACK] UUID DEBUG: {uuid_value}")

    def _check_system_changes(self, profile):
        """
        Sprawdza, czy podstawowe informacje o systemie uległy zmianie.
        Loguje zmiany używając self.logger.

        Args:
            profile: Profil sprzętowy do sprawdzenia

        Returns:
            bool: True jeśli wykryto istotne zmiany, False w przeciwnym przypadku
        """
        system_changed = False
        current_system = platform.system()
        stored_system = profile.get("system_info", {}).get("system")
        if stored_system != current_system:
            system_changed = True
            self.logger.warning(
                f"Zmiana systemu operacyjnego: {stored_system} -> {current_system}"
            )

        current_machine = platform.machine()
        stored_machine = profile.get("system_info", {}).get("machine")
        if stored_machine != current_machine:
            system_changed = True
            self.logger.warning(
                f"Zmiana architektury: {stored_machine} -> {current_machine}"
            )
        return system_changed

    def _create_new_hardware_profile(self):
        """
        Tworzy nowy profil sprzętowy z aktualnym UUID.

        Returns:
            dict: Nowy profil sprzętowy
        """
        machine_uuid = (
            get_stable_uuid()
        )  # używamy stabilnej metody generowania UUID z cache
        profile = {
            "uuid": machine_uuid,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": {
                "system": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
        }
        return profile

    def cleanup(self):
        """
        Sprzątanie zasobów przed zamknięciem aplikacji.
        """
        if self.resource_manager:
            self.resource_manager.cleanup()

        if self.thread_manager:
            self.thread_manager.cleanup()

        logger.info("Przeprowadzono cleanup aplikacji")
