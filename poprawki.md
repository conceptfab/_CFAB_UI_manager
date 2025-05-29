1. Hardware Profiler - Nowy moduł
Zmiana w pliku UI/components/menu_bar.py, w funkcji create_menu_bar()
Dodanie opcji Hardware Profiler do menu Edycja:
python# Menu Edycja
edit_menu = menu_bar.addMenu("&Edycja")
copy_action = QAction("&Kopiuj", main_window)
copy_action.setShortcut("Ctrl+C")
copy_action.setStatusTip("Kopiuje zaznaczenie")
edit_menu.addAction(copy_action)

# Dodaj separator i Hardware Profiler
edit_menu.addSeparator()
hardware_profiler_action = QAction("Hardware Profiler", main_window)
hardware_profiler_action.setStatusTip("Konfiguracja profilu sprzętowego")
hardware_profiler_action.triggered.connect(main_window.show_hardware_profiler)
edit_menu.addAction(hardware_profiler_action)

# Separator i Preferencje
edit_menu.addSeparator()
preferences_action = QAction("Preferencje", main_window)
preferences_action.setStatusTip("Ustawienia aplikacji")
preferences_action.triggered.connect(main_window.show_preferences_dialog)
edit_menu.addAction(preferences_action)
Nowy plik UI/hardware_profiler.py
Utworzenie okna Hardware Profiler:
pythonfrom PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QGroupBox, QFormLayout)
from PyQt6.QtCore import QThread, pyqtSignal
import json
import os
import platform
import psutil
import uuid

class HardwareProfilerThread(QThread):
    profile_ready = pyqtSignal(dict)
    
    def run(self):
        profile = {
            "uuid": str(uuid.uuid4()),
            "system": platform.system(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "timestamp": str(QDateTime.currentDateTime().toString())
        }
        self.profile_ready.emit(profile)

class HardwareProfilerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hardware Profiler")
        self.setMinimumSize(600, 400)
        self.profile_data = {}
        self.hardware_path = os.path.join(os.path.dirname(__file__), '..', 'hardware.json')
        
        self.init_ui()
        self.load_existing_profile()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Grupa aktualnej konfiguracji
        current_group = QGroupBox("Aktualna konfiguracja sprzętowa")
        current_layout = QVBoxLayout(current_group)
        
        self.config_display = QTextEdit()
        self.config_display.setReadOnly(True)
        current_layout.addWidget(self.config_display)
        
        layout.addWidget(current_group)
        
        # Grupa optymalizacji
        optimization_group = QGroupBox("Dostępne optymalizacje")
        opt_layout = QVBoxLayout(optimization_group)
        
        self.optimization_display = QTextEdit()
        self.optimization_display.setReadOnly(True)
        opt_layout.addWidget(self.optimization_display)
        
        layout.addWidget(optimization_group)
        
        # Przyciski
        button_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("Skanuj sprzęt")
        self.scan_btn.clicked.connect(self.scan_hardware)
        
        self.save_btn = QPushButton("Zapisz profil")
        self.save_btn.clicked.connect(self.save_profile)
        
        self.close_btn = QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.scan_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def scan_hardware(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Skanowanie...")
        
        self.thread = HardwareProfilerThread()
        self.thread.profile_ready.connect(self.on_profile_ready)
        self.thread.start()
    
    def on_profile_ready(self, profile):
        self.profile_data = profile
        self.display_profile()
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Skanuj sprzęt")
    
    def display_profile(self):
        if not self.profile_data:
            return
            
        config_text = f"""UUID: {self.profile_data.get('uuid', 'N/A')}
System: {self.profile_data.get('system', 'N/A')}
Procesor: {self.profile_data.get('processor', 'N/A')}
Liczba rdzeni: {self.profile_data.get('cpu_count', 'N/A')}
Pamięć RAM: {self.profile_data.get('memory_total', 0) // (1024**3)} GB
Ostatnia aktualizacja: {self.profile_data.get('timestamp', 'N/A')}"""
        
        self.config_display.setText(config_text)
        
        # Przykładowe optymalizacje na podstawie profilu
        optimizations = self.generate_optimizations()
        self.optimization_display.setText(optimizations)
    
    def generate_optimizations(self):
        if not self.profile_data:
            return "Brak danych profilu do analizy."
            
        opts = []
        cpu_count = self.profile_data.get('cpu_count', 0)
        memory_gb = self.profile_data.get('memory_total', 0) // (1024**3)
        
        if cpu_count >= 8:
            opts.append("• Włącz wielowątkowe przetwarzanie (8+ rdzeni)")
        elif cpu_count >= 4:
            opts.append("• Częściowa wielowątkowość (4-7 rdzeni)")
        else:
            opts.append("• Tryb pojedynczego wątku (mniej niż 4 rdzenie)")
            
        if memory_gb >= 16:
            opts.append("• Włącz zaawansowane buforowanie (16+ GB RAM)")
        elif memory_gb >= 8:
            opts.append("• Standardowe buforowanie (8-15 GB RAM)")
        else:
            opts.append("• Ograniczone buforowanie (mniej niż 8 GB RAM)")
            
        return "\n".join(opts) if opts else "Brak dostępnych optymalizacji."
    
    def load_existing_profile(self):
        if os.path.exists(self.hardware_path):
            try:
                with open(self.hardware_path, 'r', encoding='utf-8') as f:
                    self.profile_data = json.load(f)
                self.display_profile()
            except Exception as e:
                print(f"Błąd wczytywania profilu: {e}")
    
    def save_profile(self):
        if not self.profile_data:
            return
            
        try:
            with open(self.hardware_path, 'w', encoding='utf-8') as f:
                json.dump(self.profile_data, f, indent=2, ensure_ascii=False)
            self.parent().update_status("Profil sprzętowy zapisany.")
        except Exception as e:
            print(f"Błąd zapisu profilu: {e}")
2. Zapamiętanie wielkości okna
Zmiana w pliku UI/main_window.py, w klasie MainWindow
Dodanie obsługi zapisywania/wczytywania wielkości okna:
pythondef __init__(self):
    super().__init__()
    self.setWindowTitle("Moja Zaawansowana Aplikacja PyQt6")
    
    # Preferencje
    self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')
    self.preferences = self.load_preferences()
    
    # Wczytaj zapisaną wielkość okna lub ustaw domyślną
    window_size = self.preferences.get("window_size", {"width": 800, "height": 600})
    window_pos = self.preferences.get("window_position", {"x": 100, "y": 100})
    
    self.setGeometry(window_pos["x"], window_pos["y"], 
                     window_size["width"], window_size["height"])

def show_hardware_profiler(self):
    from UI.hardware_profiler import HardwareProfilerDialog
    dialog = HardwareProfilerDialog(self)
    dialog.exec()

def closeEvent(self, event):
    # Zapisz wielkość i pozycję okna
    geometry = self.geometry()
    self.preferences["window_size"] = {
        "width": geometry.width(),
        "height": geometry.height()
    }
    self.preferences["window_position"] = {
        "x": geometry.x(),
        "y": geometry.y()
    }
    self.save_preferences()
    
    # Reszta logiki zamykania...
    reply = QMessageBox.question(self, 'Zamykanie Aplikacji',
                                 "Czy na pewno chcesz zamknąć aplikację?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No)

    if reply == QMessageBox.StandardButton.Yes:
        print("Zamykanie aplikacji...")
        event.accept()
    else:
        event.ignore()
3. Wyodrębnienie okna About
Nowy plik UI/about_dialog.py
Przeniesienie dialogu "O Programie" do osobnego pliku:
pythonfrom PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("O Programie")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Logo/ikona aplikacji (opcjonalnie)
        # logo_label = QLabel()
        # logo_pixmap = QPixmap("resources/img/icon.png").scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio)
        # logo_label.setPixmap(logo_pixmap)
        # logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(logo_label)
        
        # Nazwa aplikacji
        title_label = QLabel("Moja Zaawansowana Aplikacja PyQt6")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Wersja
        version_label = QLabel("Wersja 1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Opis
        description_label = QLabel("Stworzona z użyciem PyQt6\n\nAplikacja demonstracyjna z zaawansowanymi funkcjami interfejsu użytkownika.")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        layout.addStretch()
        
        # Przycisk OK
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
Zmiana w pliku UI/components/menu_bar.py
Aktualizacja funkcji obsługi menu About:
pythonfrom UI.about_dialog import AboutDialog

def show_about_dialog(main_window):
    dialog = AboutDialog(main_window)
    dialog.exec()
4. Dodanie systemu logowania
Zmiana w pliku UI/preferences_dialog.py
Rozszerzenie okna preferencji o opcje logowania:
pythonfrom PyQt6.QtWidgets import (QDialog, QVBoxLayout, QCheckBox, QPushButton, 
                             QHBoxLayout, QGroupBox, QComboBox, QFormLayout)

class PreferencesDialog(QDialog):
    def __init__(self, preferences: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencje")
        self.setMinimumWidth(400)
        self.preferences = preferences
        
        layout = QVBoxLayout(self)
        
        # Grupa: Ogólne
        general_group = QGroupBox("Ogólne")
        general_layout = QFormLayout(general_group)
        
        self.splash_checkbox = QCheckBox("Pokazuj ekran powitalny (splash screen)")
        self.splash_checkbox.setChecked(preferences.get("show_splash", True))
        general_layout.addRow(self.splash_checkbox)
        
        self.remember_window_checkbox = QCheckBox("Zapamiętuj wielkość okna")
        self.remember_window_checkbox.setChecked(preferences.get("remember_window_size", True))
        general_layout.addRow(self.remember_window_checkbox)
        
        layout.addWidget(general_group)
        
        # Grupa: Logowanie
        logging_group = QGroupBox("Logowanie")
        logging_layout = QFormLayout(logging_group)
        
        self.log_to_file_checkbox = QCheckBox("Zapisuj logi do pliku")
        self.log_to_file_checkbox.setChecked(preferences.get("log_to_file", False))
        logging_layout.addRow(self.log_to_file_checkbox)
        
        self.log_ui_console_checkbox = QCheckBox("Loguj komunikaty UI do konsoli")
        self.log_ui_console_checkbox.setChecked(preferences.get("log_ui_to_console", False))
        logging_layout.addRow(self.log_ui_console_checkbox)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        current_level = preferences.get("log_level", "INFO")
        self.log_level_combo.setCurrentText(current_level)
        logging_layout.addRow("Poziom logowania:", self.log_level_combo)
        
        layout.addWidget(logging_group)
        
        # Przyciski
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Zapisz")
        self.cancel_btn = QPushButton("Anuluj")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_preferences(self):
        return {
            "show_splash": self.splash_checkbox.isChecked(),
            "remember_window_size": self.remember_window_checkbox.isChecked(),
            "log_to_file": self.log_to_file_checkbox.isChecked(),
            "log_ui_to_console": self.log_ui_console_checkbox.isChecked(),
            "log_level": self.log_level_combo.currentText()
        }
Nowy plik utils/logger.py
Utworzenie systemu logowania:
pythonimport logging
import os
from datetime import datetime

class AppLogger:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('AppLogger')
        self.setup_logger()
    
    def setup_logger(self):
        # Poziom logowania
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        log_level = level_map.get(self.config.get('log_level', 'INFO'), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Usuń istniejące handlery
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler (jeśli włączony)
        if self.config.get('log_ui_to_console', False):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler (jeśli włączony)
        if self.config.get('log_to_file', False):
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = os.path.join(log_dir, log_filename)
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)
5. Aktualizacja pliku config.json
Zmiana w pliku config.json
Rozszerzenie konfiguracji o nowe opcje:
json{
  "show_splash": true,
  "remember_window_size": true,
  "window_size": {
    "width": 800,
    "height": 600
  },
  "window_position": {
    "x": 100,
    "y": 100
  },
  "log_to_file": false,
  "log_ui_to_console": false,
  "log_level": "INFO"
}
6. Sekwencja startowa - aktualizacja main_app.py
Zmiana w pliku main_app.py
Dodanie weryfikacji profilu sprzętowego i inicjalizacji loggera:
pythonimport sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from UI.main_window import MainWindow
from UI.splash_screen import SplashScreen
from UI.progress_controller import ProgressController
from utils.logger import AppLogger
import os
import json

def load_config():
    """Wczytuje konfigurację z pliku config.json"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Błąd wczytywania konfiguracji: {e}")
        config = {"show_splash": True, "log_to_file": False, "log_ui_to_console": False, "log_level": "INFO"}
    
    return config

def verify_hardware_profile():
    """Weryfikuje czy istnieje profil sprzętowy"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hardware_path = os.path.join(base_dir, 'hardware.json')
    
    if not os.path.exists(hardware_path):
        print("UWAGA: Brak profilu sprzętowego. Uruchamianie z podstawową konfiguracją.")
        return False
    
    try:
        with open(hardware_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        print(f"Załadowano profil sprzętowy: {profile.get('uuid', 'N/A')}")
        return True
    except Exception as e:
        print(f"Błąd wczytywania profilu sprzętowego: {e}")
        return False

if __name__ == '__main__':
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
            with open(style_path, "r", encoding='utf-8') as f:
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
            progress_bar=False
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
Te zmiany implementują wszystkie funkcjonalności opisane w pliku TODO.md, zapewniając modularną strukturę i łatwą konfigurację aplikacji.