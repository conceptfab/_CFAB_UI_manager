import json
import os
import platform
import uuid

import psutil
from PyQt6.QtCore import QDateTime, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class HardwareProfilerThread(QThread):
    profile_ready = pyqtSignal(dict)

    def run(self):
        profile = {
            "uuid": str(uuid.uuid4()),
            "system": platform.system(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "timestamp": str(QDateTime.currentDateTime().toString()),
        }
        self.profile_ready.emit(profile)


class HardwareProfilerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hardware Profiler")
        self.setMinimumSize(600, 400)
        self.profile_data = {}
        self.hardware_path = os.path.join(
            os.path.dirname(__file__), "..", "hardware.json"
        )

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
        cpu_count = self.profile_data.get("cpu_count", 0)
        memory_gb = self.profile_data.get("memory_total", 0) // (1024**3)

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
                with open(self.hardware_path, "r", encoding="utf-8") as f:
                    self.profile_data = json.load(f)
                self.display_profile()
            except Exception as e:
                print(f"Błąd wczytywania profilu: {e}")

    def save_profile(self):
        if not self.profile_data:
            return

        try:
            with open(self.hardware_path, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=2, ensure_ascii=False)
            self.parent().update_status("Profil sprzętowy zapisany.")
        except Exception as e:
            print(f"Błąd zapisu profilu: {e}")
