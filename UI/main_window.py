import json
import logging
import os

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from UI.components.console_widget import ConsoleWidget
from UI.components.menu_bar import create_menu_bar
from UI.components.tab_one_widget import TabOneWidget
from UI.components.tab_three_widget import TabThreeWidget
from UI.components.tab_two_widget import TabTwoWidget
from UI.hardware_profiler import HardwareProfilerDialog
from UI.preferences_dialog import PreferencesDialog
from utils.improved_thread_manager import (
    ThreadManager,
)  # Zmieniono ImprovedThreadManager na ThreadManager
from utils.performance_optimizer import (
    defer_until_after_startup,
    lazy_property,
    performance_monitor,
)
from utils.translation_manager import TranslationManager

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

    def __init__(self, *args, app_logger=None, **kwargs):  # Dodano app_logger
        try:
            # Użyj przekazanego loggera lub globalnego, jeśli nie przekazano
            self.logger = (
                app_logger if app_logger else logging.getLogger("AppLogger")
            )  # Użyj przekazanego loggera

            self.logger.info("MainWindow: start __init__")
            super().__init__(*args, **kwargs)
            self.setWindowTitle(TranslationManager.translate("app.title"))
            self.thread_manager = ThreadManager()
            self.file_worker = FileWorker()
            self.app_logger = app_logger  # Zapisz instancję loggera

            # Domyślne preferencje
            self._preferences = {
                "show_splash": True,
                "log_to_file": False,
                "log_ui_to_console": False,
                "log_level": "INFO",
                "remember_window_size": True,
                "window_size": {"width": 800, "height": 600},
                "window_position": {"x": 100, "y": 100},
            }

            # Ścieżka do pliku konfiguracyjnego
            self.config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
            )

            # Konfiguracja logowania - teraz zarządzana centralnie przez AppLogger
            # self.configure_logging() # Usunięto, AppLogger jest konfigurowany w ApplicationStartup

            # Inicjalizacja interfejsu
            self._init_ui()

            # Rejestracja głównego okna w TranslationManager
            TranslationManager.register_widget(
                self
            )  # TranslationManager powinien używać własnego loggera lub przekazanego
            self.logger.info("MainWindow: koniec __init__")
        except Exception as e:
            # Użyj self.logger jeśli istnieje, w przeciwnym razie globalny logger
            effective_logger = (
                self.logger
                if hasattr(self, "logger") and self.logger
                else logging.getLogger(__name__)
            )
            effective_logger.error(
                f"MainWindow: wyjątek w __init__: {e}", exc_info=True
            )
            QMessageBox.critical(None, "Błąd MainWindow", f"Wyjątek w MainWindow:\n{e}")
            raise

    @performance_monitor.measure_execution_time("main_window_init")
    def _init_ui(self):
        """
        Inicjalizuje elementy interfejsu użytkownika z optymalizacjami wydajności.
        """
        # Ustawienie rozmiaru okna na podstawie preferencji
        if self._preferences.get("remember_window_size", True):
            window_size = self._preferences.get(
                "window_size", {"width": 800, "height": 600}
            )
            window_pos = self._preferences.get("window_position", {"x": 100, "y": 100})
            self.setGeometry(
                window_pos["x"],
                window_pos["y"],
                window_size["width"],
                window_size["height"],
            )

        # Menu
        create_menu_bar(self)

        # Zakładki
        self.tabs = QTabWidget()
        self._tab_widgets = {}  # Cache dla widgetów zakładek

        # Inicjalizacja wszystkich zakładek
        self._init_tab1()
        self._init_tab2()
        self._init_tab3()
        self._init_console()

        # Dodanie zakładek do widgeta
        self.tabs.addTab(
            self._tab_widgets["tab1"], TranslationManager.translate("app.tabs.tab1")
        )
        self.tabs.addTab(
            self._tab_widgets["tab2"], TranslationManager.translate("app.tabs.tab2")
        )
        self.tabs.addTab(
            self._tab_widgets["tab3"], TranslationManager.translate("app.tabs.tab3")
        )
        self.tabs.addTab(
            self._tab_widgets["console"],
            TranslationManager.translate("app.tabs.console.title"),
        )

        self.setCentralWidget(self.tabs)

        # Pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(TranslationManager.translate("app.status.ready"))
        # Jeśli używasz StatusBarManager:
        # self.status_manager = StatusBarManager(self.status_bar)
        # self.status_manager.set_message("Gotowy przez managera.")

    def _init_tab1(self):
        """Inicjalizacja pierwszej zakładki."""
        logging.debug("Inicjalizacja TabOneWidget...")
        widget = TabOneWidget()
        TranslationManager.register_widget(widget)
        self._tab_widgets["tab1"] = widget

    def _init_tab2(self):
        """Inicjalizacja drugiej zakładki."""
        logging.debug("Inicjalizacja TabTwoWidget...")
        widget = TabTwoWidget()
        TranslationManager.register_widget(widget)
        self._tab_widgets["tab2"] = widget

    def _init_tab3(self):
        """Inicjalizacja trzeciej zakładki."""
        logging.debug("Inicjalizacja TabThreeWidget...")
        widget = TabThreeWidget()
        TranslationManager.register_widget(widget)
        self._tab_widgets["tab3"] = widget

    def _init_console(self):
        """Inicjalizacja zakładki konsoli."""
        self.logger.debug("Inicjalizacja ConsoleWidget...")
        # ConsoleWidget nie potrzebuje już app_logger w konstruktorze
        widget = ConsoleWidget(parent=self)
        TranslationManager.register_widget(widget)
        self._tab_widgets["console"] = widget

        # Zarejestruj metodę append_log konsoli w AppLogger
        if self.app_logger and hasattr(widget, "append_log"):
            # Dodajemy bardziej szczegółowe logowanie dla debugowania
            self.logger.debug(
                f"Próba rejestracji handlera konsoli. app_logger: {self.app_logger}"
            )
            try:
                self.app_logger.set_console_widget_handler(widget.append_log)
                self.logger.info("ConsoleWidget handler registered with AppLogger.")
                # Test logu przez AppLogger
                self.app_logger.async_logger.log(
                    logging.INFO,
                    "Test logu przez AsyncLogger po rejestracji ConsoleWidget",
                )
            except Exception as e:
                self.logger.error(
                    f"Błąd podczas rejestracji handlera konsoli: {e}", exc_info=True
                )
        elif not self.app_logger:
            self.logger.warning(
                "AppLogger not available, ConsoleWidget UI logging might not work."
            )

    def _log_test_messages(self):
        """
        Loguje testowe wiadomości dla różnych poziomów logowania.
        """
        # Użyj self.logger (który jest instancją AppLogger lub standardowym loggerem)
        self.logger.debug("Debug: Inicjalizacja zakończona pomyślnie (z MainWindow)")
        self.logger.info("Info: Aplikacja uruchomiona (z MainWindow)")
        self.logger.warning("Warning: Używana wersja testowa (z MainWindow)")
        self.logger.error("Error: Test obsługi błędów (z MainWindow)")

        if self._preferences.get("log_ui_to_console", False):
            self.logger.info("UI: Logowanie akcji interfejsu włączone (z MainWindow)")

    def load_preferences_async(self):
        """
        Wczytuje preferencje asynchronicznie.
        """
        task_id = self.thread_manager.submit_task(
            self.file_worker.load_preferences, self.config_path
        )
        self.logger.info(f"Started preferences loading task: {task_id}")

    def save_preferences_async(self):
        """
        Zapisuje preferencje asynchronicznie.
        """
        task_id = self.thread_manager.submit_task(
            self.file_worker.save_preferences, self.config_path, self._preferences
        )
        self.logger.info(f"Started preferences saving task: {task_id}")
        self.status_bar.showMessage(TranslationManager.translate("app.status.saving"))

    def show_preferences_dialog(self):
        """
        Wyświetla okno dialogowe preferencji.
        """
        dialog = PreferencesDialog(self._preferences, self)
        if dialog.exec():
            new_preferences = dialog.get_preferences()
            # Sprawdź, czy preferencje faktycznie się zmieniły
            if self._preferences != new_preferences:
                self._preferences.update(new_preferences)
                self.save_preferences_async()
                self.logger.info(f"Preferences updated: {new_preferences}")
                # Aktualizujemy język jeśli się zmienił
                if (
                    "language" in new_preferences
                    and TranslationManager.get_current_language()
                    != new_preferences["language"]
                ):
                    TranslationManager.set_language(new_preferences["language"])
                    self.logger.info(
                        f"Language changed to: {new_preferences['language']}"
                    )

                # Zastosuj inne zmiany, np. poziom logowania, jeśli AppLogger jest dostępny
                if self.app_logger and "log_level" in new_preferences:
                    self.app_logger.config["log_level"] = new_preferences["log_level"]
                    self.app_logger.setup_logger()  # Rekonfiguruj logger
                    self.logger.info(
                        f"Log level changed to: {new_preferences['log_level']}"
                    )
            else:
                self.logger.info("Preferences dialog closed without changes.")

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

    def update_translations(self):
        """
        Aktualizuje wszystkie teksty w interfejsie użytkownika.
        """
        self.setWindowTitle(TranslationManager.translate("app.title"))

        # Aktualizacja zakładek
        self.tabs.setTabText(0, TranslationManager.translate("app.tabs.tab1"))
        self.tabs.setTabText(1, TranslationManager.translate("app.tabs.tab2"))
        self.tabs.setTabText(2, TranslationManager.translate("app.tabs.tab3"))
        self.tabs.setTabText(3, TranslationManager.translate("app.tabs.console.title"))

        # Aktualizacja statusu
        self.status_bar.showMessage(TranslationManager.translate("app.status.ready"))

        # Aktualizacja menu
        create_menu_bar(self)

        # Aktualizacja zawartości zakładek - tylko jeśli zostały już załadowane
        # Sprawdzamy czy widgets zostały załadowane (lazy loading)
        if hasattr(self, "_lazy_tab1_widget"):
            self._tab_widgets["tab1"].update_translations()

        if hasattr(self, "_lazy_tab2_widget"):
            self._tab_widgets["tab2"].update_translations()

        if hasattr(self, "_lazy_tab3_widget"):
            self._tab_widgets["tab3"].update_translations()

        # Aktualizacja console widget jeśli został załadowany
        if "console" in self._tab_widgets:
            console_widget = self._tab_widgets["console"]
            if hasattr(console_widget, "update_translations"):
                console_widget.update_translations()

    def closeEvent(self, event):
        """
        Obsługuje zdarzenie zamknięcia okna.

        Args:
            event: Zdarzenie zamknięcia
        """
        if self._preferences.get("remember_window_size", True):
            self._preferences["window_size"] = {
                "width": self.size().width(),
                "height": self.size().height(),
            }
            self._preferences["window_position"] = {
                "x": self.pos().x(),
                "y": self.pos().y(),
            }
            self.save_preferences_async()  # Zapisz preferencje przed zamknięciem

        reply = QMessageBox.question(
            self,
            TranslationManager.translate("app.dialogs.exit.title"),
            TranslationManager.translate("app.dialogs.exit.message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("Zamykanie aplikacji...")
            self.thread_manager.cleanup()  # Najpierw wątki
            if self.app_logger:  # Następnie logger aplikacji
                self.app_logger.cleanup()
            event.accept()
        else:
            event.ignore()

    def _get_console_tab(self):
        """Get or create console tab widget."""
        if "console" not in self._tab_widgets:
            self.logger.debug("Lazy loading ConsoleWidget...")
            # ConsoleWidget nie potrzebuje już app_logger w konstruktorze
            self._tab_widgets["console"] = ConsoleWidget(parent=self)
            # Rejestracja handlera, jeśli app_logger jest dostępny
            if self.app_logger and hasattr(self._tab_widgets["console"], "append_log"):
                self.app_logger.set_console_widget_handler(
                    self._tab_widgets["console"].append_log
                )
                self.logger.info(
                    "ConsoleWidget handler (lazy-loaded) registered with AppLogger."
                )
        return self._tab_widgets["console"]

    def _create_placeholder_widget(self, tab_name):
        """Create a lightweight placeholder widget."""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        label = QLabel(f"Loading {tab_name}...")
        label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(label)
        return placeholder

    def _on_tab_changed(self, index):
        """Handle tab change to implement lazy loading."""
        # Get current tab widget
        current_widget = self.tabs.widget(index)

        # Check if it's a placeholder that needs replacement
        if hasattr(current_widget, "findChild") and current_widget.findChild(QLabel):
            label = current_widget.findChild(QLabel)
            if label and "Loading" in label.text():
                # This is a placeholder, replace with real widget
                if index == 1:  # Tab 2
                    real_widget = self._tab_widgets["tab2"]
                    self.tabs.removeTab(index)
                    self.tabs.insertTab(
                        index,
                        real_widget,
                        TranslationManager.translate("app.tabs.tab2"),
                    )
                elif index == 2:  # Tab 3
                    real_widget = self._tab_widgets["tab3"]
                    self.tabs.removeTab(index)
                    self.tabs.insertTab(
                        index,
                        real_widget,
                        TranslationManager.translate("app.tabs.tab3"),
                    )
                elif index == 3:  # Console
                    real_widget = self._get_console_tab()
                    self.tabs.removeTab(index)
                    self.tabs.insertTab(
                        index,
                        real_widget,
                        TranslationManager.translate("app.tabs.console.title"),
                    )

                # Set the current tab back to the replaced one
                self.tabs.setCurrentIndex(index)
                logging.info(f"Lazy loaded tab at index {index}")

    @property
    def preferences(self):
        return self._preferences

    @preferences.setter
    def preferences(self, value):
        self._preferences = value
        self._apply_window_settings()

    def _apply_window_settings(self):
        """
        Stosuje ustawienia okna na podstawie preferencji.
        """
        if self._preferences.get("remember_window_size", True):
            window_size = self._preferences.get(
                "window_size", {"width": 800, "height": 600}
            )
            window_pos = self._preferences.get("window_position", {"x": 100, "y": 100})
            self.setGeometry(
                window_pos["x"],
                window_pos["y"],
                window_size["width"],
                window_size["height"],
            )
