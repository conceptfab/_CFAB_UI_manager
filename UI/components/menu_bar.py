from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMessageBox # Potrzebne dla "O Programie"

def show_about_dialog(main_window):
    QMessageBox.about(main_window, "O Programie",
                      "Moja Zaawansowana Aplikacja PyQt6\n\n"
                      "Wersja 1.0\n"
                      "Stworzona z użyciem PyQt6.")

def create_menu_bar(main_window): # Otrzymuje instancję QMainWindow
    menu_bar = main_window.menuBar() # Używamy menuBar() z QMainWindow

    # Menu Plik
    file_menu = menu_bar.addMenu("&Plik")

    new_action = QAction("&Nowy", main_window)
    new_action.setShortcut("Ctrl+N")
    new_action.setStatusTip("Tworzy nowy plik")
    new_action.triggered.connect(lambda: main_window.update_status("Wybrano Nowy")) # Przykład użycia statusu
    file_menu.addAction(new_action)

    open_action = QAction("&Otwórz", main_window)
    open_action.setShortcut("Ctrl+O")
    open_action.setStatusTip("Otwiera istniejący plik")
    open_action.triggered.connect(lambda: main_window.update_status("Wybrano Otwórz"))
    file_menu.addAction(open_action)

    file_menu.addSeparator()

    exit_action = QAction("&Zakończ", main_window)
    exit_action.setShortcut("Ctrl+Q")
    exit_action.setStatusTip("Zamyka aplikację")
    exit_action.triggered.connect(main_window.close)
    file_menu.addAction(exit_action)

    # Menu Edycja
    edit_menu = menu_bar.addMenu("&Edycja")
    copy_action = QAction("&Kopiuj", main_window)
    copy_action.setShortcut("Ctrl+C")
    copy_action.setStatusTip("Kopiuje zaznaczenie")
    # copy_action.triggered.connect(lambda: print("Kopiuj")) # Dodaj odpowiednią logikę
    edit_menu.addAction(copy_action)

    # Menu Pomoc
    help_menu = menu_bar.addMenu("&Pomoc")
    about_action = QAction("&O Programie", main_window)
    about_action.setStatusTip("Wyświetla informacje o programie")
    about_action.triggered.connect(lambda: show_about_dialog(main_window))
    help_menu.addAction(about_action)

    return menu_bar