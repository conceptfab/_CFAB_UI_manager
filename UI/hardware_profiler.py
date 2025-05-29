import json
import os
import platform
import subprocess
import time
import uuid

import numpy as np
import psutil
from PyQt6.QtCore import QDateTime, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from utils.translation_manager import TranslationManager

try:
    import cupy as cp

    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False


def get_stable_uuid():
    cpu_id = platform.processor()
    node = platform.node()
    base_str = cpu_id + node
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, base_str))


class HardwareProfilerThread(QThread):
    profile_ready = pyqtSignal(dict)

    def run(self):
        profile = {
            "uuid": get_stable_uuid(),
            "system": platform.system(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "timestamp": str(QDateTime.currentDateTime().toString()),
        }
        # Dodaj wykrywanie GPU na Windows
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output(
                    "wmic path win32_VideoController get name", shell=True
                ).decode(errors="ignore")
                print("WMIC GPU output:", output)  # logowanie do konsoli
                lines = output.strip().split("\n")[1:]
                gpus = [line.strip() for line in lines if line.strip()]
                profile["gpu"] = ", ".join(gpus) if gpus else "Brak danych"
            except Exception as e:
                print("GPU detection error:", e)
                profile["gpu"] = "Brak danych"
        else:
            profile["gpu"] = "Brak danych"

        # Dodaj OPTIMIZATIONS
        cpu_count = profile["cpu_count"]
        memory_gb = profile["memory_total"] // (1024**3)
        optimizations = {
            "multithreading": cpu_count >= 4,
            "advanced_multithreading": cpu_count >= 8,
            "advanced_buffering": memory_gb >= 16,
            "standard_buffering": memory_gb >= 8,
        }
        profile["optimizations"] = optimizations

        # Dodaj PYTHON LIBRARIES
        python_libraries = ["numpy"]
        if optimizations["multithreading"]:
            python_libraries.append("numba")
        if "NVIDIA" in profile["gpu"] and HAS_CUPY:
            python_libraries.append("cupy")
        profile["python_libraries"] = python_libraries

        # BENCHMARKS
        def score(time_val):
            if time_val < 0.1:
                return 10
            elif time_val < 0.2:
                return 9
            elif time_val < 0.4:
                return 8
            elif time_val < 0.7:
                return 7
            elif time_val < 1.0:
                return 6
            elif time_val < 1.5:
                return 5
            elif time_val < 2.0:
                return 4
            elif time_val < 3.0:
                return 3
            elif time_val < 5.0:
                return 2
            else:
                return 1

        # CPU benchmark
        arr = np.random.rand(10_000_000)
        start = time.time()
        _ = np.sum(arr)
        cpu_time = time.time() - start
        profile["performance_index"] = score(cpu_time)

        # AI benchmark (numpy or cupy)
        ai_time = None
        gpu_ready = False
        if "NVIDIA" in profile["gpu"] and HAS_CUPY:
            try:
                # Szybka weryfikacja dostępności GPU
                _ = cp.zeros(1)
                cp.cuda.Stream.null.synchronize()
                gpu_ready = True
            except Exception as e:
                print("Cupy GPU not available, fallback to CPU:", e)
                gpu_ready = False

        if gpu_ready:
            try:
                arr_gpu = cp.random.rand(2048, 2048)
                cp.cuda.Stream.null.synchronize()
                start = time.time()
                _ = cp.dot(arr_gpu, arr_gpu)
                cp.cuda.Stream.null.synchronize()
                ai_time = time.time() - start
            except Exception as e:
                print("AI GPU benchmark failed, fallback to CPU:", e)
                arr2 = np.random.rand(2048, 2048)
                start = time.time()
                _ = np.dot(arr2, arr2)
                ai_time = time.time() - start
        else:
            arr2 = np.random.rand(2048, 2048)
            start = time.time()
            _ = np.dot(arr2, arr2)
            ai_time = time.time() - start
        profile["ai_index"] = score(ai_time)

        self.profile_ready.emit(profile)


class HardwareProfilerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(400)
        self.profile_data = {}
        self.hardware_path = os.path.join(
            os.path.dirname(__file__), "..", "hardware.json"
        )

        self.init_ui()
        self.load_existing_profile()

        # Rejestracja w TranslationManager
        TranslationManager.register_widget(self)
        self.update_translations()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Tytuł
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Informacje o sprzęcie
        self.cpu_label = QLabel()
        layout.addWidget(self.cpu_label)

        self.ram_label = QLabel()
        layout.addWidget(self.ram_label)

        self.gpu_label = QLabel()
        layout.addWidget(self.gpu_label)

        # Grupa aktualnej konfiguracji
        self.current_group = QGroupBox()
        current_layout = QVBoxLayout(self.current_group)

        self.config_display = QTextEdit()
        self.config_display.setReadOnly(True)
        current_layout.addWidget(self.config_display)

        layout.addWidget(self.current_group)

        # Grupa optymalizacji
        self.optimization_group = QGroupBox()
        opt_layout = QVBoxLayout(self.optimization_group)

        self.optimization_display = QTextEdit()
        self.optimization_display.setReadOnly(True)
        opt_layout.addWidget(self.optimization_display)

        layout.addWidget(self.optimization_group)

        # Przyciski
        button_layout = QHBoxLayout()

        self.scan_btn = QPushButton()
        self.scan_btn.clicked.connect(self.scan_hardware)

        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self.save_profile)

        self.close_btn = QPushButton()
        self.close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.scan_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def scan_hardware(self):
        self.scan_btn.setEnabled(False)
        translator = TranslationManager.get_translator()
        self.scan_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.scanning")
        )

        self.thread = HardwareProfilerThread()
        self.thread.profile_ready.connect(self.on_profile_ready)
        self.thread.start()

    def on_profile_ready(self, profile):
        self.profile_data = profile
        self.display_profile()
        self.scan_btn.setEnabled(True)
        translator = TranslationManager.get_translator()
        self.scan_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.scan_hardware")
        )

    def display_profile(self):
        if not self.profile_data:
            return

        translator = TranslationManager.get_translator()
        config_text = (
            f"{translator.translate('app.dialogs.hardware_profiler.profile.uuid').format(self.profile_data.get('uuid', 'N/A'))}\n"
            f"{translator.translate('app.dialogs.hardware_profiler.profile.system').format(self.profile_data.get('system', 'N/A'))}\n"
            f"{translator.translate('app.dialogs.hardware_profiler.profile.processor').format(self.profile_data.get('processor', 'N/A'))}\n"
            f"{translator.translate('app.dialogs.hardware_profiler.profile.cpu_cores').format(self.profile_data.get('cpu_count', 'N/A'))}\n"
            f"{translator.translate('app.dialogs.hardware_profiler.profile.ram').format(self.profile_data.get('memory_total', 0) // (1024**3))}\n"
            f"{translator.translate('app.dialogs.hardware_profiler.profile.last_update').format(self.profile_data.get('timestamp', 'N/A'))}"
        )

        self.config_display.setText(config_text)

        # Przykładowe optymalizacje na podstawie profilu
        optimizations = self.generate_optimizations()
        self.optimization_display.setText(optimizations)

    def generate_optimizations(self):
        if not self.profile_data:
            translator = TranslationManager.get_translator()
            return translator.translate("app.dialogs.hardware_profiler.profile.no_data")

        opts = []
        cpu_count = self.profile_data.get("cpu_count", 0)
        memory_gb = self.profile_data.get("memory_total", 0) // (1024**3)
        translator = TranslationManager.get_translator()

        if cpu_count >= 8:
            opts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_high"
                )
            )
        elif cpu_count >= 4:
            opts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_medium"
                )
            )
        else:
            opts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_low"
                )
            )

        if memory_gb >= 16:
            opts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_high"
                )
            )
        elif memory_gb >= 8:
            opts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_medium"
                )
            )
        else:
            opts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_low"
                )
            )

        return (
            "\n".join(opts)
            if opts
            else translator.translate(
                "app.dialogs.hardware_profiler.profile.no_optimizations"
            )
        )

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

    def update_translations(self):
        translator = TranslationManager.get_translator()
        self.setWindowTitle(translator.translate("app.dialogs.hardware_profiler.title"))
        self.title_label.setText(
            translator.translate("app.dialogs.hardware_profiler.title")
        )
        self.cpu_label.setText(
            translator.translate("app.dialogs.hardware_profiler.cpu").format(
                self.profile_data.get("processor", "Brak danych")
            )
        )
        self.ram_label.setText(
            translator.translate("app.dialogs.hardware_profiler.profile.ram").format(
                self.profile_data.get("memory_total", 0) // (1024**3)
            )
        )
        self.gpu_label.setText(
            translator.translate("app.dialogs.hardware_profiler.gpu").format(
                self.profile_data.get("gpu", "Brak danych")
            )
        )
        self.current_group.setTitle(
            translator.translate("app.dialogs.hardware_profiler.current_config")
        )
        self.optimization_group.setTitle(
            translator.translate(
                "app.dialogs.hardware_profiler.available_optimizations"
            )
        )
        self.scan_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.scan_hardware")
        )
        self.save_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.save_profile")
        )
        self.close_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.close")
        )
