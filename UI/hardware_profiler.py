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

            # Bezpieczne zarządzanie pamięcią - próba wyczyszczenia przed uruchomieniem
            try:
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
                logger.debug("Successfully cleared GPU memory pool before benchmark")
            except Exception as mem_err:
                logger.warning(f"Could not clear GPU memory pool: {mem_err}")

            # Monitorowanie użycia pamięci
            try:
                before_mem = cp.cuda.Device().mem_info
                logger.debug(
                    f"GPU memory before benchmark - Free: {before_mem[0]}, Total: {before_mem[1]}"
                )
            except Exception as mem_info_err:
                logger.warning(f"Could not get GPU memory info: {mem_info_err}")

            # Tworzenie macierzy na GPU
            a_cpu = np.random.rand(size, size).astype(np.float32)
            b_cpu = np.random.rand(size, size).astype(np.float32)

            # Przenieś dane na GPU
            a_gpu = cp.asarray(a_cpu)
            b_gpu = cp.asarray(b_cpu)

            # Zwolnij pamięć CPU po przeniesieniu danych na GPU
            del a_cpu, b_cpu

            # Synchronizacja przed pomiarem czasu
            cp.cuda.Stream.null.synchronize()

            # Właściwy pomiar
            logger.debug("Starting GPU benchmark timing...")
            start_time = time.time()

            # Wykonaj mnożenie macierzy
            c_gpu = cp.dot(a_gpu, b_gpu)

            # Upewnij się, że wszystkie operacje GPU się zakończyły
            cp.cuda.Stream.null.synchronize()

            duration = time.time() - start_time

            # Monitorowanie użycia pamięci po benchmarku
            try:
                after_mem = cp.cuda.Device().mem_info
                logger.debug(
                    f"GPU memory after benchmark - Free: {after_mem[0]}, Total: {after_mem[1]}"
                )
                memory_used = before_mem[0] - after_mem[0]
                logger.debug(f"GPU memory used by benchmark: {memory_used} bytes")
            except Exception as mem_info_err:
                logger.warning(
                    f"Could not get GPU memory info after benchmark: {mem_info_err}"
                )

            # Systematyczne zwalnianie zasobów GPU
            try:
                # Najpierw usuń poszczególne tablice
                del a_gpu, b_gpu, c_gpu
                # Następnie wymuś synchronizację
                cp.cuda.Stream.null.synchronize()
                # Na koniec wyczyść całą pamięć podręczną
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
                logger.debug("Successfully released GPU memory resources")
            except Exception as e:
                logger.error(f"Error during GPU memory cleanup: {e}")

            logger.debug(f"GPU benchmark completed in {duration:.4f} seconds")
            return duration

        except Exception as e:
            logger.error(f"Error during GPU benchmark: {e}", exc_info=True)

            # Próba odzyskania zasobów nawet w przypadku błędu
            try:
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
                logger.debug("Cleaned GPU memory pool after benchmark error")
            except Exception:
                pass

            return None

    def _save_profile_to_json(self, profile, file_path=None):
        """
        Zapisuje profil sprzętowy do pliku JSON z walidacją danych.

        Args:
            profile (dict): Słownik z danymi profilu sprzętowego
            file_path (str, optional): Ścieżka do pliku JSON. Jeśli None, używa self.hardware_path.

        Returns:
            bool: True jeśli zapis się powiódł, False w przeciwnym razie.
        """
        if not file_path and self.hardware_path:
            file_path = self.hardware_path

        if not file_path:
            logger.error("No file path provided for hardware profile")
            return False

        # Walidacja profilu przed zapisem
        required_keys = [
            "uuid",
            "system",
            "processor",
            "cpu_count_logical",
            "memory_total",
        ]
        for key in required_keys:
            if key not in profile:
                logger.error(f"Invalid hardware profile: missing required key '{key}'")
                return False

        # Formatowanie timestamp dla lepszej czytelności
        if "timestamp" in profile:
            current_time = QDateTime.currentDateTime()
            profile["created_at"] = current_time.toString("yyyy-MM-dd HH:mm:ss")
            # Restrukturyzacja dla lepszej organizacji, ale zachowując wszystkie dane oryginalne
        structured_profile = profile.copy()  # Kopiujemy cały profil

        # Dodajemy dodatkowe informacje strukturalne
        structured_profile["system_info"] = {
            "system": profile["system"],
            "node": platform.node(),
            "release": profile["release"],
            "version": profile["version"],
            "machine": profile["machine"],
            "processor": profile["processor"],
        }

        # Upewniamy się, że created_at jest ustawione
        structured_profile["created_at"] = profile.get(
            "created_at", profile.get("timestamp", "")
        )

        try:
            # Sprawdź czy katalog istnieje, jeśli nie, utwórz go
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # Zapisz plik z wcięciami dla lepszej czytelności
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(structured_profile, f, indent=4, ensure_ascii=False)

            logger.info(f"Hardware profile successfully saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save hardware profile to {file_path}: {e}")
            return False

    def run(self):
        """Główna metoda wątku profilowania sprzętu."""
        logger.debug("Starting hardware profiling thread")
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

            # Obsługa błędów i walidacja dla informacji o GPU
            try:
                gpu_info = self.hardware_detector.get_gpu_info()
                if not gpu_info or not isinstance(gpu_info, str):
                    raise ValueError("Invalid GPU information format")

                profile["gpu"] = gpu_info
                logger.debug(f"GPU detected: {profile['gpu']}")
            except Exception as e:
                logger.error(f"GPU detection failed: {e}", exc_info=True)
                profile["gpu"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.gpu_detection_error"
                )
                # Dodajemy szczegóły błędu dla diagnostyki
                profile["gpu_error_details"] = str(e)

            # Walidacja i bezpieczne przypisanie liczby rdzeni CPU
            cpu_cores = profile.get("cpu_count_physical", 0)
            if not cpu_cores or not isinstance(cpu_cores, int) or cpu_cores <= 0:
                cpu_cores = profile.get("cpu_count_logical", 1)
                if not isinstance(cpu_cores, int) or cpu_cores <= 0:
                    cpu_cores = 1
                    logger.warning(
                        "Could not detect valid CPU core count, using fallback value of 1"
                    )

            # Walidacja i bezpieczne przypisanie pamięci
            memory_gb = 0
            try:
                memory_gb = profile["memory_total"] // (1024**3)
                if memory_gb <= 0:
                    raise ValueError("Invalid memory size")
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(
                    f"Invalid memory information: {e}. Using fallback value."
                )
                memory_gb = 4  # Wartość domyślna 4GB

            # Konfiguracja flag optymalizacji
            optimizations = {
                "multithreading": cpu_cores >= 4,
                "advanced_multithreading": cpu_cores >= 8,
                "high_memory_buffering": memory_gb >= 16,
                "standard_memory_buffering": memory_gb >= 8,
            }
            profile["optimizations_flags"] = optimizations

            # Walidacja i bezpieczne przypisanie bibliotek Pythona
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
                    )

            # Sprawdź GPU NVIDIA + CuPy
            if (
                isinstance(profile.get("gpu"), str)
                and "nvidia" in profile["gpu"].lower()
                and HAS_CUPY
            ):
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
                    ).format(
                        path=python_path
                    )  # CHANGED
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
                        ).format(command=" ".join(cmd))
                    )

                    stdout, stderr = secure_runner.run_command(cmd, timeout=180)
                    elapsed_perf = time.time() - start_time_perf

                    logger.debug(f"Output pyperformance (stdout): {stdout.strip()}")
                    if stderr:
                        logger.debug(f"Output pyperformance (stderr): {stderr.strip()}")

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
                            logger.debug("Found json_loads benchmark in main metadata.")
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
                        ).format(error=str(e))
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
                        ).format(
                            error=str(e)
                        )  # CHANGED
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
                    ).format(
                        error=str(e_cpu_bench)
                    )  # CHANGED
                )

            # AI/GPU Benchmark (CuPy)
            if HAS_CUPY and cp:
                self.progress_update.emit(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.running_gpu_benchmark"
                    )
                )
                logger.debug("Rozpoczęcie testu AI/GPU (CuPy)...")
                try:
                    ai_time_s = self.run_ai_benchmark()
                    profile["ai_benchmark_cupy"] = {"time_s": ai_time_s}
                    logger.debug(
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
                }  # Przygotuj profil do zapisu z walidacją
            # Usuwamy pierwsze wywołanie bez ścieżki, które nie było poprawne
            # Zapiszemy tylko raz z odpowiednią ścieżką poniżej

            # Zapisz profil do hardware.json jeśli ścieżka została podana
            if self.hardware_path:
                self.progress_update.emit(
                    TranslationManager.translate(
                        "app.dialogs.hardware_profiler.status.saving_profile"
                    )
                )

                # Walidacja profilu przed zapisem
                is_valid, validation_errors = self._validate_hardware_profile(profile)
                if not is_valid:
                    logger.warning(
                        f"Hardware profile validation errors: {validation_errors}"
                    )
                    profile["validation_errors"] = validation_errors

                self._save_profile_to_json(profile, self.hardware_path)

            # Generuj rekomendacje dla różnych konfiguracji sprzętu
            recommendations = self._generate_hardware_recommendations(profile)
            profile["recommendations"] = recommendations

            # Emituj sygnał o gotowości profilu
            self.profile_ready.emit(profile)

        except Exception as e:
            logger.error(f"Hardware profiling error: {e}", exc_info=True)
            error_profile = {"error": str(e), "traceback": traceback.format_exc()}
            self.profile_ready.emit(error_profile)
            raise HardwareProfilingError(
                f"Error during hardware profiling: {e}", details=str(e)
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
        logger.debug("Memory optimization attempt finished.")

    def get_hardware_info(self):
        # ...existing code...
        pass

    def _validate_hardware_profile(self, profile):
        """
        Waliduje poprawność struktury profilu sprzętowego.

        Args:
            profile (dict): Profil sprzętowy do walidacji

        Returns:
            tuple: (is_valid, errors_list) - czy profil jest poprawny i lista błędów
        """
        errors = []

        # Wymagane pola
        required_fields = [
            "uuid",
            "system",
            "processor",
            "cpu_count_logical",
            "memory_total",
        ]
        for field in required_fields:
            if field not in profile:
                errors.append(f"Brakujące pole: {field}")

        # Walidacja typów danych
        if "cpu_count_logical" in profile and not isinstance(
            profile["cpu_count_logical"], int
        ):
            errors.append(
                f"Niepoprawny typ pola cpu_count_logical: {type(profile['cpu_count_logical'])}, oczekiwano: int"
            )

        if "memory_total" in profile and not isinstance(profile["memory_total"], int):
            errors.append(
                f"Niepoprawny typ pola memory_total: {type(profile['memory_total'])}, oczekiwano: int"
            )

        if "gpu" in profile and not isinstance(profile["gpu"], str):
            errors.append(
                f"Niepoprawny typ pola gpu: {type(profile['gpu'])}, oczekiwano: str"
            )

        # Walidacja poprawności UUID
        if "uuid" in profile:
            try:
                uuid_obj = uuid.UUID(profile["uuid"])
                if str(uuid_obj) != profile["uuid"]:
                    errors.append(f"Niepoprawny format UUID: {profile['uuid']}")
            except (ValueError, AttributeError):
                errors.append(f"Niepoprawny format UUID: {profile['uuid']}")

        # Walidacja flag optymalizacji
        if "optimizations_flags" in profile:
            if not isinstance(profile["optimizations_flags"], dict):
                errors.append("Flagi optymalizacji muszą być słownikiem")
            else:
                # Sprawdź wymagane flagi optymalizacji
                required_flags = [
                    "multithreading",
                    "advanced_multithreading",
                    "high_memory_buffering",
                    "standard_memory_buffering",
                ]

                for flag in required_flags:
                    if flag not in profile["optimizations_flags"]:
                        errors.append(f"Brakująca flaga optymalizacji: {flag}")
                    elif not isinstance(profile["optimizations_flags"][flag], bool):
                        errors.append(
                            f"Flaga optymalizacji {flag} powinna być typu bool"
                        )

        return len(errors) == 0, errors

    def _generate_hardware_recommendations(self, profile):
        """
        Generuje rekomendacje dotyczące optymalizacji na podstawie profilu sprzętu.

        Args:
            profile (dict): Profil sprzętowy

        Returns:
            dict: Słownik z rekomendacjami
        """
        recommendations = {}

        # Sprawdzenie CPU
        cpu_cores_physical = profile.get("cpu_count_physical", 0)
        cpu_cores_logical = profile.get("cpu_count_logical", 0)

        if cpu_cores_physical > 0 and cpu_cores_logical > 0:
            # Analiza rdzeni CPU
            if cpu_cores_physical >= 8:
                recommendations["cpu"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.cpu_excellent"
                )
                recommendations["cpu_level"] = "excellent"
            elif cpu_cores_physical >= 4:
                recommendations["cpu"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.cpu_good"
                )
                recommendations["cpu_level"] = "good"
            else:
                recommendations["cpu"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.cpu_minimal"
                )
                recommendations["cpu_level"] = "minimal"

        # Sprawdzenie RAM
        memory_gb = profile.get("memory_total", 0) // (1024**3)
        if memory_gb >= 16:
            recommendations["ram"] = TranslationManager.translate(
                "app.dialogs.hardware_profiler.recommendations.ram_excellent"
            )
            recommendations["ram_level"] = "excellent"
        elif memory_gb >= 8:
            recommendations["ram"] = TranslationManager.translate(
                "app.dialogs.hardware_profiler.recommendations.ram_good"
            )
            recommendations["ram_level"] = "good"
        else:
            recommendations["ram"] = TranslationManager.translate(
                "app.dialogs.hardware_profiler.recommendations.ram_minimal"
            )
            recommendations["ram_level"] = "minimal"

        # Sprawdzenie GPU
        gpu_info = profile.get("gpu", "")
        if isinstance(gpu_info, str):
            if "nvidia" in gpu_info.lower():
                if any(
                    model in gpu_info.lower()
                    for model in ["rtx", "titan", "a100", "v100"]
                ):
                    recommendations["gpu"] = TranslationManager.translate(
                        "app.dialogs.hardware_profiler.recommendations.gpu_excellent"
                    )
                    recommendations["gpu_level"] = "excellent"
                elif any(
                    model in gpu_info.lower() for model in ["gtx", "quadro", "tesla"]
                ):
                    recommendations["gpu"] = TranslationManager.translate(
                        "app.dialogs.hardware_profiler.recommendations.gpu_good"
                    )
                    recommendations["gpu_level"] = "good"
                else:
                    recommendations["gpu"] = TranslationManager.translate(
                        "app.dialogs.hardware_profiler.recommendations.gpu_minimal"
                    )
                    recommendations["gpu_level"] = "minimal"
            elif any(
                vendor in gpu_info.lower()
                for vendor in ["amd", "radeon", "intel", "iris"]
            ):
                recommendations["gpu"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.gpu_limited"
                )
                recommendations["gpu_level"] = "limited"
            else:
                recommendations["gpu"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.gpu_unknown"
                )
                recommendations["gpu_level"] = "unknown"
        else:
            recommendations["gpu"] = TranslationManager.translate(
                "app.dialogs.hardware_profiler.recommendations.gpu_not_detected"
            )
            recommendations["gpu_level"] = "not_detected"

        # Generowanie ogólnej oceny
        scores = {
            "excellent": 3,
            "good": 2,
            "minimal": 1,
            "limited": 0.5,
            "unknown": 0,
            "not_detected": 0,
        }

        total_score = 0
        components = 0

        # Obliczanie średniej ważonej (CPU i RAM mają większą wagę niż GPU)
        if "cpu_level" in recommendations:
            total_score += scores.get(recommendations["cpu_level"], 0) * 1.5
            components += 1.5

        if "ram_level" in recommendations:
            total_score += scores.get(recommendations["ram_level"], 0) * 1.2
            components += 1.2

        if "gpu_level" in recommendations:
            total_score += scores.get(recommendations["gpu_level"], 0) * 1.0
            components += 1.0

        if components > 0:
            average_score = total_score / components

            if average_score >= 2.5:
                recommendations["overall"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.overall_excellent"
                )
                recommendations["overall_level"] = "excellent"
            elif average_score >= 1.5:
                recommendations["overall"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.overall_good"
                )
                recommendations["overall_level"] = "good"
            else:
                recommendations["overall"] = TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.overall_minimal"
                )
                recommendations["overall_level"] = "minimal"
        else:
            recommendations["overall"] = TranslationManager.translate(
                "app.dialogs.hardware_profiler.recommendations.overall_unknown"
            )
            recommendations["overall_level"] = "unknown"

        return recommendations


class HardwareProfilerDialog(QDialog):
    def __init__(self, parent=None, hardware_path=None):
        super().__init__(parent)
        self.setWindowTitle(
            TranslationManager.translate("app.dialogs.hardware_profiler.title")
        )  # CHANGED
        self.resize(700, 500)
        self.hardware_path = hardware_path
        self.profiler_thread = None
        self.timer = None
        self.elapsed_seconds = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Tytuł
        title_label = QLabel(
            TranslationManager.translate("app.dialogs.hardware_profiler.header")
        )  # CHANGED
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # Informacja
        info_label = QLabel(
            TranslationManager.translate("app.dialogs.hardware_profiler.description")
        )  # CHANGED
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Informacje o sprzęcie
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

        # Grupa dla aktualnej konfiguracji
        self.current_group = QGroupBox(
            TranslationManager.translate("app.dialogs.hardware_profiler.current_config")
        )
        self.current_group.setStyleSheet(
            """
            QGroupBox { 
                border: 1px solid #cccccc;
                margin-top: 15px;
                border-radius: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """
        )

        current_layout = QVBoxLayout(self.current_group)
        self.config_display = QTextEdit()
        self.config_display.setReadOnly(True)
        self.config_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.config_display.setStyleSheet(
            "QTextEdit { border: none; background: transparent; padding: 5px; }"
        )
        self.config_display.setViewportMargins(5, 5, 5, 5)
        current_layout.addWidget(self.config_display)
        layout.addWidget(self.current_group)

        # Grupa dla rekomendacji
        self.recommendation_group = QGroupBox(
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.recommendations"
            )
        )
        self.recommendation_group.setStyleSheet(
            """
            QGroupBox { 
                border: 1px solid #cccccc;
                margin-top: 15px;
                border-radius: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """
        )

        recommendation_layout = QVBoxLayout(self.recommendation_group)
        self.recommendation_display = QTextEdit()
        self.recommendation_display.setReadOnly(True)
        self.recommendation_display.setStyleSheet(
            "QTextEdit { border: none; background: transparent; padding: 5px; }"
        )
        self.recommendation_display.setViewportMargins(5, 5, 5, 5)
        recommendation_layout.addWidget(self.recommendation_display)
        layout.addWidget(self.recommendation_group)

        # Status i progres
        self.status_label = QLabel(
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.ready_status"
            )
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(
            "%p% - %v/%m "
            + TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.seconds"
            )
        )
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #5CB3FF;
                width: 10px;
                margin: 0.5px;
                border-radius: 2px;
            }
        """
        )
        layout.addWidget(self.progress_bar)

        # Przyciski
        button_layout = QHBoxLayout()
        self.run_button = QPushButton(
            TranslationManager.translate("app.dialogs.hardware_profiler.run_button")
        )  # CHANGED
        self.run_button.setStyleSheet(
            """
            QPushButton {
                background-color: #5CB3FF;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4CA0EE;
            }
            QPushButton:pressed {
                background-color: #3B8FDD;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """
        )

        self.close_button = QPushButton(
            TranslationManager.translate("app.dialogs.hardware_profiler.close_button")
        )  # CHANGED
        button_layout.addStretch()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Połączenia przycisków
        self.run_button.clicked.connect(self.run_profiling)
        self.close_button.clicked.connect(self.close)

        # Inicjalizacja
        self.gpu_label_static.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.gpu_label")
        )

        # Ukryj grupę rekomendacji na początku
        self.recommendation_group.hide()

    def _display_recommendation_html(self, recommendations):
        """
        Wyświetla rekomendacje w formacie HTML z kolorowym formatowaniem.

        Args:
            recommendations (dict): Słownik z rekomendacjami
        """
        if not recommendations:
            return

        # Mapowanie poziomów na kolory
        level_colors = {
            "excellent": "#339933",  # Zielony
            "good": "#3366CC",  # Niebieski
            "minimal": "#FF9933",  # Pomarańczowy
            "limited": "#FF6600",  # Ciemny pomarańczowy
            "unknown": "#999999",  # Szary
            "not_detected": "#CC3333",  # Czerwony
        }

        html = "<div style='font-family: Arial, sans-serif;'>"

        # Ogólna rekomendacja
        if "overall" in recommendations and "overall_level" in recommendations:
            color = level_colors.get(recommendations["overall_level"], "#000000")
            html += f"<div style='margin-bottom: 15px;'>"
            html += f"<div style='font-weight: bold; font-size: 16px; color: {color};'>"
            html += (
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.overall_header"
                )
                + "</div>"
            )
            html += (
                f"<div style='margin-left: 10px;'>{recommendations['overall']}</div>"
            )
            html += "</div>"

        # Rekomendacje CPU
        if "cpu" in recommendations and "cpu_level" in recommendations:
            color = level_colors.get(recommendations["cpu_level"], "#000000")
            html += f"<div style='margin-bottom: 10px;'>"
            html += f"<div style='font-weight: bold; color: {color};'>"
            html += (
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.cpu_header"
                )
                + "</div>"
            )
            html += f"<div style='margin-left: 10px;'>{recommendations['cpu']}</div>"
            html += "</div>"

        # Rekomendacje RAM
        if "ram" in recommendations and "ram_level" in recommendations:
            color = level_colors.get(recommendations["ram_level"], "#000000")
            html += f"<div style='margin-bottom: 10px;'>"
            html += f"<div style='font-weight: bold; color: {color};'>"
            html += (
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.ram_header"
                )
                + "</div>"
            )
            html += f"<div style='margin-left: 10px;'>{recommendations['ram']}</div>"
            html += "</div>"

        # Rekomendacje GPU
        if "gpu" in recommendations and "gpu_level" in recommendations:
            color = level_colors.get(recommendations["gpu_level"], "#000000")
            html += f"<div style='margin-bottom: 10px;'>"
            html += f"<div style='font-weight: bold; color: {color};'>"
            html += (
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.recommendations.gpu_header"
                )
                + "</div>"
            )
            html += f"<div style='margin-left: 10px;'>{recommendations['gpu']}</div>"
            html += "</div>"

        html += "</div>"
        self.recommendation_display.setHtml(html)
        self.recommendation_group.show()

    def display_profile(self, profile):
        """
        Wyświetla informacje o profilu sprzętu w dialogu.

        Args:
            profile (dict): Profil sprzętu do wyświetlenia
        """
        # Sprawdź czy wystąpił błąd
        if "error" in profile:
            self.status_label.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.status.error"
                )
                + f": {profile['error']}"
            )
            self.status_label.setStyleSheet("color: #CC3333; font-weight: bold;")
            return

        # CPU i RAM
        cpu_physical = profile.get("cpu_count_physical", 0)
        cpu_logical = profile.get("cpu_count_logical", 0)

        memory_gb = profile.get("memory_total", 0) // (1024**3)

        self.cpu_label.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.cpu_label")
            + f" {cpu_physical} ({cpu_logical})"
        )

        self.ram_label.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.ram_label")
            + f" {memory_gb} GB"
        )

        # GPU
        gpu_info = profile.get(
            "gpu",
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.gpu_not_detected"
            ),
        )
        self.gpu_value_label.setText(gpu_info)

        # Warnungi związane z GPU
        if "gpu_error_details" in profile:
            self.gpu_value_label.setStyleSheet("color: #CC3333;")
        else:
            self.gpu_value_label.setStyleSheet("")

        # Aktualna konfiguracja w formacie JSON
        config_json = json.dumps(profile, indent=2)
        self.config_display.setText(config_json)

        # Rekomendacje
        if "recommendations" in profile:
            self._display_recommendation_html(profile["recommendations"])

        # Status
        self.status_label.setText(
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.status.finished"
            )
        )
        self.status_label.setStyleSheet("color: #339933; font-weight: bold;")

        # Ukryj progres i zaktualizuj przyciski
        self.progress_bar.hide()
        self.run_button.setText(
            TranslationManager.translate(
                "app.dialogs.hardware_profiler.run_again_button"
            )
        )
        self.run_button.setEnabled(True)

    def run_profiling(self):
        """
        Uruchamia profilowanie sprzętu w osobnym wątku.
        """
        if self.profiler_thread and self.profiler_thread.isRunning():
            return

        # Zresetuj UI
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.run_button.setEnabled(False)
        self.recommendation_group.hide()
        self.status_label.setStyleSheet("")
        self.status_label.setText(
            TranslationManager.translate("app.dialogs.hardware_profiler.status.running")
        )

        # Zresetuj licznik czasu
        self.elapsed_seconds = 0

        # Stwórz i uruchom wątek
        self.profiler_thread = HardwareProfilerThread(hardware_path=self.hardware_path)
        self.profiler_thread.profile_ready.connect(self.display_profile)
        self.profiler_thread.progress_update.connect(self.status_label.setText)
        self.profiler_thread.finished.connect(self.on_thread_finished)

        # Uruchom timer do aktualizacji paska postępu
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)  # Co sekundę

        # Uruchom wątek
        self.profiler_thread.start()

    def update_progress(self):
        """
        Aktualizuje pasek postępu podczas profilowania.
        """
        self.elapsed_seconds += 1
        max_seconds = self.progress_bar.maximum()

        if self.elapsed_seconds >= max_seconds:
            # Jeśli przekroczono maksymalny czas, zwiększ go
            new_max = max_seconds + 10
            self.progress_bar.setMaximum(new_max)

        self.progress_bar.setValue(self.elapsed_seconds)

    def on_thread_finished(self):
        """
        Obsługuje zakończenie wątku profilowania.
        """
        if self.timer and self.timer.isActive():
            self.timer.stop()

        # Jeśli wystąpił błąd, przywróć przycisk do stanu początkowego
        if self.status_label.text().startswith(
            TranslationManager.translate("app.dialogs.hardware_profiler.status.error")
        ):
            self.run_button.setEnabled(True)
            self.run_button.setText(
                TranslationManager.translate(
                    "app.dialogs.hardware_profiler.run_again_button"
                )
            )
