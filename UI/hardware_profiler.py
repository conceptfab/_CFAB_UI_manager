import json
import logging
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

from utils.exceptions import HardwareProfilingError, handle_error_gracefully
from utils.secure_commands import (
    CommandExecutionError,
    CommandTimeoutError,
    HardwareDetector,
    SecureCommandRunner,
)
from utils.system_info import get_stable_uuid
from utils.translation_manager import TranslationManager

logger = logging.getLogger(__name__)

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

# Funkcja get_stable_uuid została przeniesiona do utils.system_info


class HardwareProfilerThread(QThread):
    profile_ready = pyqtSignal(dict)
    progress_update = pyqtSignal(str)

    def __init__(self, parent=None, hardware_path=None):
        super().__init__(parent)
        self.hardware_detector = HardwareDetector()
        self.hardware_path = hardware_path

    def run(self):
        logger.info("Starting hardware profiling thread")
        try:
            translator = TranslationManager.get_translator()
            self.progress_update.emit(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.collecting_info"
                )
            )
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

            self.progress_update.emit(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.detecting_gpu"
                )
            )
            try:
                profile["gpu"] = self.hardware_detector.get_gpu_info()
                logger.debug(f"GPU detected: {profile['gpu']}")
            except Exception as e:
                logger.error(f"GPU detection failed: {e}")
                profile["gpu"] = translator.translate(
                    "app.dialogs.hardware_profiler.status.gpu_detection_error"
                )

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
                    logger.debug(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.numba_not_installed"
                        )
                    )  # CHANGED
            if "nvidia" in profile["gpu"].lower() and HAS_CUPY:
                python_libraries.append("cupy")
            profile["python_libraries"] = sorted(list(set(python_libraries)))

            self.progress_update.emit(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.running_cpu_benchmark"
                )
            )

            def run_pyperformance():
                try:
                    import pyperformance  # sprawdzamy czy jest zainstalowane

                    logger.info(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.pyperformance_installed"
                        )
                    )  # CHANGED
                except ImportError:
                    logger.warning(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.pyperformance_not_installed"
                        )  # CHANGED
                    )
                    return None, 0.0
                try:
                    import os
                    import sys
                    import time

                    secure_runner = SecureCommandRunner()
                    start = time.time()

                    # Używamy pełnej ścieżki do Pythona
                    python_path = sys.executable
                    logger.info(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.using_python_path"
                        ).format(python_path)
                    )  # CHANGED

                    # Uruchamiamy benchmark
                    cmd = [
                        python_path,
                        "-m",
                        "pyperformance",
                        "run",
                        "--benchmarks",
                        "json_loads",
                    ]
                    logger.info(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.running_command"
                        ).format(" ".join(cmd))
                    )  # CHANGED

                    stdout, stderr = secure_runner.run_command(
                        cmd,
                        timeout=120,
                    )
                    elapsed = time.time() - start

                    logger.info(f"Output pyperformance: {stdout}")
                    if stderr:
                        logger.warning(f"Błędy pyperformance: {stderr}")

                    # Szukamy wyniku w output - nowy format
                    match = re.search(
                        r"Mean \\+-\\s+std dev:\\s+([0-9.]+)\\s+us", stdout
                    )
                    if match:
                        score = float(match.group(1))
                        logger.info(
                            translator.translate(
                                "app.dialogs.hardware_profiler.status.cpu_test_result"
                            ).format(score=score, time=elapsed)
                        )  # CHANGED
                        return score, elapsed
                    else:
                        logger.warning(
                            translator.translate(
                                "app.dialogs.hardware_profiler.status.cpu_test_result_not_found"
                            )
                        )  # CHANGED
                        return None, elapsed

                except (CommandTimeoutError, CommandExecutionError) as e:
                    logger.error(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.pyperformance_run_error"
                        ).format(e=e)
                    )  # CHANGED
                    return None, 0.0
                except Exception as e:
                    logger.error(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.cpu_test_unexpected_error"
                        ).format(e=e)
                    )  # CHANGED
                    return None, 0.0

            perf_score, perf_time = run_pyperformance()
            if perf_score is not None:
                profile["cpu_benchmark"] = {
                    "score": perf_score,
                    "time": perf_time,
                    "benchmark": "json_loads",
                }
                logger.info(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.cpu_test_result_saved"
                    ).format(perf_score)
                )  # CHANGED

                # Bezpośrednie zapisanie do pliku hardware.json
                try:
                    with open(self.hardware_path, "r", encoding="utf-8") as f:
                        hardware_data = json.load(f)

                    hardware_data["cpu_benchmark"] = {
                        "score": perf_score,
                        "time": perf_time,
                        "benchmark": "json_loads",
                    }

                    with open(self.hardware_path, "w", encoding="utf-8") as f:
                        json.dump(hardware_data, f, indent=4, ensure_ascii=False)
                    logger.info(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.cpu_test_results_saved_to_file"
                        )
                    )  # CHANGED
                except Exception as e:
                    logger.error(
                        translator.translate(
                            "app.dialogs.hardware_profiler.status.cpu_test_save_to_file_error"
                        ).format(e=e)
                    )  # CHANGED
            else:
                logger.warning(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.cpu_test_result_not_obtained"
                    )
                )  # CHANGED

            self.progress_update.emit(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.running_ai_benchmark"
                )
            )
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
                logger.error(f"AI benchmark error: {e}")
                profile["ai_benchmark_time"] = None
                profile["ai_benchmark_score"] = None

            self.profile_ready.emit(profile)
        except Exception as e:
            logger.error(f"Error in hardware profiling: {e}")
            self.progress_update.emit(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.profiling_error"
                ).format(e=str(e))
            )  # CHANGED
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

        self.status_label = QLabel(
            TranslationManager.get_translator().translate(
                "app.dialogs.hardware_profiler.status.ready_status"
            )
        )  # CHANGED
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
            translator.translate("app.dialogs.hardware_profiler.scanning")
        )
        self.status_label.setText(
            translator.translate("app.dialogs.hardware_profiler.status.starting")
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
            logger.warning(
                "Profiler thread is already running. This should not happen."
            )
            return

        self.thread = HardwareProfilerThread(self, hardware_path=self.hardware_path)
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
        if (
            TranslationManager.get_translator().translate(
                "app.dialogs.hardware_profiler.status.cpu_benchmark_duration_prefix"
            )
            in message
        ):  # CHANGED
            try:
                time_str = (
                    message.split(
                        TranslationManager.get_translator().translate(
                            "app.dialogs.hardware_profiler.status.cpu_benchmark_duration_prefix"
                        )
                    )[1]
                    .split(
                        TranslationManager.get_translator().translate(
                            "app.dialogs.hardware_profiler.status.cpu_benchmark_duration_suffix"
                        )
                    )[0]
                    .strip()  # CHANGED
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
            translator.translate("app.dialogs.hardware_profiler.scan_hardware")
        )
        if self.profile_data and not self.profile_data.get("error"):
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.scan_completed"
                )
            )
        elif self.profile_data.get("error"):
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.scan_error_detailed"
                )
            )
        else:
            self.status_label.setText(
                translator.translate("app.dialogs.hardware_profiler.status.scan_failed")
            )

    def on_profile_ready(self, profile):
        logger.debug(f"PROFILE RECEIVED IN DIALOG: {json.dumps(profile, indent=2)}")
        translator = TranslationManager.get_translator()
        self.profile_data = profile  # Store the received profile immediately
        if "error" in profile:
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.error_profile"
                ).format(error=profile["error"][:100] + "...")
            )
        else:
            # Status might be set by on_scan_finished or progress_update, only update if still generic
            if self.status_label.text() == translator.translate(
                "app.dialogs.hardware_profiler.status.starting"
            ):
                self.status_label.setText(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.profile_ready"
                    )
                )
            self.save_profile()  # Auto-save on successful scan
        self.display_profile()

    def display_profile(self):
        translator = TranslationManager.get_translator()

        # Update quick info labels first
        self.cpu_label.setText(
            translator.translate("app.dialogs.hardware_profiler.cpu").format(
                self.profile_data.get(
                    "processor",
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.not_available"
                    ),
                )  # CHANGED
            )
        )
        ram_gb = self.profile_data.get("memory_total", 0) // (1024**3)
        self.ram_label.setText(
            translator.translate("app.dialogs.hardware_profiler.ram").format(ram_gb)
        )
        self.gpu_value_label.setText(
            # translator.translate("app.dialogs.hardware_profiler.gpu").format( # Original line, seems like a bug, GPU is already in the key
            #    self.profile_data.get("gpu", translator.translate("app.dialogs.hardware_profiler.status.not_available")) # CHANGED
            # )
            self.profile_data.get(
                "gpu",
                translator.translate(
                    "app.dialogs.hardware_profiler.status.not_available"
                ),
            )  # Corrected line
        )

        if not self.profile_data:
            self.config_display.setText(
                translator.translate("app.dialogs.hardware_profiler.profile.no_data")
            )
            self.optimization_display.setText("")
            self.save_btn.setEnabled(False)
            return

        if "error" in self.profile_data:
            error_details = (
                f"{translator.translate('app.dialogs.hardware_profiler.profile.error_display')}\n"
                f"{self.profile_data.get('error', 'Unknown error')}\n\n"
            )
            if "traceback" in self.profile_data:
                error_details += (
                    f"{translator.translate('app.dialogs.hardware_profiler.profile.traceback')}\\n"
                    f"{self.profile_data.get('traceback', translator.translate('app.dialogs.hardware_profiler.status.no_details_available'))}"  # CHANGED
                )
            self.config_display.setText(error_details)
            self.optimization_display.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.no_optimizations_due_to_error"
                )
            )
            self.save_btn.setEnabled(False)
            return

        config_items = [
            ("uuid", "app.dialogs.hardware_profiler.profile.uuid"),
            ("system", "app.dialogs.hardware_profiler.profile.system"),
            ("processor", "app.dialogs.hardware_profiler.profile.processor"),
            ("cpu_count_physical", "app.dialogs.hardware_profiler.profile.cpu_cores"),
            (
                "memory_total",
                "app.dialogs.hardware_profiler.profile.ram",
                lambda x: round(x / (1024**3), 1),
            ),
            ("gpu", "app.dialogs.hardware_profiler.gpu"),
            ("timestamp", "app.dialogs.hardware_profiler.profile.last_update"),
        ]

        # Dodajemy wyniki testu CPU jeśli są dostępne
        if "cpu_benchmark" in self.profile_data:
            cpu_benchmark = self.profile_data["cpu_benchmark"]
            config_items.append(
                (
                    "cpu_benchmark",
                    "app.dialogs.hardware_profiler.profile.cpu_benchmark",
                    lambda x: f"Score: {x['score']:.2f} (Time: {x['time']:.2f}s)",
                )
            )

        config_text_parts = []
        for key, trans_key, *formatter_and_condition in config_items:
            value = self.profile_data.get(key)
            if value is not None:
                if formatter_and_condition and callable(formatter_and_condition[0]):
                    try:
                        value = formatter_and_condition[0](value)
                    except Exception:
                        value = translator.translate(
                            "app.dialogs.hardware_profiler.status.not_available_in_formatter"
                        )  # CHANGED

                if value is not None and not (
                    isinstance(value, str)
                    and (
                        value.lower()
                        == translator.translate(
                            "app.dialogs.hardware_profiler.status.not_available_short"
                        ).lower()
                        or value
                        == translator.translate(
                            "app.dialogs.hardware_profiler.status.error_short"
                        )
                    )  # CHANGED
                ):
                    try:
                        config_text_parts.append(
                            translator.translate(trans_key).format(value)
                        )
                    except KeyError:
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
                "app.dialogs.hardware_profiler.profile.no_optimizations"
            )

        opt_flags = self.profile_data["optimizations_flags"]
        opt_texts = []

        if opt_flags.get("advanced_multithreading"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_high"
                )
            )
        elif opt_flags.get("multithreading"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_medium"
                )
            )
        else:
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_low"
                )
            )

        if opt_flags.get("high_memory_buffering"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_high"
                )
            )
        elif opt_flags.get("standard_memory_buffering"):
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_medium"
                )
            )
        else:
            opt_texts.append(
                translator.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_low"
                )
            )

        if not opt_texts:
            return translator.translate(
                "app.dialogs.hardware_profiler.profile.no_optimizations"
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
                        "app.dialogs.hardware_profiler.status.profile_loaded"
                    )
                )
                self.save_btn.setEnabled(True)
            except json.JSONDecodeError as e:
                self.status_label.setText(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.profile_corrupt"
                    ).format(error=e)
                )
                self.profile_data = {}
            except Exception as e:
                self.status_label.setText(
                    translator.translate(
                        "app.dialogs.hardware_profiler.status.profile_load_error"
                    ).format(error=e)
                )
                self.profile_data = {}
        else:
            self.status_label.setText(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.no_profile_found"
                )
            )
        self.display_profile()

    def save_profile(self):
        translator = TranslationManager.get_translator()
        if not self.profile_data or "error" in self.profile_data:
            self.status_message_requested.emit(
                translator.translate(
                    "app.dialogs.hardware_profiler.status.save_no_data"
                )
            )
            logger.warning("No valid profile data to save.")
            return

        try:
            with open(self.hardware_path, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=4, ensure_ascii=False)
            msg = translator.translate(
                "app.dialogs.hardware_profiler.status.profile_saved"
            ).format(path=self.hardware_path)
            self.status_message_requested.emit(msg)
            logger.info(f"Profile saved to {self.hardware_path}")
            self.save_btn.setEnabled(True)
        except Exception as e:
            error_msg = translator.translate(
                "app.dialogs.hardware_profiler.status.profile_save_error"
            ).format(error=e)
            logger.error(f"Error saving profile: {e}")
            self.status_message_requested.emit(error_msg)

    def update_translations(self):
        translator = TranslationManager.get_translator()
        self.setWindowTitle(translator.translate("app.dialogs.hardware_profiler.title"))
        self.title_label.setText(
            translator.translate("app.dialogs.hardware_profiler.title")
        )

        self.gpu_label_static.setText(
            translator.translate("app.dialogs.hardware_profiler.gpu")
        )
        self.current_group.setTitle(
            translator.translate("app.dialogs.hardware_profiler.current_config")
        )
        self.optimization_group.setTitle(
            translator.translate(
                "app.dialogs.hardware_profiler.available_optimizations"
            )
        )

        if not (self.thread and self.thread.isRunning()):
            self.scan_btn.setText(
                translator.translate("app.dialogs.hardware_profiler.scan_hardware")
            )
        else:
            self.scan_btn.setText(
                translator.translate("app.dialogs.hardware_profiler.scanning")
            )

        self.save_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.save_profile")
        )
        self.close_btn.setText(
            translator.translate("app.dialogs.hardware_profiler.close")
        )

        self.display_profile()

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            # Consider if a more graceful shutdown is needed (e.g., signal thread to stop)
            # For now, QThread should handle termination if parent dialog is destroyed.
            logger.info("Profiler thread is running. Dialog closing.")
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
        logger.info(f"STATUS UPDATE (from dialog): {message}")

    dialog.status_message_requested.connect(show_status)

    dialog.show()
    sys.exit(app.exec())
