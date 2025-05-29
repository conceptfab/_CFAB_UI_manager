import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from UI.main_window import MainWindow
import os

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Ustaw ikonę aplikacji (pasek zadań)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "img", "icon.png")
    app.setWindowIcon(QIcon(icon_path))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(base_dir, "resources", "styles.qss")

    print(f"DEBUG: Próba załadowania QSS dla PROSTEJ APLIKACJI z: {style_path}")

    if os.path.exists(style_path):
        try:
            with open(style_path, "r", encoding='utf-8') as f:
                app.setStyleSheet(f.read())
            print(f"DEBUG: Pomyślnie załadowano style dla PROSTEJ APLIKACJI z: {style_path}")
        except Exception as e:
            print(f"DEBUG: BŁĄD ładowania QSS dla PROSTEJ APLIKACJI: {e}")
    else:
        print(f"DEBUG: OSTRZEŻENIE: Plik QSS dla PROSTEJ APLIKACJI nie znaleziony: {style_path}")

    main_win = MainWindow()
    # Ustaw ikonę okna głównego
    main_win.setWindowIcon(QIcon(icon_path))
    main_win.show()
    sys.exit(app.exec())