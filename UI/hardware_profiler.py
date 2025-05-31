import json
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile  # For pyperformance JSON output
import time
import traceback  # Dodano import traceback
import uuid
import warnings

try:
    import cupy
except ImportError:
    cupy = None  # Define cupy as None if it's not installed

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

warnings.filterwarnings("ignore", category=UserWarning, module="cupy")

# Domyślnie ustawiamy HAS_CUPY na False i cp na None
HAS_CUPY = False
cp = None

try:
    # Globalny filtr ostrzeżeń ustawiony w main_app.py powinien obsłużyć
    # ostrzeżenie UserWarning z cupy._environment dotyczące wielu pakietów.
    # Usuwamy lokalne `import warnings` i `with warnings.catch_warnings()`
    # oraz lokalne `warnings.filterwarnings` dla tego importu.
    import cupy as cp

    HAS_CUPY = True
    logger.info("CuPy imported successfully.")
except ImportError:
    logger.info("CuPy not found or import failed. HAS_CUPY set to False.")
    # HAS_CUPY jest już False, cp jest już None z inicjalizacji powyżej.
except Exception as e:
    # Złap inne nieoczekiwane błędy podczas próby importu CuPy
    logger.error(f"An unexpected error occurred while trying to import cupy: {e}")
    # HAS_CUPY jest już False, cp jest już None z inicjalizacji powyżej.

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

    def run_ai_benchmark(self):
        """Runs a simple matrix multiplication benchmark using CuPy.

        Returns:
            float: Time in seconds, or None if benchmark couldn't run.
        """
        global cp, HAS_CUPY  # Zapewniamy dostęp do tych zmiennych

        if not HAS_CUPY or cp is None:
            logger.warning("CuPy is not available for AI benchmark")
            return None

        try:
            # Użyj mniejszej macierzy dla bezpieczeństwa
            size = AI_BENCHMARK_MATRIX_SIZE
            logger.info(f"Creating {size}x{size} random matrices for GPU benchmark...")

            # Tworzenie macierzy na GPU
            a_cpu = np.random.rand(size, size).astype(np.float32)
            b_cpu = np.random.rand(size, size).astype(np.float32)

            # Przenieś dane na GPU
            a_gpu = cp.asarray(a_cpu)
            b_gpu = cp.asarray(b_cpu)

            # Synchronizacja przed pomiarem czasu
            cp.cuda.Stream.null.synchronize()

            # Właściwy pomiar
            logger.info("Starting GPU benchmark timing...")
            start_time = time.time()

            # Wykonaj mnożenie macierzy
            c_gpu = cp.dot(a_gpu, b_gpu)

            # Upewnij się, że wszystkie operacje GPU się zakończyły
            cp.cuda.Stream.null.synchronize()

            duration = time.time() - start_time

            # Zwolnij pamięć GPU
            del a_gpu, b_gpu, c_gpu
            mempool = cp.get_default_memory_pool()
            mempool.free_all_blocks()

            logger.info(f"GPU benchmark completed in {duration:.4f} seconds")
            return duration

        except Exception as e:
            logger.error(f"Error during GPU benchmark: {e}", exc_info=True)
            return None

    def run(self):
        logger.info("Starting hardware profiling thread")
        try:
            self.progress_update.emit(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.collecting_info"
                )
            )
            # Tworzenie znacznika czasu w formacie ISO
            current_time = QDateTime.currentDateTime()
            iso_time_str = current_time.toString(Qt.DateFormat.ISODate)

            # Utwórz profil sprzętowy
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
                "timestamp": iso_time_str,  # Upraszczamy przypisanie bez zbędnego rzutowania na string
            }

            # Dodatkowe logowanie timestamp dla debugowania
            logger.debug(
                f"Timestamp utworzony: '{iso_time_str}', typ: {type(iso_time_str)}"
            )

            self.progress_update.emit(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.detecting_gpu"
                )
            )
            try:
                profile["gpu"] = self.hardware_detector.get_gpu_info()
                logger.debug(f"GPU detected: {profile['gpu']}")
            except Exception as e:
                logger.error(f"GPU detection failed: {e}")
                profile["gpu"] = TranslationManager.translate(
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
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.numba_not_installed"
                        )
                    )  # CHANGED
            if "nvidia" in profile["gpu"].lower() and HAS_CUPY:
                python_libraries.append("cupy")
            profile["python_libraries"] = sorted(list(set(python_libraries)))

            # Definicja run_pyperformance musi być tutaj, aby była w zasięgu
            def run_pyperformance():
                try:
                    import pyperformance  # sprawdzamy czy jest zainstalowane

                    logger.info(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.pyperformance_installed"
                        )
                    )  # CHANGED
                except ImportError:
                    logger.warning(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.pyperformance_not_installed"
                        )  # CHANGED
                    )
                    return None, 0.0

                import sys
                import time

                secure_runner = SecureCommandRunner()
                start_time_perf = time.time()

                python_path = sys.executable
                logger.info(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.using_python_path"
                    ).format(python_path)
                )

                temp_json_path = None
                try:
                    temp_dir = tempfile.gettempdir()
                    temp_filename = f"pyperformance_output_{uuid.uuid4().hex}.json"
                    temp_json_path = os.path.join(temp_dir, temp_filename)

                    if os.path.exists(temp_json_path):
                        logger.warning(
                            f"Generated temporary path {temp_json_path} already exists. Attempting to remove."
                        )
                        try:
                            os.remove(temp_json_path)
                            logger.info(
                                f"Successfully removed pre-existing temp file: {temp_json_path}"
                            )
                        except OSError as e_remove:
                            logger.error(
                                f"Failed to remove pre-existing temp file {temp_json_path}: {e_remove}. Pyperformance will likely fail."
                            )

                    logger.info(
                        f"Pyperformance will output to temporary file: {temp_json_path}"
                    )

                    cmd = [
                        python_path,
                        "-m",
                        "pyperformance",
                        "run",
                        "--benchmarks",
                        "json_loads",
                        "-o",
                        temp_json_path,
                    ]
                    logger.info(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.running_command"
                        ).format(" ".join(cmd))
                    )

                    stdout, stderr = secure_runner.run_command(cmd, timeout=180)
                    elapsed_perf = time.time() - start_time_perf

                    if stdout:
                        logger.info(f"Output pyperformance (stdout): {stdout.strip()}")
                    if stderr:
                        logger.info(f"Output pyperformance (stderr): {stderr.strip()}")

                    score = None
                    try:
                        if not os.path.exists(temp_json_path):
                            logger.error(
                                f"Pyperformance output file {temp_json_path} was not created."
                            )
                            if stdout:
                                logger.error(
                                    f"pyperformance stdout (file not created): {stdout.strip()}"
                                )
                            if stderr:
                                logger.error(
                                    f"pyperformance stderr (file not created): {stderr.strip()}"
                                )
                            raise FileNotFoundError(
                                f"Pyperformance output file not found: {temp_json_path}"
                            )

                        with open(temp_json_path, "r", encoding="utf-8") as f:
                            perf_data = json.load(f)

                        if perf_data.get("metadata", {}).get("name") == "json_loads":
                            logger.info("Found json_loads benchmark in main metadata.")
                            all_run_values = []
                            if perf_data.get("benchmarks"):
                                for bench_run_detail in perf_data["benchmarks"]:
                                    if bench_run_detail.get("runs"):
                                        for run_item in bench_run_detail["runs"]:
                                            if (
                                                isinstance(run_item, dict)
                                                and "values" in run_item
                                            ):
                                                all_run_values.extend(
                                                    run_item["values"]
                                                )

                            if all_run_values:
                                mean_time_seconds = sum(all_run_values) / len(
                                    all_run_values
                                )
                                score = mean_time_seconds * 1_000_000
                                logger.info(
                                    TranslationManager.translate(
                                        "app.dialogs.hardware_profiler.status.cpu_test_result"
                                    ).format(score=score, time=elapsed_perf)
                                )
                            else:
                                logger.warning(
                                    "json_loads benchmark found, but no 'values' array in any run or runs are empty."
                                    + f" Data: {json.dumps(perf_data, indent=2)}"
                                )

                        elif perf_data.get("benchmarks"):
                            logger.info("Checking 'benchmarks' array for json_loads.")
                            for bench_result in perf_data["benchmarks"]:
                                is_json_loads_in_array = (
                                    bench_result.get("name") == "json_loads"
                                    or bench_result.get("metadata", {}).get("name")
                                    == "json_loads"
                                )
                                if is_json_loads_in_array:
                                    logger.info(
                                        f"Found json_loads in benchmarks array: {bench_result.get('metadata', {}).get('name')}"
                                    )
                                    all_run_values_item = []
                                    if bench_result.get("runs"):
                                        for run_item in bench_result["runs"]:
                                            if (
                                                isinstance(run_item, dict)
                                                and "values" in run_item
                                            ):
                                                all_run_values_item.extend(
                                                    run_item["values"]
                                                )

                                    if all_run_values_item:
                                        mean_time_seconds = sum(
                                            all_run_values_item
                                        ) / len(all_run_values_item)
                                        score = mean_time_seconds * 1_000_000
                                        logger.info(
                                            TranslationManager.translate(
                                                "app.dialogs.hardware_profiler.status.cpu_test_result"
                                            ).format(score=score, time=elapsed_perf)
                                        )
                                        break
                                    else:
                                        logger.warning(
                                            f"json_loads benchmark found in array (name: {bench_result.get('metadata', {}).get('name')}), but no 'values' in runs."
                                        )
                                else:
                                    logger.debug(
                                        f"Skipping benchmark item, not json_loads: {bench_result.get('metadata', {}).get('name')}"
                                    )

                        if score is None:
                            logger.warning(
                                TranslationManager.translate(
                                    "app.dialogs.hardware_profiler.status.cpu_test_result_not_found_json"
                                )
                                + f" in {temp_json_path}. Data: {json.dumps(perf_data, indent=2)}"
                            )

                    except FileNotFoundError:
                        logger.error(
                            f"Pyperformance output file not found: {temp_json_path}"
                        )
                        if stdout:
                            logger.error(f"pyperformance stdout was: {stdout}")
                        if stderr:
                            logger.error(f"pyperformance stderr was: {stderr}")
                    except json.JSONDecodeError:
                        logger.error(
                            f"Failed to decode JSON from pyperformance output: {temp_json_path}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing pyperformance JSON output {temp_json_path}: {e}"
                        )

                    return score, elapsed_perf

                except (CommandTimeoutError, CommandExecutionError) as e:
                    logger.error(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.pyperformance_run_error"
                        ).format(e=str(e))
                    )
                    if hasattr(e, "stdout") and e.stdout:
                        logger.error(f"pyperformance stdout on error: {e.stdout}")
                    if hasattr(e, "stderr") and e.stderr:
                        logger.error(f"pyperformance stderr on error: {e.stderr}")
                    return None, 0.0
                except Exception as e:
                    logger.error(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.cpu_test_unexpected_error"
                        ).format(e=e)
                    )
                    return None, 0.0
                finally:
                    if temp_json_path and os.path.exists(temp_json_path):
                        try:
                            os.remove(temp_json_path)
                            logger.info(
                                f"Successfully removed temp file: {temp_json_path}"
                            )
                        except OSError as e_remove_final:
                            logger.warning(
                                f"Failed to remove temp file {temp_json_path} in finally block: {e_remove_final}"
                            )

            # Koniec definicji run_pyperformance

            self.progress_update.emit(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.running_cpu_benchmark"
                )
            )
            logger.info("Rozpoczęcie testu CPU (pyperformance)...")
            try:
                cpu_score, cpu_time = run_pyperformance()
                profile["cpu_benchmark"] = {"score": cpu_score, "time_s": cpu_time}
                logger.info(
                    f"Test CPU (pyperformance) zakończony. Wynik: {cpu_score}, Czas: {cpu_time:.2f}s"
                )
                self.progress_update.emit(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.cpu_benchmark_duration_prefix"
                    )
                    + f" {cpu_time:.2f}s"
                )
            except Exception as e_cpu_bench:
                logger.error(
                    f"Błąd podczas testu CPU (pyperformance): {e_cpu_bench}",
                    exc_info=True,
                )
                profile["cpu_benchmark"] = {"error": str(e_cpu_bench)}
                self.progress_update.emit(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.cpu_benchmark_error"
                    )
                )

            # AI/GPU Benchmark (CuPy)
            if HAS_CUPY and cp:
                self.progress_update.emit(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.running_gpu_benchmark"
                    )
                )
                logger.info("Rozpoczęcie testu AI/GPU (CuPy)...")
                try:
                    ai_time_s = self.run_ai_benchmark()
                    profile["ai_benchmark_cupy"] = {"time_s": ai_time_s}
                    logger.info(
                        f"Test AI/GPU (CuPy) zakończony. Czas: {ai_time_s:.4f}s"
                    )
                    self.progress_update.emit(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.gpu_benchmark_duration_prefix"
                        )
                        + f" {ai_time_s:.4f}s"
                    )
                except Exception as e_gpu_bench:
                    logger.error(
                        f"Błąd podczas testu AI/GPU (CuPy): {e_gpu_bench}",
                        exc_info=True,
                    )
                    profile["ai_benchmark_cupy"] = {"error": str(e_gpu_bench)}
                    self.progress_update.emit(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.gpu_benchmark_error"
                        )
                    )
            else:
                logger.info("Pominięto test AI/GPU (CuPy) - CuPy niedostępne.")
                profile["ai_benchmark_cupy"] = {
                    "status": TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.cupy_not_available"
                    )
                }

            self.progress_update.emit(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.profiling_complete"
                )
            )
            self.profile_ready.emit(profile)
            logger.info("Hardware profiling finished successfully.")

        except Exception as e:
            logger.error(f"Hardware profiling failed: {e}", exc_info=True)
            error_profile = {
                "error": str(e),
                "details": traceback.format_exc(),
            }  # traceback jest teraz zdefiniowany
            self.profile_ready.emit(error_profile)
            self.progress_update.emit(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.profiling_error"
                )
            )

    def optimize_memory_usage(self):
        """Optimize memory usage during profiling"""
        # Add specific memory optimization techniques here
        # For example, if using pandas DataFrames:
        # self.data_frame = self.data_frame.astype('float32') # Or other smaller types
        # Or trigger garbage collection more aggressively if appropriate
        import gc

        gc.collect()
        if cupy and "cupy" in sys.modules:  # Check if cupy was imported successfully
            try:
                mempool = cupy.get_default_memory_pool()
                mempool.free_all_blocks()
                logger.info("CuPy memory pool freed.")
            except Exception as e:
                logger.warning(f"Could not free CuPy memory pool: {e}")
        logger.info("Memory optimization attempt finished.")

    def get_hardware_info(self):
        # ...existing code...
        pass


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
            TranslationManager.translate(
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
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.scanning")
        )
        self.status_label.setText(
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.starting"
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
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.cpu_benchmark_duration_prefix"
            )
            in message
        ):  # CHANGED
            try:
                time_str = (
                    message.split(
                        TranslationManager.translate(
                            "app.dialogs.hardware_profiler.status.cpu_benchmark_duration_prefix"
                        )
                    )[1]
                    .split(
                        TranslationManager.translate(
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
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.scan_hardware")
        )
        if self.profile_data and not self.profile_data.get("error"):
            self.status_label.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.scan_completed"
                )
            )
        elif self.profile_data.get("error"):
            self.status_label.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.scan_error_detailed"
                )
            )
        else:
            self.status_label.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.scan_failed"
                )
            )

    def on_profile_ready(self, profile):
        logger.debug(f"PROFILE RECEIVED IN DIALOG: {json.dumps(profile, indent=2)}")
        self.profile_data = profile  # Store the received profile immediately
        if "error" in profile:
            self.status_label.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.error_profile"
                ).format(error=profile["error"][:100] + "...")
            )
        else:
            # Status might be set by on_scan_finished or progress_update, only update if still generic
            if self.status_label.text() == TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.starting"
            ):
                self.status_label.setText(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.profile_ready"
                    )
                )
            self.save_profile()  # Auto-save on successful scan
        self.display_profile()

    def display_profile(self):
        # Update quick info labels first
        self.cpu_label.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.cpu").format(
                self.profile_data.get(
                    "processor",
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.not_available"
                    ),
                )
            )
        )
        ram_gb = self.profile_data.get("memory_total", 0) // (1024**3)
        self.ram_label.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.ram").format(
                ram_gb
            )
        )
        self.gpu_value_label.setText(
            self.profile_data.get(
                "gpu",
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.not_available"
                ),
            )
        )

        if not self.profile_data:
            self.config_display.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.no_data"
                )
            )
            self.optimization_display.setText("")
            self.save_btn.setEnabled(False)
            return

        if "error" in self.profile_data:
            error_details = (
                f"{TranslationManager.translate('app.dialogs.hardware_profiler.profile.error_display')}\\n"
                f"{self.profile_data.get('error', 'Unknown error')}\\n\\n"
            )
            if "traceback" in self.profile_data:
                error_details += (
                    f"{TranslationManager.translate('app.dialogs.hardware_profiler.profile.traceback')}\\\\n"
                    f"{self.profile_data.get('traceback', TranslationManager.translate('app.dialogs.hardware_profiler.status.no_details_available'))}"  # CHANGED
                )
            self.config_display.setText(error_details)
            self.optimization_display.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.no_optimizations_due_to_error"
                )
            )
            self.save_btn.setEnabled(False)
            return

        config_text_parts = []

        # Podstawowe informacje systemowe
        if "uuid" in self.profile_data:
            config_text_parts.append(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.uuid"
                ).format(self.profile_data["uuid"])
            )

        if "system" in self.profile_data:
            config_text_parts.append(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.system"
                ).format(self.profile_data["system"])
            )

        if "processor" in self.profile_data:
            config_text_parts.append(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.processor"
                ).format(self.profile_data["processor"])
            )

        if "cpu_count_physical" in self.profile_data:
            config_text_parts.append(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.cpu_cores"
                ).format(self.profile_data["cpu_count_physical"])
            )

        if "memory_total" in self.profile_data:
            ram_gb = round(self.profile_data["memory_total"] / (1024**3), 1)
            config_text_parts.append(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.ram"
                ).format(ram_gb)
            )

        if "timestamp" in self.profile_data:
            config_text_parts.append(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.last_update"
                ).format(self.profile_data["timestamp"])
            )

        # Wynik testu CPU
        if "cpu_benchmark" in self.profile_data:
            cpu_bench = self.profile_data["cpu_benchmark"]
            if "score" in cpu_bench and cpu_bench["score"] is not None:
                config_text_parts.append(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.profile.cpu_benchmark_score"
                    ).format(round(cpu_bench["score"], 2))
                )
            if "time_s" in cpu_bench and cpu_bench["time_s"] is not None:
                config_text_parts.append(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.profile.cpu_benchmark_time"
                    ).format(f"{round(cpu_bench['time_s'], 2)}s")
                )
            if "error" in cpu_bench:
                config_text_parts.append(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.profile.cpu_benchmark"
                    ).format(f"ERROR: {cpu_bench['error']}")
                )

        # Wynik testu AI/GPU
        if "ai_benchmark_cupy" in self.profile_data:
            ai_bench = self.profile_data["ai_benchmark_cupy"]
            if "time_s" in ai_bench and ai_bench["time_s"] is not None:
                config_text_parts.append(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.profile.ai_benchmark_time"
                    ).format(f"{round(ai_bench['time_s'], 4)}s")
                )
                # Obliczanie i wyświetlanie wyniku AI
                ai_score = calculate_ai_score(ai_bench["time_s"])
                config_text_parts.append(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.profile.ai_benchmark_score"
                    ).format(ai_score)
                )
            elif "error" in ai_bench:
                config_text_parts.append(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.profile.ai_benchmark_score"
                    ).format(f"ERROR: {ai_bench['error']}")
                )
            elif "status" in ai_bench:
                config_text_parts.append(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.profile.ai_benchmark_score"
                    ).format(f"STATUS: {ai_bench['status']}")
                )

        self.config_display.setText("\n".join(config_text_parts))
        self.optimization_display.setText(self.generate_optimizations_text())
        self.save_btn.setEnabled(True)

    def generate_optimizations_text(self):
        if (
            not self.profile_data
            or "optimizations_flags" not in self.profile_data
            or "error" in self.profile_data
        ):
            return TranslationManager.translate(
                "app.dialogs.hardware_profiler.profile.no_optimizations"
            )

        opt_flags = self.profile_data["optimizations_flags"]
        opt_texts = []

        if opt_flags.get("advanced_multithreading"):
            opt_texts.append(
                "• "
                + TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_high"
                )
            )
        elif opt_flags.get("multithreading"):
            opt_texts.append(
                "• "
                + TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_medium"
                )
            )
        else:
            opt_texts.append(
                "• "
                + TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.multithreading_low"
                )
            )

        if opt_flags.get("high_memory_buffering"):
            opt_texts.append(
                "• "
                + TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_high"
                )
            )
        elif opt_flags.get("standard_memory_buffering"):
            opt_texts.append(
                "• "
                + TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_medium"
                )
            )
        else:
            opt_texts.append(
                "• "
                + TranslationManager.translate(
                    "app.dialogs.hardware_profiler.profile.optimizations.buffering_low"
                )
            )

        if not opt_texts:
            return TranslationManager.translate(
                "app.dialogs.hardware_profiler.profile.no_optimizations"
            )
        return "\n".join(opt_texts)

    def load_existing_profile(self):
        if os.path.exists(self.hardware_path):
            try:
                with open(self.hardware_path, "r", encoding="utf-8") as f:
                    self.profile_data = json.load(f)
                self.status_label.setText(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.profile_loaded"
                    )
                )
                self.save_btn.setEnabled(True)
            except json.JSONDecodeError as e:
                self.status_label.setText(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.profile_corrupt"
                    ).format(error=e)
                )
                self.profile_data = {}
            except Exception as e:
                self.status_label.setText(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.profile_load_error"
                    ).format(error=e)
                )
                self.profile_data = {}
        else:
            self.status_label.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.no_profile_found"
                )
            )
        self.display_profile()

    def save_profile(self):
        if not self.profile_data or "error" in self.profile_data:
            self.status_message_requested.emit(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.save_no_data"
                )
            )
            logger.warning("No valid profile data to save.")
            return

        # Upewnij się, że timestamp jest poprawny
        if "timestamp" not in self.profile_data or not self.profile_data["timestamp"]:
            # Dodaj brakujący timestamp
            from PyQt6.QtCore import QDateTime, Qt

            self.profile_data["timestamp"] = QDateTime.currentDateTime().toString(
                Qt.DateFormat.ISODate
            )
            logger.warning(
                f"Dodano brakujący timestamp: {self.profile_data['timestamp']}"
            )

        try:
            # Przed zapisem sprawdź, czy profil może być poprawnie zwalidowany
            from utils.validators import ConfigValidator

            try:
                logger.debug(
                    f"Próba walidacji profilu przed zapisem: {json.dumps(self.profile_data, indent=2)}"
                )
                # Walidacja jest możliwa tylko jeśli plik istnieje - zapis tymczasowy
                temp_path = self.hardware_path + ".temp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(self.profile_data, f, indent=4, ensure_ascii=False)

                # Spróbuj zwalidować
                ConfigValidator.validate_hardware_profile(temp_path)

                # Jeśli walidacja się powiedzie, usuń plik tymczasowy
                os.remove(temp_path)
                logger.info("Walidacja profilu przed zapisem zakończona pomyślnie")
            except Exception as e:
                logger.warning(f"Nieudana walidacja profilu przed zapisem: {e}")
                # Kontynuuj zapis mimo błędu walidacji (możemy dodać pytanie użytkownika)

            # Właściwy zapis profilu
            with open(self.hardware_path, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=4, ensure_ascii=False)
            msg = TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.profile_saved"
            ).format(path=self.hardware_path)
            self.status_message_requested.emit(msg)
            logger.info(f"Profile saved to {self.hardware_path}")
            self.save_btn.setEnabled(True)
        except Exception as e:
            error_msg = TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.profile_save_error"
            ).format(error=e)
            logger.error(f"Error saving profile: {e}")
            self.status_message_requested.emit(error_msg)

    def update_translations(self):
        self.setWindowTitle(
            TranslationManager.translate("app.dialogs.hardware_profiler.title")
        )
        self.title_label.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.title")
        )

        self.gpu_label_static.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.gpu")
        )
        self.current_group.setTitle(
            TranslationManager.translate("app.dialogs.hardware_profiler.current_config")
        )
        self.optimization_group.setTitle(
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.available_optimizations"
            )
        )

        if not (self.thread and self.thread.isRunning()):
            self.scan_btn.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.scan_hardware"
                )
            )
        else:
            self.scan_btn.setText(
                TranslationManager.translate("app.dialogs.hardware_profiler.scanning")
            )

        self.save_btn.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.save_profile")
        )
        self.close_btn.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.close")
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
