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

    startup_completed = pyqtSignal()
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

            # 3. Initialize resource manager
            self.setup_resource_manager()

            # 4. Verify hardware
            self.thread_manager.run_in_thread(self.verify_hardware)

            # 5. Emituj sygnał ukończenia startupu
            self.startup_completed.emit()
            logger.info("Aplikacja uruchomiona pomyślnie")

            return True
        except Exception as e:
            logger.error(f"Błąd podczas inicjalizacji aplikacji: {e}")
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
                logger.error(f"Nie udało się załadować konfiguracji dla loggera: {e}")
                # Można tu ustawić domyślną konfigurację lub przerwać
                # Dla uproszczenia, kontynuujemy z potencjalnym brakiem konfiguracji
                # co może prowadzić do domyślnych ustawień w AppLogger

        # Sprawdź, czy self.config zostało poprawnie załadowane
        if self.config:
            self.logger = AppLogger(self.config)  # Tworzenie instancji AppLogger
        else:
            # Obsługa przypadku, gdy konfiguracja nie jest dostępna
            # Można użyć domyślnej konfiguracji lub zalogować błąd
            default_config_for_logger = {
                "log_level": "INFO",
                "log_to_file": False,
                "log_ui_to_console": True,  # Domyślnie loguj do konsoli, jeśli brak configu
                "log_dir": log_dir,
            }
            self.logger = AppLogger(default_config_for_logger)
            logger.warning(
                "Użyto domyślnej konfiguracji loggera, ponieważ główna konfiguracja nie była dostępna."
            )

        logger.info("Logger skonfigurowany")

    @handle_error_gracefully
    def load_config(self):
        """
        Wczytuje konfigurację z pliku config.json.
        """
        config_path = os.path.join(self.base_dir, "config.json")

        logger.debug(f"Loading configuration from: {config_path}")

        if not os.path.exists(config_path):
            raise FileOperationError(
                f"Configuration file not found: {config_path}",
                file_path=config_path,
                operation="read",
            )

        try:
            # Użyj ConfigValidator do walidacji
            config = ConfigValidator.validate_config_file(config_path)

            logger.info("Configuration loaded and validated successfully")
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
        self.resource_manager = ResourceManager(self.base_dir)

        # Załaduj zasoby asynchronicznie
        self.resource_manager.load_all_resources()

        logger.info("ResourceManager skonfigurowany")
        return self.resource_manager

    @handle_error_gracefully
    def verify_hardware(self):
        """
        Weryfikuje profil sprzętowy.
        """
        hardware_path = os.path.join(self.base_dir, "hardware.json")

        # Generuj UUID tylko raz i zapisz do logów - używamy stabilnej metody z cache
        current_uuid = get_stable_uuid()
        self._log_uuid_debug(current_uuid)
        logger.info(f"Aktualnie wygenerowany UUID: {current_uuid}")

        try:
            if os.path.exists(hardware_path):
                # Wczytaj istniejący profil
                profile = ConfigValidator.validate_hardware_profile(hardware_path)
                stored_uuid = profile.get("uuid")
                logger.info(f"UUID zapisany w profilu: {stored_uuid}")

                # Sprawdź podstawowe informacje o systemie
                system_changed = self._check_system_changes(profile)

                if stored_uuid != current_uuid:
                    if system_changed:
                        # Rzeczywiście nastąpiła zmiana sprzętu
                        logger.warning(
                            "Wykryto niezgodność UUID sprzętowego i zmianę parametrów systemu. Tworzenie nowego profilu."
                        )
                        # Usuń stary profil
                        os.remove(hardware_path)
                        # Utwórz nowy profil
                        new_profile = self._create_new_hardware_profile()
                        with open(hardware_path, "w") as f:
                            json.dump(new_profile, f, indent=4)
                        logger.info(f"Utworzono nowy profil sprzętowy: {current_uuid}")
                    else:
                        # UUID się różni, ale parametry systemu nie - to prawdopodobnie ten sam komputer
                        # Aktualizujemy tylko UUID w istniejącym profilu
                        logger.warning(
                            "Niewielka niezgodność UUID bez zmiany parametrów systemu. Aktualizacja UUID w profilu."
                        )
                        profile["uuid"] = current_uuid
                        with open(hardware_path, "w") as f:
                            json.dump(profile, f, indent=4)
                        logger.info(
                            f"Zaktualizowano UUID w profilu sprzętowym: {current_uuid}"
                        )
            else:
                # Nie ma jeszcze profilu sprzętowego, utwórz nowy
                logger.warning(
                    "Nie znaleziono profilu sprzętowego. Tworzenie nowego profilu."
                )
                new_profile = self._create_new_hardware_profile()

                with open(hardware_path, "w") as f:
                    json.dump(new_profile, f, indent=4)

                logger.info(f"Utworzono nowy profil sprzętowy: {current_uuid}")

            logger.info("Weryfikacja profilu sprzętowego zakończona pomyślnie")
            return True
        except Exception as e:
            logger.error(f"Błąd weryfikacji profilu sprzętowego: {e}")
            return False

    def _log_uuid_debug(self, uuid_value):
        """
        Zapisuje informacje o UUID do logów i pliku debug.

        Args:
            uuid_value: Wartość UUID do zalogowania
        """
        # Zapisz do logów
        logger.warning(f"====== UUID DEBUG ======")
        logger.warning(f"System: {platform.system()}")
        logger.warning(f"Node: {platform.node()}")
        logger.warning(f"Machine: {platform.machine()}")
        logger.warning(f"UUID (cached): {uuid_value}")
        logger.warning(f"========================")

        # Zapisz na dysku do analizy
        try:
            with open(
                os.path.join(self.base_dir, "uuid_debug.txt"),
                "a",
            ) as f:
                f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"UUID (cached): {uuid_value}\n")
                f.write("-" * 50 + "\n")
        except Exception as e:
            logger.error(f"Nie udało się zapisać debugowania UUID: {e}")

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

    def _check_system_changes(self, profile):
        """
        Sprawdza czy nastąpiły istotne zmiany w systemie.

        Args:
            profile: Profil sprzętowy do sprawdzenia

        Returns:
            bool: True jeśli wykryto istotne zmiany, False w przeciwnym przypadku
        """
        system_changed = False
        if profile.get("system_info", {}).get("system") != platform.system():
            system_changed = True
            logger.warning(
                f"Zmiana systemu operacyjnego: {profile.get('system_info', {}).get('system')} -> {platform.system()}"
            )

        if profile.get("system_info", {}).get("machine") != platform.machine():
            system_changed = True
            logger.warning(
                f"Zmiana architektury: {profile.get('system_info', {}).get('machine')} -> {platform.machine()}"
            )

        return system_changed

    def cleanup(self):
        """
        Sprzątanie zasobów przed zamknięciem aplikacji.
        """
        if self.resource_manager:
            self.resource_manager.cleanup()

        if self.thread_manager:
            self.thread_manager.cleanup()

        logger.info("Przeprowadzono cleanup aplikacji")
