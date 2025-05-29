import json
import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from UI.main_window import MainWindow
from UI.progress_controller import ProgressController
from UI.splash_screen import SplashScreen
from utils.logger import AppLogger


def load_config():
    """Wczytuje konfigurację z pliku config.json"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Błąd wczytywania konfiguracji: {e}")
        config = {
            "show_splash": True,
            "log_to_file": False,
            "log_ui_to_console": False,
            "log_level": "INFO",
        }

    return config


def verify_hardware_profile():
    """Weryfikuje czy istnieje profil sprzętowy"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hardware_path = os.path.join(base_dir, "hardware.json")

    if not os.path.exists(hardware_path):
        print(
            "UWAGA: Brak profilu sprzętowego. "
            "Uruchamianie z podstawową konfiguracją."
        )
        return False

    try:
        with open(hardware_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        print(f"Załadowano profil sprzętowy: {profile.get('uuid', 'N/A')}")
        return True
    except Exception as e:
        print(f"Błąd wczytywania profilu sprzętowego: {e}")
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sekwencja startowa
    print("=== Sekwencja startowa ===")

    # 1. Wczytanie konfiguracji
    print("1. Wczytywanie konfiguracji...")
    config = load_config()

    # 2. Inicjalizacja loggera
    print("2. Inicjalizacja systemu logowania...")
    logger = AppLogger(config)
    logger.info("Aplikacja uruchomiona")

    # 3. Weryfikacja profilu sprzętowego
    print("3. Weryfikacja profilu sprzętowego...")
    has_hardware_profile = verify_hardware_profile()

    if not has_hardware_profile:
        logger.warning("Brak profilu sprzętowego - używana podstawowa konfiguracja")

    # Ikona aplikacji
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "resources", "img", "icon.png")
    app.setWindowIcon(QIcon(icon_path))

    # Style CSS
    style_path = os.path.join(base_dir, "resources", "styles.qss")
    if os.path.exists(style_path):
        try:
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            logger.info(f"Załadowano style z: {style_path}")
        except Exception as e:
            logger.error(f"Błąd ładowania stylów: {e}")

    # Splash screen
    splash = None
    if config.get("show_splash", True):
        logger.info("Wyświetlanie splash screen")
        splash_path = os.path.join(base_dir, "resources", "img", "splash.jpg")
        splash = SplashScreen(
            image_path=splash_path,
            display_time=3000,
            window_size=(642, 250),
            messages=["Ładowanie aplikacji ConceptFab NeuroSorter..."],
            progress_bar=False,
        )
        splash.start()
        app.processEvents()

    # Główne okno aplikacji
    logger.info("Inicjalizacja głównego okna")
    main_win = MainWindow()
    main_win.setWindowIcon(QIcon(icon_path))

    # Przekaż logger do głównego okna
    main_win.logger = logger

    main_win.show()
    logger.info("Główne okno wyświetlone")

    if splash:
        splash.close()

    print("=== Aplikacja gotowa ===")
    sys.exit(app.exec())
