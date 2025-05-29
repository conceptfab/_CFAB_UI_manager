import json
import logging
import os

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStatusBar, QTabWidget

from UI.components.console_widget import ConsoleWidget
from UI.components.menu_bar import create_menu_bar
from UI.components.tab_one_widget import TabOneWidget
from UI.components.tab_three_widget import TabThreeWidget
from UI.components.tab_two_widget import TabTwoWidget
from UI.hardware_profiler import HardwareProfilerDialog
from UI.preferences_dialog import PreferencesDialog

# from UI.components.status_bar_manager import StatusBarManager # Jeśli używasz


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moja Zaawansowana Aplikacja PyQt6")
        self.setGeometry(100, 100, 800, 600)

        # Preferencje
        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
        )
        self.preferences = self.load_preferences()

        # Menu
        create_menu_bar(self)  # Przekazujemy self (QMainWindow)

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

        # Pasek Statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Gotowy.")
        # Jeśli używasz StatusBarManager:
        # self.status_manager = StatusBarManager(self.status_bar)
        # self.status_manager.set_message("Gotowy przez managera.")

        # Testowe logi
        logger = logging.getLogger("AppLogger")
        logger.info("Aplikacja uruchomiona")
        logger.debug("Debug: Test debug")
        logger.warning("Uwaga: Test warning")
        logger.error("Błąd: Test error")

    def load_preferences(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"show_splash": True}

    def save_preferences(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu preferencji: {e}")

    def show_preferences_dialog(self):
        dialog = PreferencesDialog(self.preferences, self)
        if dialog.exec():
            self.preferences.update(dialog.get_preferences())
            self.save_preferences()
            self.status_bar.showMessage("Zapisano preferencje.")

    def show_hardware_profiler(self):
        dialog = HardwareProfilerDialog(self)
        dialog.exec()

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def closeEvent(self, event):
        # Tutaj możesz dodać logikę przed zamknięciem, np. zapis stanu
        reply = QMessageBox.question(
            self,
            "Zamykanie Aplikacji",
            "Czy na pewno chcesz zamknąć aplikację?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            print("Zamykanie aplikacji...")
            event.accept()
        else:
            event.ignore()


# Dodaj import QMessageBox jeśli go używasz w closeEvent
from PyQt6.QtWidgets import QMessageBox
