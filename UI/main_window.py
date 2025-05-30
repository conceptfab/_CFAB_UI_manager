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
from utils.improved_thread_manager import ImprovedThreadManager
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

    def __init__(self, *args, **kwargs):
        try:
            logging.info("MainWindow: start __init__")
            super().__init__(*args, **kwargs)
            translator = TranslationManager.get_translator()
            self.setWindowTitle(translator.translate("app.title"))
            self.thread_manager = ImprovedThreadManager()
            self.file_worker = FileWorker()

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

            # Konfiguracja logowania
            self.configure_logging()

            # Inicjalizacja interfejsu
            self._init_ui()

            # Rejestracja głównego okna w TranslationManager
            TranslationManager.register_widget(self)
            logging.info("MainWindow: koniec __init__")
        except Exception as e:
            logging.error(f"MainWindow: wyjątek w __init__: {e}")
            QMessageBox.critical(None, "Błąd MainWindow", f"Wyjątek w MainWindow:\n{e}")
            raise

    @performance_monitor.measure_execution_time("main_window_init")
    def _init_ui(self):
        """
        Inicjalizuje elementy interfejsu użytkownika z optymalizacjami wydajności.
        """
        translator = TranslationManager.get_translator()
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
            self._tab_widgets["tab1"], translator.translate("app.tabs.tab1")
        )
        self.tabs.addTab(
            self._tab_widgets["tab2"], translator.translate("app.tabs.tab2")
        )
        self.tabs.addTab(
            self._tab_widgets["tab3"], translator.translate("app.tabs.tab3")
        )
        self.tabs.addTab(
            self._tab_widgets["console"], translator.translate("app.tabs.console.title")
        )

        self.setCentralWidget(self.tabs)

        # Pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(translator.translate("app.status.ready"))
        # Jeśli używasz StatusBarManager:
        # self.status_manager = StatusBarManager(self.status_bar)
        # self.status_manager.set_message("Gotowy przez managera.")

        # Testowe logi
        self._log_test_messages()

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
        logging.debug("Inicjalizacja ConsoleWidget...")
        widget = ConsoleWidget()
        TranslationManager.register_widget(widget)
        self._tab_widgets["console"] = widget

    def _log_test_messages(self):
        """
        Loguje testowe wiadomości dla różnych poziomów logowania.
        """
        logger = logging.getLogger("AppLogger")
        logger.info("Aplikacja uruchomiona")
        logger.debug("Debug: Inicjalizacja zakończona pomyślnie")
        logger.warning("Uwaga: Używana wersja testowa")
        logger.error("Błąd: Test obsługi błędów")

        if self._preferences.get("log_ui_to_console", False):
            logger.info("UI: Logowanie akcji interfejsu włączone")

    def configure_logging(self):
        """
        Konfiguruje system logowania na podstawie preferencji.
        """
        logger = logging.getLogger("AppLogger")
        log_level = self._preferences.get("log_level", "INFO")
        logger.setLevel(getattr(logging, log_level))

        # Usuń wszystkie istniejące handlery
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        if self._preferences.get("log_to_file", False):
            log_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "app.log"
            )
            file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    def load_preferences_async(self):
        """
        Wczytuje preferencje asynchronicznie.
        """
        task_id = self.thread_manager.submit_task(
            self.file_worker.load_preferences, self.config_path
        )
        # Note: Z improved thread manager będziemy potrzebować inny sposób na callback
        # To zostanie poprawione w następnej iteracji
        logging.info(f"Started preferences loading task: {task_id}")

    def save_preferences_async(self):
        """
        Zapisuje preferencje asynchronicznie.
        """
        task_id = self.thread_manager.submit_task(
            self.file_worker.save_preferences, self.config_path, self._preferences
        )
        logging.info(f"Started preferences saving task: {task_id}")
        self.status_bar.showMessage(
            TranslationManager.get_translator().translate("app.status.saving")
        )

    def show_preferences_dialog(self):
        """
        Wyświetla okno dialogowe preferencji.
        """
        dialog = PreferencesDialog(self._preferences, self)
        if dialog.exec():
            new_preferences = dialog.get_preferences()
            self._preferences.update(new_preferences)
            self.save_preferences_async()
            # Aktualizujemy język jeśli się zmienił
            if "language" in new_preferences:
                TranslationManager.set_language(new_preferences["language"])

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
        translator = TranslationManager.get_translator()
        self.setWindowTitle(translator.translate("app.title"))

        # Aktualizacja zakładek
        self.tabs.setTabText(0, translator.translate("app.tabs.tab1"))
        self.tabs.setTabText(1, translator.translate("app.tabs.tab2"))
        self.tabs.setTabText(2, translator.translate("app.tabs.tab3"))
        self.tabs.setTabText(3, translator.translate("app.tabs.console.title"))

        # Aktualizacja statusu
        self.status_bar.showMessage(translator.translate("app.status.ready"))

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
            self.save_preferences_async()

        translator = TranslationManager.get_translator()
        reply = QMessageBox.question(
            self,
            translator.translate("app.dialogs.exit.title"),
            translator.translate("app.dialogs.exit.message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            logging.info("Zamykanie aplikacji...")
            self.thread_manager.cleanup()
            event.accept()
        else:
            event.ignore()

    def _get_console_tab(self):
        """Get or create console tab widget."""
        if "console" not in self._tab_widgets:
            logging.debug("Lazy loading ConsoleWidget...")
            self._tab_widgets["console"] = ConsoleWidget()
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
                        TranslationManager.get_translator().translate("app.tabs.tab2"),
                    )
                elif index == 2:  # Tab 3
                    real_widget = self._tab_widgets["tab3"]
                    self.tabs.removeTab(index)
                    self.tabs.insertTab(
                        index,
                        real_widget,
                        TranslationManager.get_translator().translate("app.tabs.tab3"),
                    )
                elif index == 3:  # Console
                    real_widget = self._get_console_tab()
                    self.tabs.removeTab(index)
                    self.tabs.insertTab(
                        index,
                        real_widget,
                        TranslationManager.get_translator().translate(
                            "app.tabs.console.title"
                        ),
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
