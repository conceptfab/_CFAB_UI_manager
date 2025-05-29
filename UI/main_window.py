import json
import logging
import os

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStatusBar, QTabWidget

from UI.components.console_widget import ConsoleWidget
from UI.components.menu_bar import create_menu_bar
from UI.components.tab_one_widget import TabOneWidget
from UI.components.tab_three_widget import TabThreeWidget
from UI.components.tab_two_widget import TabTwoWidget
from UI.hardware_profiler import HardwareProfilerDialog
from UI.preferences_dialog import PreferencesDialog
from utils.thread_manager import ThreadManager

# from UI.components.status_bar_manager import StatusBarManager # Jeśli używasz


class FileWorker(QObject):
    """
    Klasa obsługująca operacje na plikach w osobnym wątku.
    """

    finished = pyqtSignal(dict)
    error = pyqtSignal(Exception)

    def load_preferences(self, config_path):
        """
        Wczytuje preferencje z pliku konfiguracyjnego.

        Args:
            config_path (str): Ścieżka do pliku konfiguracyjnego
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                preferences = json.load(f)
            self.finished.emit(preferences)
        except Exception as e:
            self.error.emit(e)

    def save_preferences(self, config_path, preferences):
        """
        Zapisuje preferencje do pliku konfiguracyjnego.

        Args:
            config_path (str): Ścieżka do pliku konfiguracyjnego
            preferences (dict): Słownik z preferencjami do zapisania
        """
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
            self.finished.emit({"success": True})
        except Exception as e:
            self.error.emit(e)


class MainWindow(QMainWindow):
    """
    Główne okno aplikacji.
    """

    def __init__(self):
        """
        Inicjalizuje główne okno aplikacji.
        """
        super().__init__()
        self.setWindowTitle("Moja Zaawansowana Aplikacja PyQt6")
        self.thread_manager = ThreadManager()
        self.file_worker = FileWorker()

        # Domyślne preferencje
        self.preferences = {
            "show_splash": True,
            "log_to_file": False,
            "log_ui_to_console": False,
            "log_level": "INFO",
            "remember_window_size": True,
            "window_size": {"width": 800, "height": 600},
            "window_position": {"x": 100, "y": 100},
        }

        # Inicjalizacja preferencji
        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
        )
        self.load_preferences_async()

        # Konfiguracja okna
        self.setGeometry(100, 100, 800, 600)

        # Konfiguracja logowania
        self.configure_logging()

        # Inicjalizacja interfejsu
        self._init_ui()

    def _init_ui(self):
        """
        Inicjalizuje elementy interfejsu użytkownika.
        """
        # Menu
        create_menu_bar(self)

        # Zakładki
        self.tabs = QTabWidget()
        self.tab1 = TabOneWidget()
        self.tab2 = TabTwoWidget()
        self.tab3 = TabThreeWidget()
        self.console_tab = ConsoleWidget()

        self.tabs.addTab(self.tab1, "Zakładka 1")
        self.tabs.addTab(self.tab2, "Zakładka 2")
        self.tabs.addTab(self.tab3, "Zakładka 3")
        self.tabs.addTab(self.console_tab, "Konsola")

        self.setCentralWidget(self.tabs)

        # Pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Gotowy.")
        # Jeśli używasz StatusBarManager:
        # self.status_manager = StatusBarManager(self.status_bar)
        # self.status_manager.set_message("Gotowy przez managera.")

        # Testowe logi
        self._log_test_messages()

    def _log_test_messages(self):
        """
        Loguje testowe wiadomości dla różnych poziomów logowania.
        """
        logger = logging.getLogger("AppLogger")
        logger.info("Aplikacja uruchomiona")
        logger.debug("Debug: Inicjalizacja zakończona pomyślnie")
        logger.warning("Uwaga: Używana wersja testowa")
        logger.error("Błąd: Test obsługi błędów")

        if self.preferences.get("log_ui_to_console", False):
            logger.info("UI: Logowanie akcji interfejsu włączone")

    def configure_logging(self):
        """
        Konfiguruje system logowania na podstawie preferencji.
        """
        logger = logging.getLogger("AppLogger")
        log_level = self.preferences.get("log_level", "INFO")
        logger.setLevel(getattr(logging, log_level))

        if self.preferences.get("log_to_file", False):
            log_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "app.log"
            )
            file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    def load_preferences_async(self):
        """
        Wczytuje preferencje asynchronicznie.
        """
        worker = self.thread_manager.run_in_thread(
            self.file_worker.load_preferences, self.config_path
        )
        worker.finished.connect(self.on_preferences_loaded)
        worker.error.connect(self.on_preferences_error)

    def on_preferences_loaded(self, preferences):
        """
        Obsługuje załadowane preferencje.

        Args:
            preferences (dict): Słownik z preferencjami
        """
        if preferences:
            self.preferences.update(preferences)
            if self.preferences.get("remember_window_size", True):
                window_size = self.preferences.get(
                    "window_size", {"width": 800, "height": 600}
                )
                window_pos = self.preferences.get(
                    "window_position", {"x": 100, "y": 100}
                )
                self.setGeometry(
                    window_pos["x"],
                    window_pos["y"],
                    window_size["width"],
                    window_size["height"],
                )

    def on_preferences_error(self, error):
        """
        Obsługuje błąd wczytywania preferencji.

        Args:
            error (Exception): Wystąpiony błąd
        """
        print(f"Błąd wczytywania preferencji: {error}")
        # Używamy domyślnych preferencji zdefiniowanych w __init__

    def save_preferences_async(self):
        """
        Zapisuje preferencje asynchronicznie.
        """
        worker = self.thread_manager.run_in_thread(
            self.file_worker.save_preferences, self.config_path, self.preferences
        )
        worker.finished.connect(
            lambda _: self.status_bar.showMessage("Zapisano preferencje.")
        )
        worker.error.connect(lambda e: self.status_bar.showMessage(f"Błąd zapisu: {e}"))

    def show_preferences_dialog(self):
        """
        Wyświetla okno dialogowe preferencji.
        """
        dialog = PreferencesDialog(self.preferences, self)
        if dialog.exec():
            self.preferences.update(dialog.get_preferences())
            self.save_preferences_async()

    def show_hardware_profiler(self):
        """
        Wyświetla okno dialogowe profilera sprzętowego.
        """
        dialog = HardwareProfilerDialog(self)
        dialog.exec()

    def update_status(self, message):
        """
        Aktualizuje komunikat na pasku statusu.

        Args:
            message (str): Nowy komunikat
        """
        self.status_bar.showMessage(message)

    def closeEvent(self, event):
        """
        Obsługuje zdarzenie zamknięcia okna.

        Args:
            event: Zdarzenie zamknięcia
        """
        if self.preferences.get("remember_window_size", True):
            self.preferences["window_size"] = {
                "width": self.size().width(),
                "height": self.size().height(),
            }
            self.preferences["window_position"] = {
                "x": self.pos().x(),
                "y": self.pos().y(),
            }
            self.save_preferences_async()

        reply = QMessageBox.question(
            self,
            "Zamykanie Aplikacji",
            "Czy na pewno chcesz zamknąć aplikację?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            print("Zamykanie aplikacji...")
            self.thread_manager.cleanup()
            event.accept()
        else:
            event.ignore()


# Dodaj import QMessageBox jeśli go używasz w closeEvent
from PyQt6.QtWidgets import QMessageBox
