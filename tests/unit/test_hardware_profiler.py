"""
Test dla HardwareProfiler z modułu UI.hardware_profiler.

Testy pokrywają:
1. Inicjalizację hardware_profiler
2. Profilowanie sprzętu
3. Walidację danych wyjściowych
4. Obsługę różnych konfiguracji sprzętu
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

import psutil
from PyQt6.QtCore import QDateTime, Qt

from UI.hardware_profiler import HardwareProfilerThread, HardwareProfilerDialog
from utils.exceptions import HardwareProfilingError
from utils.secure_commands import HardwareDetector


class TestHardwareProfiler(unittest.TestCase):
    """Testy dla klas HardwareProfilerThread i HardwareProfilerDialog."""

    def setUp(self):
        """Inicjalizacja przed każdym testem."""
        self.temp_dir = tempfile.mkdtemp()
        self.hardware_json_path = os.path.join(self.temp_dir, "hardware.json")
        
        # Mockowanie HardwareDetector
        self.hardware_detector_patcher = patch("UI.hardware_profiler.HardwareDetector")
        self.mock_hardware_detector = self.hardware_detector_patcher.start()
        self.mock_hardware_detector_instance = self.mock_hardware_detector.return_value
        self.mock_hardware_detector_instance.get_gpu_info.return_value = "NVIDIA GeForce RTX 3080 10GB"
        
        # Mockowanie cupy
        self.cupy_patcher = patch("UI.hardware_profiler.cp")
        self.mock_cp = self.cupy_patcher.start()
        
        # Mockowanie HAS_CUPY
        self.has_cupy_patcher = patch("UI.hardware_profiler.HAS_CUPY", True)
        self.mock_has_cupy = self.has_cupy_patcher.start()

        # Mockowanie psutil
        self.psutil_patcher = patch("UI.hardware_profiler.psutil")
        self.mock_psutil = self.psutil_patcher.start()
        # Konfiguracja psutil.cpu_count
        self.mock_psutil.cpu_count.side_effect = lambda logical: 16 if logical else 8
        # Konfiguracja psutil.virtual_memory
        mock_virtual_memory = MagicMock()
        mock_virtual_memory.total = 16 * 1024 * 1024 * 1024  # 16GB
        self.mock_psutil.virtual_memory.return_value = mock_virtual_memory
        
        # Mockowanie get_stable_uuid
        self.uuid_patcher = patch("UI.hardware_profiler.get_stable_uuid")
        self.mock_get_uuid = self.uuid_patcher.start()
        self.mock_get_uuid.return_value = "3915dbc5-3f60-5f22-a06a-fd48556b8dd1"

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        self.hardware_detector_patcher.stop()
        self.cupy_patcher.stop()
        self.has_cupy_patcher.stop()
        self.psutil_patcher.stop()
        self.uuid_patcher.stop()
        
        # Usunięcie plików tymczasowych
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_run_ai_benchmark_with_gpu(self):
        """Test benchmarku AI gdy GPU jest dostępne."""
        # Konfiguracja mock dla cp.cuda.Stream.null.synchronize()
        mock_stream = MagicMock()
        type(self.mock_cp.cuda).Stream = PropertyMock(return_value=mock_stream)
        mock_stream.null = MagicMock()
        
        # Konfiguracja mock dla cp.get_default_memory_pool()
        mock_mempool = MagicMock()
        self.mock_cp.get_default_memory_pool.return_value = mock_mempool
        
        # Konfiguracja mock dla cp.cuda.Device().mem_info
        mock_device = MagicMock()
        type(self.mock_cp.cuda).Device = MagicMock(return_value=mock_device)
        type(mock_device).mem_info = PropertyMock(return_value=(10000000000, 16000000000))
        
        # Wykonanie benchmarku AI
        profiler_thread = HardwareProfilerThread(hardware_path=self.hardware_json_path)
        result = profiler_thread.run_ai_benchmark()
        
        # Asercje
        self.assertIsNotNone(result)
        self.assertIsInstance(result, float)
        self.mock_cp.asarray.assert_called()
        self.mock_cp.dot.assert_called()
        mempool = self.mock_cp.get_default_memory_pool.return_value
        mempool.free_all_blocks.assert_called()

    def test_run_ai_benchmark_without_gpu(self):
        """Test benchmarku AI gdy GPU nie jest dostępne."""
        # Nadpisanie wartości HAS_CUPY na False
        with patch("UI.hardware_profiler.HAS_CUPY", False):
            profiler_thread = HardwareProfilerThread(hardware_path=self.hardware_json_path)
            result = profiler_thread.run_ai_benchmark()
            
            # Asercje
            self.assertIsNone(result)
            self.mock_cp.asarray.assert_not_called()

    def test_profile_validation(self):
        """Test walidacji profilu sprzętowego."""
        profiler_thread = HardwareProfilerThread(hardware_path=self.hardware_json_path)
        
        # Poprawny profil
        valid_profile = {
            "uuid": "3915dbc5-3f60-5f22-a06a-fd48556b8dd1",
            "system": "Windows",
            "processor": "Intel Core i7",
            "cpu_count_logical": 16,
            "cpu_count_physical": 8,
            "memory_total": 16 * 1024 * 1024 * 1024,
            "gpu": "NVIDIA GeForce RTX 3080 10GB",
            "optimizations_flags": {
                "multithreading": True,
                "advanced_multithreading": True,
                "high_memory_buffering": True,
                "standard_memory_buffering": True
            }
        }
        
        is_valid, errors = profiler_thread._validate_hardware_profile(valid_profile)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Niepoprawny profil - brak wymaganych pól
        invalid_profile = {
            "system": "Windows",
            "processor": "Intel Core i7"
        }
        
        is_valid, errors = profiler_thread._validate_hardware_profile(invalid_profile)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Niepoprawny profil - złe typy danych
        invalid_types_profile = {
            "uuid": "3915dbc5-3f60-5f22-a06a-fd48556b8dd1",
            "system": "Windows",
            "processor": "Intel Core i7",
            "cpu_count_logical": "16",  # powinien być int
            "memory_total": 16 * 1024 * 1024 * 1024,
            "gpu": 123,  # powinien być string
            "optimizations_flags": {
                "multithreading": "tak",  # powinien być bool
                "advanced_multithreading": True,
                "high_memory_buffering": True,
                "standard_memory_buffering": True
            }
        }
        
        is_valid, errors = profiler_thread._validate_hardware_profile(invalid_types_profile)
        self.assertFalse(is_valid)
        self.assertGreaterEqual(len(errors), 2)  # co najmniej 2 błędy

    def test_save_profile_to_json(self):
        """Test zapisywania profilu do pliku JSON."""
        profiler_thread = HardwareProfilerThread(hardware_path=self.hardware_json_path)
        
        profile = {
            "uuid": "3915dbc5-3f60-5f22-a06a-fd48556b8dd1",
            "system": "Windows",
            "release": "11",
            "version": "10.0.26100",
            "machine": "AMD64",
            "processor": "Intel Core i7",
            "cpu_count_logical": 16,
            "memory_total": 16 * 1024 * 1024 * 1024,
            "timestamp": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
        }
        
        # Zapis do pliku
        result = profiler_thread._save_profile_to_json(profile, self.hardware_json_path)
        
        # Asercje
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.hardware_json_path))
        
        # Sprawdzenie zawartości pliku
        with open(self.hardware_json_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        self.assertIn("uuid", saved_data)
        self.assertIn("created_at", saved_data)
        self.assertIn("system_info", saved_data)
        self.assertEqual(saved_data["uuid"], "3915dbc5-3f60-5f22-a06a-fd48556b8dd1")

    def test_run_with_gpu(self):
        """Test głównej metody run() z dostępnym GPU."""
        # Konfiguracja mocków dla profilera
        profiler_thread = HardwareProfilerThread(hardware_path=self.hardware_json_path)
        profiler_thread.run_ai_benchmark = MagicMock(return_value=0.123)
        profiler_thread.profile_ready = MagicMock()
        profiler_thread.progress_update = MagicMock()
        
        # Wykonanie metody run
        profiler_thread.run()
        
        # Asercje
        profiler_thread.profile_ready.emit.assert_called_once()
        profile = profiler_thread.profile_ready.emit.call_args[0][0]
        
        # Sprawdzenie wyników
        self.assertEqual(profile["uuid"], "3915dbc5-3f60-5f22-a06a-fd48556b8dd1")
        self.assertEqual(profile["gpu"], "NVIDIA GeForce RTX 3080 10GB")
        self.assertTrue(profile["optimizations_flags"]["multithreading"])
        self.assertTrue(profile["optimizations_flags"]["advanced_multithreading"])
        self.assertTrue("cupy" in profile["python_libraries"])

    @patch("UI.hardware_profiler.HAS_CUPY", False)
    def test_run_without_gpu(self):
        """Test głównej metody run() bez dostępnego GPU."""
        # Symulacja błędu wykrywania GPU
        self.mock_hardware_detector_instance.get_gpu_info.side_effect = Exception("GPU not found")
        
        # Konfiguracja profilera
        profiler_thread = HardwareProfilerThread(hardware_path=self.hardware_json_path)
        profiler_thread.profile_ready = MagicMock()
        profiler_thread.progress_update = MagicMock()
        
        # Wykonanie metody run
        profiler_thread.run()
        
        # Asercje
        profiler_thread.profile_ready.emit.assert_called_once()
        profile = profiler_thread.profile_ready.emit.call_args[0][0]
        
        # Sprawdzenie obsługi błędu GPU
        self.assertNotEqual(profile["gpu"], "NVIDIA GeForce RTX 3080 10GB")
        self.assertIn("gpu_error_details", profile)
        self.assertNotIn("cupy", profile["python_libraries"])


if __name__ == "__main__":
    unittest.main()
