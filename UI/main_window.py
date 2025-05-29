from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from UI.components.menu_bar import create_menu_bar
from UI.components.tab_one_widget import TabOneWidget
from UI.components.tab_two_widget import TabTwoWidget
from UI.components.tab_three_widget import TabThreeWidget
# from UI.components.status_bar_manager import StatusBarManager # Jeśli używasz

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moja Zaawansowana Aplikacja PyQt6")
        self.setGeometry(100, 100, 800, 600)

        # Menu
        create_menu_bar(self) # Przekazujemy self (QMainWindow), aby menu mogło być do niego dodane

        # Zakładki
        self.tabs = QTabWidget()
        self.tab1 = TabOneWidget()
        self.tab2 = TabTwoWidget()
        self.tab3 = TabThreeWidget()

        self.tabs.addTab(self.tab1, "Zakładka 1")
        self.tabs.addTab(self.tab2, "Zakładka 2")
        self.tabs.addTab(self.tab3, "Zakładka 3")

        self.setCentralWidget(self.tabs)

        # Pasek Statusu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Gotowy.")
        # Jeśli używasz StatusBarManager:
        # self.status_manager = StatusBarManager(self.status_bar)
        # self.status_manager.set_message("Gotowy przez managera.")

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def closeEvent(self, event):
        # Tutaj możesz dodać logikę przed zamknięciem, np. zapis stanu
        reply = QMessageBox.question(self, 'Zamykanie Aplikacji',
                                     "Czy na pewno chcesz zamknąć aplikację?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            print("Zamykanie aplikacji...")
            event.accept()
        else:
            event.ignore()

# Dodaj import QMessageBox jeśli go używasz w closeEvent
from PyQt6.QtWidgets import QMessageBox