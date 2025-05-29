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

    def __init__(self):
        """
        Inicjalizuje główne okno aplikacji.
        """
        super().__init__()
        self.setWindowTitle("Moja Zaawansowana Aplikacja PyQt6")
        self.thread_manager = ThreadManager()
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
            "language": "en",
        }

        # Inicjalizacja TranslationManager
        TranslationManager.initialize(self._preferences["language"])

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

    def _init_ui(self):
        """
        Inicjalizuje elementy interfejsu użytkownika.
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
        self.tab1 = TabOneWidget()
        self.tab2 = TabTwoWidget()
        self.tab3 = TabThreeWidget()
        self.console_tab = ConsoleWidget()

        # Rejestracja zakładek w TranslationManager
        TranslationManager.register_widget(self.tab1)
        TranslationManager.register_widget(self.tab2)
        TranslationManager.register_widget(self.tab3)

        self.tabs.addTab(self.tab1, "Tab 1")
        self.tabs.addTab(self.tab2, "Tab 2")
        self.tabs.addTab(self.tab3, "Tab 3")
        self.tabs.addTab(self.console_tab, "Console")

        self.setCentralWidget(self.tabs)

        # Pasek statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
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

        if self._preferences.get("log_ui_to_console", False):
            logger.info("UI: Logowanie akcji interfejsu włączone")

    def configure_logging(self):
        """
        Konfiguruje system logowania na podstawie preferencji.
        """
        logger = logging.getLogger("AppLogger")
        log_level = self._preferences.get("log_level", "INFO")
        logger.setLevel(getattr(logging, log_level))

        if self._preferences.get("log_to_file", False):
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
            print(f"Wczytano preferencje: {preferences}")
            self._preferences.update(preferences)
            # Stosujemy ustawienia okna
            self._apply_window_settings()
            # Aktualizujemy język
            if "language" in preferences:
                print(f"Zmiana języka na: {preferences['language']}")
                TranslationManager.set_language(preferences["language"])
                self.update_translations()

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
            self.file_worker.save_preferences, self.config_path, self._preferences
        )
        worker.finished.connect(
            lambda _: self.status_bar.showMessage(
                TranslationManager.get_translator().translate("app.status.saving")
            )
        )
        worker.error.connect(
            lambda e: self.status_bar.showMessage(
                TranslationManager.get_translator().translate(
                    "app.status.error", str(e)
                )
            )
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
                self.update_translations()

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

        # Aktualizacja tytułu okna
        self.setWindowTitle(translator.translate("app.title"))

        # Aktualizacja menu
        create_menu_bar(self)

        # Aktualizacja nazw zakładek
        self.tabs.setTabText(0, translator.translate("app.tabs.tab1"))
        self.tabs.setTabText(1, translator.translate("app.tabs.tab2"))
        self.tabs.setTabText(2, translator.translate("app.tabs.tab3"))
        self.tabs.setTabText(3, translator.translate("app.tabs.console"))

        # Aktualizacja zawartości zakładek
        self.tab1.label.setText(translator.translate("app.tabs.content.tab1.content"))
        self.tab1.button.setText(translator.translate("app.tabs.content.tab1.button"))
        self.tab1.line_edit.setPlaceholderText(
            translator.translate("app.tabs.content.tab1.placeholder")
        )

        self.tab2.label.setText(translator.translate("app.tabs.content.tab2.content"))
        self.tab2.checkbox.setText(
            translator.translate("app.tabs.content.tab2.checkbox")
        )
        self.tab2.spinbox_label.setText(
            translator.translate("app.tabs.content.tab2.select_value")
        )

        self.tab3.label.setText(translator.translate("app.tabs.content.tab3.content"))
        self.tab3.text_edit.setPlaceholderText(
            translator.translate("app.tabs.content.tab3.placeholder")
        )
        self.tab3.button.setText(
            translator.translate("app.tabs.content.tab3.show_text")
        )

        # Aktualizacja paska statusu
        self.status_bar.showMessage(translator.translate("app.status.ready"))

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
            print("Zamykanie aplikacji...")
            self.thread_manager.cleanup()
            event.accept()
        else:
            event.ignore()

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


# Dodaj import QMessageBox jeśli go używasz w closeEvent
from PyQt6.QtWidgets import QMessageBox
