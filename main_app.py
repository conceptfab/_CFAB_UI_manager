import datetime
import json
import logging
import os
import platform
import sys
import uuid

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from UI.main_window import MainWindow
from UI.splash_screen import SplashScreen
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
    startup_optimizer,
)
from utils.system_info import get_stable_uuid
from utils.translation_manager import TranslationManager
from utils.translator import Translator
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
    Rozszerzona klasa aplikacji z obsługą konfiguracji.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = {
            "show_splash": True,
            "log_to_file": False,
            "log_ui_to_console": False,
            "log_level": "INFO",
        }

        # Inicjalizacja TranslationManager z ścieżką do config.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")
        TranslationManager.initialize(config_path)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value


if __name__ == "__main__":
    # Inicjalizacja aplikacji
    app = Application(sys.argv)
    thread_manager = ThreadManager()

    # Sekwencja startowa
    logger.info("=== Sekwencja startowa ===")

    # 1. Wczytanie konfiguracji w osobnym wątku
    logger.info("1. Wczytywanie konfiguracji...")
    config_loader = ConfigLoader()

    # Klasa do przechowywania stanu konfiguracji
    class ConfigState:
        def __init__(self):
            self.loaded = False
            self.config = None

    state = ConfigState()

    def on_config_loaded(loaded_config):
        state.config = loaded_config
        state.loaded = True

    config_loader.config_loaded.connect(on_config_loaded)
    thread_manager.run_in_thread(config_loader.load_config)

    # Czekamy na załadowanie konfiguracji
    while not state.loaded:
        app.processEvents()

    # Ustawiamy konfigurację
    app._config = state.config

    # 2. Inicjalizacja loggera
    logger.info("2. Inicjalizacja systemu logowania...")
    app_logger = AppLogger(app.config)
    logger.info("Aplikacja uruchomiona")

    # 3. Initialize performance optimization
    logger.info("3. Initializing performance optimization...")
    async_loader = AsyncResourceLoader()

    # Take initial memory snapshot
    initial_memory = performance_monitor.take_memory_snapshot("application_start")
    logger.info(f"Initial memory usage: {initial_memory.get('rss_mb', 0):.1f}MB")

    # Register lazy loaders for heavy resources
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "resources", "styles.qss")
    lazy_loader.register_loader("main_css", create_css_loader(css_path))

    # 4. Weryfikacja profilu sprzętowego w osobnym wątku (deferred)
    @defer_until_after_startup(delay_ms=500)
    def deferred_hardware_verification():
        logger.info("4. Weryfikacja profilu sprzętowego (deferred)...")
        thread_manager.run_in_thread(verify_hardware_profile)

    deferred_hardware_verification()

    # Konfiguracja interfejsu (reuse base_dir from above)
    icon_path = os.path.join(base_dir, "resources", "img", "icon.png")
    app.setWindowIcon(QIcon(icon_path))

    # Optimized async style loading
    @performance_monitor.measure_execution_time("css_loading")
    def load_styles_optimized():
        """
        Optimized CSS loading with lazy loading and caching.
        """
        try:
            # Try to get from lazy loader cache first
            styles = lazy_loader.get_resource("main_css")
            logger.info("CSS styles loaded from cache")
            return styles
        except Exception as e:
            logger.warning(f"Could not load CSS from cache: {e}")
            return ""

    # Load styles asynchronously
    async_loader.resource_loaded.connect(
        lambda name, styles: (
            app.setStyleSheet(styles),
            logger.info(f"Applied {len(styles)} characters of CSS styles"),
        )
    )

    async_loader.loading_failed.connect(
        lambda name, error: logger.warning(f"Failed to load CSS: {error}")
    )

    # Start async CSS loading
    async_loader.load_resource_async("main_css", load_styles_optimized)

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

        # CSS and hardware tasks will be completed by their respective async operations

        # Show main window when splash completes
        splash.startup_completed.connect(main_win.show)

        # Complete remaining tasks after a short delay
        QTimer.singleShot(
            2000,
            lambda: [
                progress_tracker.start_task("Loading CSS styles"),
                progress_tracker.complete_task("Loading CSS styles"),
                progress_tracker.start_task("Initializing hardware detection"),
                progress_tracker.complete_task("Initializing hardware detection"),
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

    # Czyszczenie wątków przy zamknięciu
    app.aboutToQuit.connect(thread_manager.cleanup)

    sys.exit(app.exec())
