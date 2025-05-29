import json
import os
import sys

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from UI.main_window import MainWindow
from UI.splash_screen import SplashScreen
from utils.logger import AppLogger
from utils.thread_manager import ThreadManager


class ConfigLoader(QObject):
    """
    Klasa odpowiedzialna za asynchroniczne wczytywanie konfiguracji.
    """

    config_loaded = pyqtSignal(dict)
    error = pyqtSignal(Exception)

    def load_config(self):
        """
        Wczytuje konfigurację z pliku config.json.
        Emituje sygnał config_loaded z konfiguracją lub error w przypadku błędu.
        """
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "config.json")

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.config_loaded.emit(config)
        except Exception as e:
            self.error.emit(e)


def verify_hardware_profile():
    """
    Weryfikuje czy istnieje profil sprzętowy.

    Returns:
        bool: True jeśli profil istnieje i został poprawnie wczytany,
              False w przeciwnym razie
    """
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


class Application(QApplication):
    """
    Rozszerzona klasa aplikacji z obsługą konfiguracji.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = {
            "show_splash": True,
            "log_to_file": False,
            "log_ui_to_console": False,
            "log_level": "INFO",
        }

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value


if __name__ == "__main__":
    # Inicjalizacja aplikacji
    app = Application(sys.argv)
    thread_manager = ThreadManager()

    # Sekwencja startowa
    print("=== Sekwencja startowa ===")

    # 1. Wczytanie konfiguracji w osobnym wątku
    print("1. Wczytywanie konfiguracji...")
    config_loader = ConfigLoader()
    config_loader.config_loaded.connect(lambda config: setattr(app, "_config", config))
    thread_manager.run_in_thread(config_loader.load_config)

    # 2. Inicjalizacja loggera
    print("2. Inicjalizacja systemu logowania...")
    logger = AppLogger(app.config)
    logger.info("Aplikacja uruchomiona")

    # 3. Weryfikacja profilu sprzętowego w osobnym wątku
    print("3. Weryfikacja profilu sprzętowego...")
    thread_manager.run_in_thread(verify_hardware_profile)

    # Konfiguracja interfejsu
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "resources", "img", "icon.png")
    app.setWindowIcon(QIcon(icon_path))

    # Wczytywanie stylów CSS
    def load_styles():
        """
        Wczytuje style CSS z pliku.

        Returns:
            str: Zawartość pliku ze stylami lub pusty string w przypadku błędu
        """
        style_path = os.path.join(base_dir, "resources", "styles.qss")
        if os.path.exists(style_path):
            try:
                with open(style_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Błąd ładowania stylów: {e}")
                return ""
        return ""

    def on_styles_loaded(styles):
        """
        Obsługuje załadowane style CSS.

        Args:
            styles (str): Zawartość pliku ze stylami
        """
        if styles:
            app.setStyleSheet(styles)
            logger.info("Załadowano style")

    # Wczytaj style w osobnym wątku
    thread_manager.run_in_thread(load_styles).finished.connect(on_styles_loaded)

    # Inicjalizacja głównego okna
    logger.info("Inicjalizacja głównego okna")
    main_win = MainWindow()
    main_win.setWindowIcon(QIcon(icon_path))
    main_win.logger = logger

    # Obsługa splash screenu
    splash = None
    if app.config.get("show_splash", True):
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

        # Używamy QTimer zamiast time.sleep
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: (splash.close(), main_win.show()))
        timer.start(3000)
    else:
        main_win.show()

    logger.info("Główne okno wyświetlone")
    print("=== Aplikacja gotowa ===")

    # Czyszczenie wątków przy zamknięciu
    app.aboutToQuit.connect(thread_manager.cleanup)

    sys.exit(app.exec())
