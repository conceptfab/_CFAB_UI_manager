import warnings

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="cupy._environment",
)

import os
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from UI.main_window import MainWindow
from utils.application_startup import ApplicationStartup
from utils.enhanced_splash import create_optimized_splash
from utils.performance_optimizer import performance_monitor


class Application(QApplication):
    """
    Rozszerzona klasa aplikacji z obsługą konfiguracji i zasobów.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = {
            "show_splash": True,
            "log_to_file": False,
            "log_to_system_console": False,  # Zmieniona nazwa z log_ui_to_console
            "log_level": "INFO",
        }
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.startup = None
        self.resource_manager = None
        self.app_logger = None  # Dodano do przechowywania instancji AppLogger
        self.main_window = None  # Dodano do przechowywania instancji MainWindow

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
        self.startup.startup_completed.connect(
            self.on_startup_completed
        )  # Podłącz nowy sygnał

        # Uruchom inicjalizację
        success = self.startup.initialize()

        if success:
            # Pobierz resource manager z inicjalizacji
            self.resource_manager = self.startup.resource_manager

            # Podłącz sygnały resource managera
            if self.resource_manager:
                self.resource_manager.css_loaded.connect(self.on_css_loaded)

        return success

    def on_startup_completed(self, app_logger_instance):  # Odbierz instancję AppLogger
        """Handler dla pomyślnego ukończenia startupu."""
        self.app_logger = app_logger_instance
        if self.app_logger:
            self.app_logger.info(
                "Application startup completed successfully. AppLogger instance received."
            )

    def on_config_loaded(self, config):
        """Handler dla załadowanej konfiguracji"""
        self._config = config

    def on_css_loaded(self, css):
        """Handler dla załadowanych stylów CSS"""
        self.setStyleSheet(css)

    def on_startup_failed(self, error):
        """Handler dla błędów podczas uruchamiania"""
        # Można tu dodać np. wyświetlenie krytycznego błędu użytkownikowi
        if self.app_logger:
            self.app_logger.critical(f"CRITICAL STARTUP ERROR: {error}")
        else:
            sys.stderr.write(
                f"CRITICAL STARTUP ERROR: {error}\n"
            )  # Fallback if logger not ready

    def cleanup(self):
        """Sprzątanie zasobów przed zamknięciem aplikacji"""
        if self.startup:
            self.startup.cleanup()

    def setup_ui(self):
        """Konfiguruje i wyświetla główne okno aplikacji."""
        icon_path = os.path.join(self.base_dir, "resources", "img", "icon.png")
        self.setWindowIcon(QIcon(icon_path))

        performance_monitor.take_memory_snapshot("before_main_window")
        self.main_window = MainWindow(
            app_logger=self.app_logger if hasattr(self, "app_logger") else None
        )
        self.main_window.setWindowIcon(QIcon(icon_path))

        # Przekazywanie tylko niezbędnych części konfiguracji lub przez dedykowany serwis
        # Na razie zostawiamy przekazanie całego config dla zachowania funkcjonalności
        # W przyszłości można to zrefaktoryzować, np. main_window.load_preferences(self.config.get("window_settings"))
        self.main_window.preferences = self.config

        performance_monitor.take_memory_snapshot("after_main_window")

        if not self.config.get("show_splash", True):
            self.main_window.show()

        return self.main_window

    def show_splash_screen_if_enabled(self, main_window_instance):
        """Pokazuje splash screen, jeśli jest włączony w konfiguracji."""
        if self.config.get("show_splash", True):
            splash_path = os.path.join(self.base_dir, "resources", "img", "splash.jpg")
            startup_tasks = [
                "Loading configuration",
                "Initializing UI components",
                "Loading translations",
                "Loading CSS styles",
                "Initializing hardware detection",
                "Finalizing startup",
            ]
            splash, progress_tracker = create_optimized_splash(
                image_path=splash_path,
                startup_tasks=startup_tasks,
                window_size=(642, 250),
            )

            # Symulacja postępu dla zadań, które mogły już zostać wykonane
            # lub są szybko wykonywane przez ApplicationStartup
            tasks_to_simulate = [
                "Loading configuration",
                "Initializing UI components",  # Częściowo, reszta w MainWindow
                "Loading translations",  # Zakładając, że TranslationManager jest szybki
                "Loading CSS styles",  # Obsługiwane przez ResourceManager
            ]
            for task_name in tasks_to_simulate:
                if task_name in startup_tasks:
                    progress_tracker.start_task(task_name)
                    progress_tracker.complete_task(task_name)

            # Pozostałe zadania będą aktualizowane w miarę postępu
            # np. "Initializing hardware detection" może być dłuższe

            main_window_instance.splash_progress_tracker = (
                progress_tracker  # Przekazanie trackera do MainWindow
            )

            splash.startup_completed.connect(main_window_instance.show)

            # Symulacja dla "Finalizing startup" - można to zintegrować z faktycznym końcem inicjalizacji MainWindow
            QTimer.singleShot(
                1000,  # Krótkie opóźnienie dla demonstracji
                lambda: (
                    progress_tracker.start_task(
                        "Initializing hardware detection"
                    ),  # Przykładowe miejsce
                    progress_tracker.complete_task("Initializing hardware detection"),
                    progress_tracker.start_task("Finalizing startup"),
                    progress_tracker.complete_task("Finalizing startup"),
                ),
            )
            return splash
        return None


if __name__ == "__main__":
    app = Application(sys.argv)

    initial_memory = performance_monitor.take_memory_snapshot("application_start")

    if not app.initialize():
        sys.exit(1)

    main_win = app.setup_ui()
    splash = app.show_splash_screen_if_enabled(main_win)

    final_memory = performance_monitor.take_memory_snapshot("application_ready")
    memory_trend = performance_monitor.get_memory_usage_trend()
    performance_stats = performance_monitor.get_performance_stats()

    memory_timer = QTimer()
    memory_timer.timeout.connect(
        lambda: performance_monitor.take_memory_snapshot("periodic_check")
    )
    memory_timer.start(30000)

    app.aboutToQuit.connect(app.cleanup)

    sys.exit(app.exec())
