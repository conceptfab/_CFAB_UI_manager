import json
import os
import platform
import re
import subprocess
import tempfile  # For pyperformance JSON output
import time
import uuid

import numpy as np
import psutil
from PyQt6.QtCore import QThread  # Added Qt for Qt.ISODate
from PyQt6.QtCore import QDateTime, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QProgressBar  # Dodajemy progress bar
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


# Assuming this exists and works
# from utils.translation_manager import TranslationManager
# Mocking TranslationManager for standalone execution for now
class MockTranslator:
    def translate(self, key, default_text=None, **kwargs):
        # Simple mock: returns default_text or key, and formats if needed
        text_to_format = default_text if default_text is not None else key
        if kwargs:
            try:
                return text_to_format.format(**kwargs)
            except KeyError:  # Handle cases where not all kwargs are in the string
                return text_to_format.format(
                    **{
                        k: v
                        for k, v in kwargs.items()
                        if "{" + k + "}" in text_to_format
                    }
                )

        return text_to_format


class MockTranslationManager:
    _translator = MockTranslator()
    _widgets = []

    @classmethod
    def get_translator(cls):
        return cls._translator

    @classmethod
    def register_widget(cls, widget):
        if widget not in cls._widgets:
            cls._widgets.append(widget)

    @classmethod
    def unregister_widget(cls, widget):
        if widget in cls._widgets:
            cls._widgets.remove(widget)

    @classmethod
    def update_all_translations(cls):
        for widget in cls._widgets:
            if hasattr(widget, "update_translations"):
                widget.update_translations()


TranslationManager = MockTranslationManager  # Use the mock


try:
    import cupy as cp

    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False

# --- Constants for Benchmarks ---
AI_BENCHMARK_MATRIX_SIZE = 2048
# A smaller, faster subset of pyperformance default benchmarks
PYPERFORMANCE_BENCHMARKS = "bm_ai,bm_json_loads,bm_nbody,bm_regex_dna,bm_spectral_norm"
# For full 'default' set (slower):
# PYPERFORMANCE_BENCHMARKS = "default"


def get_stable_uuid():
    machine_id_str = ""
    # Try to get a unique machine identifier
    if platform.system() == "Windows":
        try:
            # Motherboard serial number is often a good candidate
            result = subprocess.check_output(
                "wmic baseboard get serialnumber",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            serial = result.split("\n")[1].strip()
            if serial and serial != "To be filled by O.E.M.":
                machine_id_str = serial
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            pass  # Fall through
    elif platform.system() == "Linux":
        try:
            # /etc/machine-id is usually available and stable
            with open("/etc/machine-id", "r") as f:
                machine_id_str = f.read().strip()
        except FileNotFoundError:
            pass  # Fall through
    elif platform.system() == "Darwin":  # macOS
        try:
            # IOPlatformUUID is a good candidate on macOS
            result = subprocess.check_output(
                "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', result)
            if match:
                machine_id_str = match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # Fall through

    # Fallback if specific IDs aren't available or if they are empty
    if not machine_id_str:
        machine_id_str = (
            platform.node()
            + platform.machine()
            + (platform.processor() or "unknown_processor")
        )

    # Add MAC address of the first non-loopback interface for more stability if needed,
    # but this can change (e.g., USB NICs) and might be too volatile for some use cases.
    # For this example, the above should be sufficient for "stable enough".

    return str(uuid.uuid5(uuid.NAMESPACE_DNS, machine_id_str))


class HardwareProfilerThread(QThread):
    profile_ready = pyqtSignal(dict)
    progress_update = pyqtSignal(str)

    def run(self):
        print("STARTING BENCHMARK THREAD")
        try:
            self.progress_update.emit("Collecting system information...")
            profile = {
                "uuid": get_stable_uuid(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "memory_total": psutil.virtual_memory().total,
                "timestamp": str(
                    QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
                ),
            }

            self.progress_update.emit("Detecting GPU...")
            if platform.system() == "Windows":
                try:
                    cmd = "wmic path win32_VideoController get name"
                    try:
                        output = subprocess.check_output(
                            cmd,
                            shell=True,
                            text=True,
                            stderr=subprocess.PIPE,
                            encoding="utf-8",
                            errors="ignore",
                        )
                    except UnicodeDecodeError:
                        output = subprocess.check_output(
                            cmd, shell=True, text=False, stderr=subprocess.PIPE
                        ).decode(errors="ignore")

                    print("WMIC GPU output:", output)
                    lines = output.strip().split("\n")
                    gpus = [
                        line.strip()
                        for line in lines
                        if line.strip() and line.strip().lower() != "name"
                    ]
                    profile["gpu"] = ", ".join(gpus) if gpus else "N/A"
                except Exception as e:
                    print(f"GPU detection error (Windows): {e}")
                    profile["gpu"] = "Error detecting GPU"
            elif platform.system() == "Linux":
                gpu_info_list = []
                try:  # Try lspci
                    output_lspci = subprocess.check_output(
                        "lspci -vnn | grep -i VGA -A 12",
                        shell=True,
                        text=True,
                        stderr=subprocess.PIPE,
                    )
                    for line in output_lspci.splitlines():
                        if "VGA compatible controller" in line:
                            match = re.search(
                                r":\s*(.*?)(?:\[|\(|$)", line
                            )  # More robust regex
                            if match:
                                gpu_info_list.append(match.group(1).strip())
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"lspci for GPU failed: {e}")

                try:  # Try nvidia-smi if NVIDIA might be present or lspci failed
                    output_smi = subprocess.check_output(
                        "nvidia-smi --query-gpu=gpu_name --format=csv,noheader",
                        shell=True,
                        text=True,
                        stderr=subprocess.PIPE,
                    )
                    nvidia_gpus = [
                        line.strip() for line in output_smi.splitlines() if line.strip()
                    ]
                    if nvidia_gpus:
                        gpu_info_list = nvidia_gpus  # Prefer nvidia-smi if successful
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass  # nvidia-smi not found or failed, stick with lspci if it worked

                profile["gpu"] = (
                    ", ".join(list(set(gpu_info_list)))
                    if gpu_info_list
                    else "N/A (Linux)"
                )
            elif platform.system() == "Darwin":  # macOS
                try:
                    # system_profiler SPDisplaysDataType
                    output = subprocess.check_output(
                        "system_profiler SPDisplaysDataType",
                        shell=True,
                        text=True,
                        stderr=subprocess.PIPE,
                    )
                    gpus = []
                    current_gpu_name = None
                    for line in output.splitlines():
                        line = line.strip()
                        if "Chipset Model:" in line:
                            current_gpu_name = line.split(":", 1)[1].strip()
                        elif (
                            "VRAM (Total):" in line and current_gpu_name
                        ):  # Confirm it's a display entry
                            gpus.append(current_gpu_name)
                            current_gpu_name = None  # Reset for next GPU
                        elif (
                            "Graphics:" in line and ":" in line
                        ):  # Fallback for some structures
                            gpus.append(
                                line.split(":", 1)[1].strip().split(",")[0]
                            )  # Take first part

                    profile["gpu"] = (
                        ", ".join(list(set(gpus))) if gpus else "N/A (macOS)"
                    )
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"GPU detection error (macOS): {e}")
                    profile["gpu"] = "Error detecting GPU"
            else:
                profile["gpu"] = "N/A (OS not Windows/Linux/macOS)"

            cpu_cores = (
                profile["cpu_count_physical"]
                if profile.get("cpu_count_physical")
                else profile["cpu_count_logical"]
            )
            memory_gb = profile["memory_total"] // (1024**3)
            optimizations = {
                "multithreading": cpu_cores >= 4,
                "advanced_multithreading": cpu_cores >= 8,
                "high_memory_buffering": memory_gb >= 16,
                "standard_memory_buffering": memory_gb >= 8,
            }
            profile["optimizations_flags"] = optimizations

            python_libraries = ["numpy", "psutil", "PyQt6"]
            if optimizations["multithreading"]:
                try:
                    import numba

                    python_libraries.append("numba")
                except ImportError:
                    print("Numba not installed, skipping.")
            if "nvidia" in profile["gpu"].lower() and HAS_CUPY:
                python_libraries.append("cupy")
            profile["python_libraries"] = sorted(list(set(python_libraries)))

            self.progress_update.emit("Running CPU benchmark (pyperformance)...")

            def run_pyperformance():
                try:
                    import pyperformance  # sprawdzamy czy jest zainstalowane
                except ImportError:
                    print("pyperformance nie jest zainstalowane! Pomijam test CPU.")
                    return None, 0.0
                try:
                    import time

                    start = time.time()
                    # Uruchamiamy tylko jeden szybki benchmark
                    result = subprocess.run(
                        [
                            "python",
                            "-m",
                            "pyperformance",
                            "run",
                            "--benchmarks",
                            "json_loads",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    elapsed = time.time() - start
                    output = result.stdout
                    match = re.search(r"Geometric mean:\s+([0-9.]+)", output)
                    if match:
                        score = float(match.group(1))
                        return score, elapsed
                    else:
                        print(
                            "Nie znaleziono wyniku Geometric mean w output pyperformance."
                        )
                        return None, elapsed
                except Exception as e:
                    print("Błąd uruchamiania pyperformance:", e)
                    return None, 0.0

            perf_score, perf_time = run_pyperformance()
            if perf_score is not None:
                profile["cpu_benchmark_score"] = perf_score
                profile["cpu_benchmark_time"] = perf_time

            self.progress_update.emit("Running AI benchmark...")
            try:
                import time

                start = time.time()
                # Matrix multiplication benchmark
                a = np.random.rand(AI_BENCHMARK_MATRIX_SIZE, AI_BENCHMARK_MATRIX_SIZE)
                b = np.random.rand(AI_BENCHMARK_MATRIX_SIZE, AI_BENCHMARK_MATRIX_SIZE)
                c = np.matmul(a, b)
                elapsed = time.time() - start
                profile["ai_benchmark_time"] = elapsed
                profile["ai_benchmark_score"] = calculate_ai_score(elapsed)
            except Exception as e:
                print(f"AI benchmark error: {e}")
                profile["ai_benchmark_time"] = None
                profile["ai_benchmark_score"] = None

            self.profile_ready.emit(profile)
        except Exception as e:
            print(f"Error in hardware profiling: {e}")
            self.progress_update.emit(f"Error: {str(e)}")
            self.profile_ready.emit({})


class HardwareProfilerDialog(QDialog):
    status_message_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(550)
        self.profile_data = {}
        self.start_time = None  # Dodajemy zmienną do śledzenia czasu
        self.timer = None  # Timer do aktualizacji licznika
        # IMPORTANT: Replace ".yourappname" with your actual application's name
        # This creates a directory in the user's home folder for the config.
        app_name_for_config = ".my_hardware_profiler_app"  # CHANGE THIS
        self.config_dir = os.path.join(os.path.expanduser("~"), app_name_for_config)
        os.makedirs(self.config_dir, exist_ok=True)
        self.hardware_path = os.path.abspath("hardware.json")

        self.thread = None

        self.init_ui()
        self.load_existing_profile()
        TranslationManager.register_widget(self)  # Register with the (mocked) manager
        self.update_translations()
        # Ustawiamy wysokość grupy optymalizacji na 30% wysokości okna
        self.update_optimization_group_height()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 8)  # Zwiększam margines dolny do 8px

        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px;"
        )
        layout.addWidget(self.title_label)

        info_layout_1 = QHBoxLayout()
        self.cpu_label = QLabel()
        self.ram_label = QLabel()
        info_layout_1.addWidget(self.cpu_label)
        info_layout_1.addStretch()
        info_layout_1.addWidget(self.ram_label)
        layout.addLayout(info_layout_1)

        gpu_layout = QHBoxLayout()
        self.gpu_label_static = QLabel()  # Static "GPU:" text
        self.gpu_value_label = QLabel()  # Dynamic GPU value, allows wrapping
        self.gpu_value_label.setWordWrap(True)
        gpu_layout.addWidget(self.gpu_label_static)
        gpu_layout.addWidget(self.gpu_value_label, 1)  # Give it stretch factor
        layout.addLayout(gpu_layout)

        self.current_group = QGroupBox()
        self.current_group.setStyleSheet(
            """
            QGroupBox { 
                border: none; 
                margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
        """
        )
        current_layout = QVBoxLayout(self.current_group)
        self.config_display = QTextEdit()
        self.config_display.setReadOnly(True)
        self.config_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.config_display.setStyleSheet(
            "QTextEdit { border: none; background: transparent; padding: 0px; margin: 0px; padding-right: 0px; }"
        )
        self.config_display.setViewportMargins(0, 0, 0, 0)
        current_layout.setContentsMargins(0, 0, 0, 0)
        current_layout.setSpacing(0)
        current_layout.addWidget(self.config_display)
        layout.addWidget(self.current_group)

        self.optimization_group = QGroupBox()
        self.optimization_group.setStyleSheet(
            """
            QGroupBox { 
                border: none; 
                margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
        """
        )
        opt_layout = QVBoxLayout(self.optimization_group)
        self.optimization_display = QTextEdit()
        self.optimization_display.setReadOnly(True)
        self.optimization_display.setStyleSheet(
            "QTextEdit { border: none; background: transparent; padding: 0px; margin: 0px; padding-right: 0px; }"
        )
        self.optimization_display.setViewportMargins(0, 0, 0, 0)
        opt_layout.setContentsMargins(0, 0, 0, 0)
        opt_layout.setSpacing(0)
        opt_layout.addWidget(self.optimization_display)
        layout.addWidget(self.optimization_group)

        self.status_label = QLabel("Ready.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Progress bar przeniesiony tutaj, tuż nad przyciskami
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m sekund")
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                width: 10px;
                margin: 0.5px;
            }
        """
        )
        layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        self.scan_btn = QPushButton()
        self.scan_btn.clicked.connect(self.scan_hardware)
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self.save_profile)
        self.save_btn.setEnabled(False)
        self.close_btn = QPushButton()
        self.close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.scan_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)

    def scan_hardware(self):
        translator = TranslationManager.get_translator()
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.scanning", "Scanning..."
            )
        )
        self.status_label.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.status.starting", "Starting scan..."
            )
        )
        self.save_btn.setEnabled(False)
        self.profile_data = {}  # Clear old data before scan
        self.display_profile()  # Update UI to reflect clearing

        # Reset i start progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(30)  # Zakładamy max 30 sekund na test
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)  # Update co sekundę

        if self.thread and self.thread.isRunning():
            print("Profiler thread is already running. This should not happen.")
            return

        self.thread = HardwareProfilerThread(self)
        self.thread.profile_ready.connect(self.on_profile_ready)
        self.thread.progress_update.connect(self.on_progress_update)
        self.thread.finished.connect(self.on_scan_finished)
        self.thread.start()

    def update_progress(self):
        current = self.progress_bar.value()
        if current < self.progress_bar.maximum():
            self.progress_bar.setValue(current + 1)
        else:
            self.timer.stop()

    def on_progress_update(self, message):
        self.status_label.setText(message)
        # Aktualizujemy licznik czasu
        if "CPU benchmark trwał:" in message:
            try:
                time_str = (
                    message.split("CPU benchmark trwał:")[1].split("sekundy")[0].strip()
                )
                self.progress_bar.setMaximum(int(float(time_str)))
            except:
                pass

    def on_scan_finished(self):
        if self.timer:
            self.timer.stop()
        self.progress_bar.setValue(self.progress_bar.maximum())  # Ustaw na 100%
        translator = TranslationManager.get_translator()
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.scan_hardware", "Scan Hardware"
            )
        )
        if self.profile_data and not self.profile_data.get("error"):
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.scan_completed",
                    "Scan completed.",
                )
            )
        elif self.profile_data.get("error"):
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.scan_error_detailed",
                    "Scan finished with errors. Check details.",
                )
            )
        else:
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.scan_failed",
                    "Scan did not produce a profile.",
                )
            )

    def on_profile_ready(self, profile):
        print("PROFILE RECEIVED IN DIALOG:", json.dumps(profile, indent=2))
        translator = TranslationManager.get_translator()
        self.profile_data = profile  # Store the received profile immediately
        if "error" in profile:
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.error_profile",
                    "Error during profiling: {error}",
                ).format(error=profile["error"][:100] + "...")
            )
        else:
            # Status might be set by on_scan_finished or progress_update, only update if still generic
            if self.status_label.text() == translator.translate(
                "app.dialogs.hardware_profiler.status.starting", "Starting scan..."
            ):
                self.status_label.setText(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.profile_ready",
                        "Profile ready.",
                    )
                )
            self.save_profile()  # Auto-save on successful scan
        self.display_profile()

    def display_profile(self):
        translator = TranslationManager.get_translator()

        # Update quick info labels first
        self.cpu_label.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.cpu", "CPU: {cpu}"
            ).format(cpu=self.profile_data.get("processor", "N/A"))
        )
        ram_gb = self.profile_data.get("memory_total", 0) // (1024**3)
        self.ram_label.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.ram_gb", "RAM: {ram} GB"
            ).format(ram=ram_gb)
        )
        self.gpu_value_label.setText(self.profile_data.get("gpu", "N/A"))

        if not self.profile_data:
            self.config_display.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.no_data",
                    "No profile data available. Please scan hardware.",
                )
            )
            self.optimization_display.setText("")
            self.save_btn.setEnabled(False)
            return

        if "error" in self.profile_data:
            error_details = (
                f"{translator.translate('app.dialogs.hardware_profiler.profile.error_display', 'Error during profiling:')}\n"
                f"{self.profile_data.get('error', 'Unknown error')}\n\n"
            )
            if "traceback" in self.profile_data:
                error_details += (
                    f"{translator.translate('app.dialogs.hardware_profiler.profile.traceback', 'Details (Traceback):')}\n"
                    f"{self.profile_data.get('traceback', 'No details available')}"
                )
            self.config_display.setText(error_details)
            self.optimization_display.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.no_optimizations_due_to_error",
                    "Optimizations cannot be determined due to error.",
                )
            )
            self.save_btn.setEnabled(False)
            return

        config_items = [
            ("uuid", "app.dialogs.hardware_profiler.profile.uuid", "UUID: {value}"),
            (
                "system",
                "app.dialogs.hardware_profiler.profile.system",
                "System: {value}",
            ),
            (
                "release",
                "app.dialogs.hardware_profiler.profile.release",
                "Release: {value}",
            ),
            (
                "version",
                "app.dialogs.hardware_profiler.profile.version",
                "OS Version: {value}",
            ),
            (
                "machine",
                "app.dialogs.hardware_profiler.profile.architecture",
                "Architecture: {value}",
            ),
            (
                "processor",
                "app.dialogs.hardware_profiler.profile.processor_info",
                "Processor Info: {value}",
            ),
            (
                "cpu_count_physical",
                "app.dialogs.hardware_profiler.profile.cpu_cores_physical",
                "CPU Cores (Physical): {value}",
            ),
            (
                "cpu_count_logical",
                "app.dialogs.hardware_profiler.profile.cpu_cores_logical",
                "CPU Cores (Logical): {value}",
            ),
            (
                "memory_total",
                "app.dialogs.hardware_profiler.profile.ram_exact_gb",
                "Total RAM: {value:.2f} GB",
                lambda x: x / (1024**3),
            ),
            (
                "gpu",
                "app.dialogs.hardware_profiler.profile.gpu_detected",
                "Detected GPU(s): {value}",
            ),
            (
                "timestamp",
                "app.dialogs.hardware_profiler.profile.last_update",
                "Profile Timestamp: {value}",
            ),
            (
                "cpu_benchmark_score",
                "app.dialogs.hardware_profiler.profile.perf_score",
                "CPU Benchmark (pyperformance, lower is better): {value}",
            ),
            (
                "cpu_benchmark_time",
                "app.dialogs.hardware_profiler.profile.perf_time",
                "CPU Benchmark Time: {value} seconds",
            ),
            (
                "ai_benchmark_score",
                "app.dialogs.hardware_profiler.profile.ai_index",
                "AI Index (0-10, higher is better): {value}",
            ),
            (
                "ai_benchmark_time",
                "app.dialogs.hardware_profiler.profile.ai_time",
                "AI Benchmark Time: {value} s",
            ),
            (
                "ai_benchmark_device",
                "app.dialogs.hardware_profiler.profile.ai_device",
                "AI Benchmark Device: {value}",
            ),
            (
                "ai_benchmark_error",
                "app.dialogs.hardware_profiler.profile.ai_error",
                "AI Benchmark Note: {value}",
            ),
            (
                "python_libraries",
                "app.dialogs.hardware_profiler.profile.python_libs",
                "Key Python Libraries: {value}",
                lambda x: ", ".join(x),
            ),
        ]

        config_text_parts = []
        for key, trans_key, default_fmt, *formatter_and_condition in config_items:
            value = self.profile_data.get(key)
            condition = (
                formatter_and_condition[1]
                if len(formatter_and_condition) > 1
                else lambda v: v is not None
            )  # Default condition: value exists

            if condition(value):  # Check condition before processing
                if formatter_and_condition and callable(formatter_and_condition[0]):
                    try:
                        value = formatter_and_condition[0](value)
                    except Exception:  # If formatter fails with None/unexpected type
                        value = "N/A in formatter"

                if value is not None and not (
                    isinstance(value, str)
                    and (value.lower() == "n/a" or value == "Error")
                ):  # Don't add if value ended up as "N/A" or "Error"
                    fmt_str = translator.translate(trans_key, default_fmt)
                    try:
                        config_text_parts.append(fmt_str.format(value=value))
                    except KeyError:  # If {value} is not in fmt_str
                        config_text_parts.append(
                            f"{trans_key.split('.')[-1].replace('_', ' ').title()}: {value}"
                        )

        self.config_display.setText("\n".join(config_text_parts))
        self.optimization_display.setText(self.generate_optimizations_text())
        self.save_btn.setEnabled(True)

    def generate_optimizations_text(self):
        translator = TranslationManager.get_translator()
        if (
            not self.profile_data
            or "optimizations_flags" not in self.profile_data
            or "error" in self.profile_data
        ):
            return translator.translate(
                "app.dialogs.hardware_profiler.profile.no_data_for_optimizations",
                "Scan hardware to see optimization suggestions.",
            )

        opt_flags = self.profile_data["optimizations_flags"]
        opt_texts = []

        if opt_flags.get("advanced_multithreading"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.advanced_multithreading",
                    "• Consider enabling Advanced Multithreading (8+ physical cores detected).",
                )
            )
        elif opt_flags.get("multithreading"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.multithreading",
                    "• Standard Multithreading recommended (4-7 physical cores detected).",
                )
            )
        else:
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.multithreading_limited",
                    "• Multithreading capabilities may be limited (<4 physical cores detected).",
                )
            )

        if opt_flags.get("high_memory_buffering"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.high_memory",
                    "• High Memory Buffering strategies can be used (16GB+ RAM).",
                )
            )
        elif opt_flags.get("standard_memory_buffering"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.standard_memory",
                    "• Standard Memory Buffering is suitable (8-15GB RAM).",
                )
            )
        else:
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.low_memory",
                    "• Optimize for lower memory usage (<8GB RAM).",
                )
            )

        gpu_name = self.profile_data.get("gpu", "").lower()
        if "nvidia" in gpu_name:
            if HAS_CUPY:
                opt_texts.append(
                    translator.translate(
                        "app.dialogs.hardware_profiler.optimizations.cuda_available",
                        "• NVIDIA GPU with CuPy detected: CUDA acceleration available for compatible tasks.",
                    )
                )
            else:
                opt_texts.append(
                    translator.translate(
                        "app.dialogs.hardware_profiler.optimizations.cuda_install_cupy",
                        "• NVIDIA GPU detected: Install CuPy for potential CUDA acceleration.",
                    )
                )
        elif "amd" in gpu_name or "radeon" in gpu_name:
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.amd_gpu",
                    "• AMD GPU detected. Consider ROCm/HIP for GPU acceleration if supported by your tasks and libraries.",
                )
            )
        elif "intel" in gpu_name and ("iris" in gpu_name or "arc" in gpu_name):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.optimizations.intel_gpu",
                    "• Intel GPU detected. Consider oneAPI / OpenCL for GPU acceleration if supported.",
                )
            )

        if not opt_texts:
            return translator.translate(
                "app.dialogs.hardware_profiler.profile.no_specific_optimizations",
                "No specific optimization flags triggered based on current hardware profile.",
            )
        return "\n".join(opt_texts)

    def load_existing_profile(self):
        translator = TranslationManager.get_translator()
        if os.path.exists(self.hardware_path):
            try:
                with open(self.hardware_path, "r", encoding="utf-8") as f:
                    self.profile_data = json.load(f)
                self.status_label.setText(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.profile_loaded",
                        "Existing profile loaded.",
                    )
                )
                self.save_btn.setEnabled(True)
            except json.JSONDecodeError as e:
                self.status_label.setText(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.profile_corrupt",
                        "Error loading profile (corrupted?): {error}",
                    ).format(error=e)
                )
                self.profile_data = {}
            except Exception as e:
                self.status_label.setText(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.profile_load_error",
                        "Error loading profile: {error}",
                    ).format(error=e)
                )
                self.profile_data = {}
        else:
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.no_profile_found",
                    "No existing profile found. Scan hardware to create one.",
                )
            )
        self.display_profile()

    def save_profile(self):
        translator = TranslationManager.get_translator()
        if not self.profile_data or "error" in self.profile_data:
            self.status_message_requested.emit(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.save_no_data",
                    "No valid profile data to save.",
                )
            )
            print("No valid profile data to save.")
            return

        try:
            with open(self.hardware_path, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=4, ensure_ascii=False)
            msg = translator.translate(
                "app.dialogs.hardware_profiler.status.profile_saved",
                "Hardware profile saved to: {path}",
            ).format(path=self.hardware_path)
            self.status_message_requested.emit(msg)
            print(f"Profile saved to {self.hardware_path}")
            self.save_btn.setEnabled(True)
        except Exception as e:
            error_msg = translator.translate(
                "app.dialogs.hardware_profiler.status.profile_save_error",
                "Error saving profile: {error}",
            ).format(error=e)
            print(f"Error saving profile: {e}")
            self.status_message_requested.emit(error_msg)

    def update_translations(self):
        translator = TranslationManager.get_translator()
        self.setWindowTitle(
            translator.translate(
                "app.dialogs.hardware_profiler.title", "Hardware Profiler & Optimizer"
            )
        )
        self.title_label.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.title", "Hardware Profiler & Optimizer"
            )
        )

        self.gpu_label_static.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.gpu_static_label", "GPU(s):"
            )
        )
        self.current_group.setTitle(
            translator.translate(
                "app.dialogs.hardware_profiler.current_config",
                "Current Hardware Configuration",
            )
        )
        self.optimization_group.setTitle(
            translator.translate(
                "app.dialogs.hardware_profiler.available_optimizations",
                "Suggested Optimizations & Capabilities",
            )
        )

        if not (self.thread and self.thread.isRunning()):
            self.scan_btn.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.scan_hardware", "Scan Hardware"
                )
            )
        else:
            self.scan_btn.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.scanning", "Scanning..."
                )
            )

        self.save_btn.setText(
            translator.translate(
                "app.dialogs.hardware_profiler.save_profile", "Save Profile"
            )
        )
        self.close_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.close", "Close")
        )

        self.display_profile()  # Refresh displayed data with new translations

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            # Consider if a more graceful shutdown is needed (e.g., signal thread to stop)
            # For now, QThread should handle termination if parent dialog is destroyed.
            print("Profiler thread is running. Dialog closing.")
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_optimization_group_height()

    def update_optimization_group_height(self):
        self.optimization_group.setMaximumHeight(int(self.height() * 0.3))


def calculate_ai_score(time_val_s):
    if time_val_s is None:
        return 0
    # Scores adjusted for typical performance; higher is better.
    if time_val_s < 0.05:
        return 10  # High-end GPU
    elif time_val_s < 0.1:
        return 9
    elif time_val_s < 0.2:
        return 8
    elif time_val_s < 0.4:
        return 7  # Mid-range GPU / Very Fast CPU
    elif time_val_s < 0.7:
        return 6
    elif time_val_s < 1.0:
        return 5  # Decent CPU
    elif time_val_s < 1.5:
        return 4
    elif time_val_s < 2.0:
        return 3
    elif time_val_s < 3.0:
        return 2
    elif time_val_s < 5.0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    # Ensure Numba doesn't conflict with Qt event loop if it uses multiprocessing
    # os.environ['NUMBA_DISABLE_INTEL_SVML'] = '1' # If issues arise

    app = QApplication(sys.argv)
    dialog = HardwareProfilerDialog()

    # To see status messages from the dialog (if it were part of a main window)
    def show_status(message):
        print(f"STATUS UPDATE (from dialog): {message}")

    dialog.status_message_requested.connect(show_status)

    dialog.show()
    sys.exit(app.exec())
