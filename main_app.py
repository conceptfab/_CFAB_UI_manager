import datetime
import json
import logging
import os
import platform
import sys
import time

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from UI.main_window import MainWindow
from UI.splash_screen import SplashScreen
from utils.application_startup import ApplicationStartup
from utils.enhanced_splash import StartupProgressTracker, create_optimized_splash
from utils.exceptions import (
    ConfigurationError,
    FileOperationError,
    ValidationError,
    handle_error_gracefully,
)
from utils.improved_thread_manager import ThreadManager
from utils.logger import AppLogger
from utils.performance_optimizer import (
    AsyncResourceLoader,
    create_css_loader,
    defer_until_after_startup,
    lazy_loader,
    performance_monitor,
)
from utils.resource_manager import ResourceManager
from utils.system_info import get_stable_uuid
from utils.translation_manager import TranslationManager
from utils.validators import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigLoader(QObject):
    """
    Klasa odpowiedzialna za asynchroniczne wczytywanie konfiguracji.
    """

    config_loaded = pyqtSignal(dict)
    error = pyqtSignal(Exception)

    @handle_error_gracefully
    def load_config(self):
        """
        Wczytuje konfigurację z pliku config.json.
        Emituje sygnał config_loaded z konfiguracją lub error w przypadku błędu.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")

        logger.debug(f"Loading configuration from: {config_path}")

        if not os.path.exists(config_path):
            raise FileOperationError(
                f"Configuration file not found: {config_path}",
                file_path=config_path,
                operation="read",
            )

        try:
            # Use ConfigValidator for comprehensive validation
            config = ConfigValidator.validate_config_file(config_path)

            logger.info("Configuration loaded and validated successfully")
            self.config_loaded.emit(config)
        except (ConfigurationError, ValidationError) as e:
            # Re-raise configuration-specific errors
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


def log_uuid_debug(uuid_value):
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "uuid_debug.txt"),
            "a",
        ) as f:
            f.write(f"Time: {datetime.datetime.now()}\n")
            f.write(f"UUID (cached): {uuid_value}\n")
            f.write("-" * 50 + "\n")
    except Exception as e:
        logger.error(f"Nie udało się zapisać debugowania UUID: {e}")


def create_new_hardware_profile():
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
        "created_at": str(datetime.datetime.now()),
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


def verify_hardware_profile():
    """
    Weryfikuje czy istnieje profil sprzętowy i czy jest zgodny z aktualnym sprzętem.
    Jeśli profil nie istnieje lub UUID się nie zgadza, tworzy nowy profil.

    Returns:
        bool: True jeśli profil istnieje i został poprawnie wczytany lub utworzony,
              False w przypadku błędu
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hardware_path = os.path.join(base_dir, "hardware.json")

    # Generuj UUID tylko raz i zapisz do logów - używamy stabilnej metody z cache
    current_uuid = get_stable_uuid()
    log_uuid_debug(current_uuid)
    logger.info(f"Aktualnie wygenerowany UUID: {current_uuid}")

    try:
        if os.path.exists(hardware_path):
            # Wczytaj istniejący profil
            profile = ConfigValidator.validate_hardware_profile(hardware_path)
            stored_uuid = profile.get("uuid")
            logger.info(f"UUID zapisany w profilu: {stored_uuid}")

            # Sprawdź podstawowe informacje o systemie, aby upewnić się, że rzeczywiście nastąpiła zmiana sprzętu
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

            # Jeśli UUID jest różny, ale tylko nieznacznie, to prawdopodobnie to nadal ten sam komputer
            if stored_uuid != current_uuid:
                if system_changed:
                    # Rzeczywiście nastąpiła zmiana sprzętu
                    logger.warning(
                        "Wykryto niezgodność UUID sprzętowego i zmianę parametrów systemu. Tworzenie nowego profilu."
                    )
                    # Usuń stary profil
                    os.remove(hardware_path)
                    # Utwórz nowy profil
                    new_profile = create_new_hardware_profile()
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
                        f"Zaktualizowano UUID profilu sprzętowego: {current_uuid}"
                    )
                return True
            else:
                logger.info(f"Profil sprzętowy poprawny: {stored_uuid}")
                return True
        else:
            # Utwórz nowy profil
            new_profile = create_new_hardware_profile()
            with open(hardware_path, "w") as f:
                json.dump(new_profile, f, indent=4)
            logger.info(f"Utworzono nowy profil sprzętowy: {current_uuid}")
            return True

    except ValidationError as e:
        logger.error(f"Błąd walidacji profilu sprzętowego: {e}")
        return False
    except Exception as e:
        logger.error(f"Błąd obsługi profilu sprzętowego: {e}")
        return False


class Application(QApplication):
    """
    Rozszerzona klasa aplikacji z obsługą konfiguracji i zasobów.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = {
            "show_splash": True,
            "log_to_file": False,
            "log_ui_to_console": False,
            "log_level": "INFO",
        }
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.startup = None
        self.resource_manager = None

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    def initialize(self):
        """
        Scentralizowana inicjalizacja aplikacji.
        """
        self.startup = ApplicationStartup(self.base_dir)

        # Podłącz sygnały
        self.startup.config_loaded.connect(self.on_config_loaded)
        self.startup.startup_failed.connect(self.on_startup_failed)

        # Uruchom inicjalizację
        success = self.startup.initialize()

        if success:
            # Pobierz resource manager z inicjalizacji
            self.resource_manager = self.startup.resource_manager

            # Podłącz sygnały resource managera
            if self.resource_manager:
                self.resource_manager.css_loaded.connect(self.on_css_loaded)

        return success

    def on_config_loaded(self, config):
        """Handler dla załadowanej konfiguracji"""
        self._config = config
        logger.info("Zaktualizowano konfigurację aplikacji")

    def on_css_loaded(self, css):
        """Handler dla załadowanych stylów CSS"""
        self.setStyleSheet(css)
        logger.info(f"Zastosowano {len(css)} znaków styli CSS")

    def on_startup_failed(self, error):
        """Handler dla błędów podczas uruchamiania"""
        logger.error(f"Błąd inicjalizacji aplikacji: {error}")

    def cleanup(self):
        """Sprzątanie zasobów przed zamknięciem aplikacji"""
        if self.startup:
            self.startup.cleanup()


if __name__ == "__main__":
    # Inicjalizacja aplikacji
    logger.info("=== Sekwencja startowa ===")

    # Utwórz aplikację
    app = Application(sys.argv)

    # Take initial memory snapshot
    initial_memory = performance_monitor.take_memory_snapshot("application_start")
    logger.info(f"Initial memory usage: {initial_memory.get('rss_mb', 0):.1f}MB")

    # Uruchom scentralizowaną inicjalizację
    if not app.initialize():
        logger.error("Nie udało się zainicjalizować aplikacji")
        sys.exit(1)

    # Konfiguracja interfejsu
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "resources", "img", "icon.png")
    app.setWindowIcon(QIcon(icon_path))

    # Inicjalizacja głównego okna
    logger.info("Inicjalizacja głównego okna")

    # Take memory snapshot before main window creation
    performance_monitor.take_memory_snapshot("before_main_window")

    main_win = MainWindow()
    main_win.setWindowIcon(QIcon(icon_path))
    main_win.logger = logger
    main_win.preferences = app.config  # Przekazujemy już załadowaną konfigurację

    # Take memory snapshot after main window creation
    performance_monitor.take_memory_snapshot("after_main_window")

    # Enhanced splash screen with progress tracking
    splash = None
    progress_tracker = None
    if app.config.get("show_splash", True):
        logger.info("Wyświetlanie enhanced splash screen")
        splash_path = os.path.join(base_dir, "resources", "img", "splash.jpg")

        # Define startup tasks for progress tracking
        startup_tasks = [
            "Loading configuration",
            "Initializing UI components",
            "Loading translations",
            "Loading CSS styles",
            "Initializing hardware detection",
            "Finalizing startup",
        ]

        splash, progress_tracker = create_optimized_splash(
            image_path=splash_path, startup_tasks=startup_tasks, window_size=(642, 250)
        )

        # Simulate progress for completed tasks
        progress_tracker.start_task("Loading configuration")
        progress_tracker.complete_task("Loading configuration")

        progress_tracker.start_task("Initializing UI components")
        progress_tracker.complete_task("Initializing UI components")

        progress_tracker.start_task("Loading translations")
        progress_tracker.complete_task("Loading translations")

        progress_tracker.start_task("Loading CSS styles")
        progress_tracker.complete_task("Loading CSS styles")

        progress_tracker.start_task("Initializing hardware detection")
        progress_tracker.complete_task("Initializing hardware detection")

        # Show main window when splash completes
        splash.startup_completed.connect(main_win.show)

        # Complete remaining tasks after a short delay
        QTimer.singleShot(
            1000,
            lambda: [
                progress_tracker.start_task("Finalizing startup"),
                progress_tracker.complete_task("Finalizing startup"),
            ],
        )
    else:
        main_win.show()

    logger.info("Główne okno wyświetlone")

    # Final performance and memory summary
    final_memory = performance_monitor.take_memory_snapshot("application_ready")
    memory_trend = performance_monitor.get_memory_usage_trend()
    performance_stats = performance_monitor.get_performance_stats()

    logger.info("=== Performance Summary ===")
    logger.info(f"Final memory usage: {final_memory.get('rss_mb', 0):.1f}MB")
    logger.info(f"Memory trend: {memory_trend.get('trend', 'unknown')}")

    if performance_stats:
        logger.info("Execution time stats:")
        for operation, stats in performance_stats.items():
            logger.info(
                f"  {operation}: {stats['avg_time']:.3f}s avg ({stats['count']} calls)"
            )

    logger.info("=== Aplikacja gotowa ===")

    # Schedule periodic memory monitoring
    memory_timer = QTimer()
    memory_timer.timeout.connect(
        lambda: performance_monitor.take_memory_snapshot("periodic_check")
    )
    memory_timer.start(30000)  # Every 30 seconds

    # Czyszczenie zasobów przy zamknięciu
    app.aboutToQuit.connect(app.cleanup)

    sys.exit(app.exec())
