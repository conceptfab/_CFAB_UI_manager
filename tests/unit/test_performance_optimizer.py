"""
Testy jednostkowe dla modułu utils.performance_optimizer.

Ten moduł testuje wszystkie komponenty optymalizacji wydajności:
- LazyLoader (lazy loading zasobów)
- AsyncResourceLoader (asynchroniczne ładowanie)
- PerformanceMonitor (monitorowanie wydajności)
- StartupOptimizer (optymalizacja startu)
- Funkcje pomocnicze (cached_file_reader, lazy_property itp.)
"""

import asyncio
import gc
import json
import os
import tempfile
import threading
import time
import unittest
import weakref
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, Mock, call, patch

import psutil
from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from utils.exceptions import ErrorCode, PerformanceError

# Import systemu do testowania
from utils.performance_optimizer import (
    AsyncResourceLoader,
    LazyLoader,
    PerformanceMonitor,
    StartupOptimizer,
    cached_file_reader,
    create_config_loader,
    create_css_loader,
    create_translation_loader,
    defer_until_after_startup,
    lazy_loader,
    lazy_property,
    performance_monitor,
    startup_optimizer,
)


class TestLazyLoader(unittest.TestCase):
    """Test klasy LazyLoader dla lazy loading zasobów."""

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        self.loader = LazyLoader()

    def test_register_loader_success(self):
        """Should register loader function for resource."""

        def test_loader():
            return "test_resource"

        self.loader.register_loader("test", test_loader)

        self.assertIn("test", self.loader._loaders)
        self.assertEqual(self.loader._loaders["test"], test_loader)

    def test_get_resource_loads_once(self):
        """Should load resource only once and cache result."""
        call_count = 0

        def expensive_loader():
            nonlocal call_count
            call_count += 1
            return f"resource_{call_count}"

        self.loader.register_loader("expensive", expensive_loader)

        # Pierwsze wywołanie - powinno ładować
        result1 = self.loader.get_resource("expensive")
        self.assertEqual(result1, "resource_1")
        self.assertEqual(call_count, 1)

        # Drugie wywołanie - powinno zwrócić z cache
        result2 = self.loader.get_resource("expensive")
        self.assertEqual(result2, "resource_1")
        self.assertEqual(call_count, 1)  # Nie powinno wywołać loadera ponownie

    def test_get_resource_unregistered(self):
        """Should raise PerformanceError for unregistered resource."""
        with self.assertRaises(PerformanceError) as cm:
            self.loader.get_resource("nonexistent")

        self.assertIn("No loader registered", str(cm.exception))

    def test_get_resource_loader_exception(self):
        """Should raise PerformanceError when loader fails."""

        def failing_loader():
            raise ValueError("Loader failed")

        self.loader.register_loader("failing", failing_loader)

        with self.assertRaises(PerformanceError) as cm:
            self.loader.get_resource("failing")

        self.assertIn("Failed to load resource", str(cm.exception))

    def test_is_loaded(self):
        """Should correctly report if resource is loaded."""

        def simple_loader():
            return "loaded"

        self.loader.register_loader("test", simple_loader)

        # Przed załadowaniem
        self.assertFalse(self.loader.is_loaded("test"))

        # Po załadowaniu
        self.loader.get_resource("test")
        self.assertTrue(self.loader.is_loaded("test"))

    def test_clear_cache_specific(self):
        """Should clear cache for specific resource."""

        def loader1():
            return "resource1"

        def loader2():
            return "resource2"

        self.loader.register_loader("res1", loader1)
        self.loader.register_loader("res2", loader2)

        # Załaduj oba zasoby
        self.loader.get_resource("res1")
        self.loader.get_resource("res2")

        self.assertTrue(self.loader.is_loaded("res1"))
        self.assertTrue(self.loader.is_loaded("res2"))

        # Wyczyść cache dla res1
        self.loader.clear_cache("res1")

        self.assertFalse(self.loader.is_loaded("res1"))
        self.assertTrue(self.loader.is_loaded("res2"))

    def test_clear_cache_all(self):
        """Should clear all cached resources."""

        def loader1():
            return "resource1"

        def loader2():
            return "resource2"

        self.loader.register_loader("res1", loader1)
        self.loader.register_loader("res2", loader2)

        # Załaduj oba zasoby
        self.loader.get_resource("res1")
        self.loader.get_resource("res2")

        # Wyczyść cały cache
        self.loader.clear_cache()

        self.assertFalse(self.loader.is_loaded("res1"))
        self.assertFalse(self.loader.is_loaded("res2"))

    def test_concurrent_loading_protection(self):
        """Should handle concurrent loading attempts."""
        loading_started = threading.Event()
        can_complete = threading.Event()

        def slow_loader():
            loading_started.set()
            can_complete.wait(timeout=5)  # Czeka na sygnał
            return "slow_resource"

        self.loader.register_loader("slow", slow_loader)

        # Uruchom pierwsze ładowanie w osobnym wątku
        def load_first():
            return self.loader.get_resource("slow")

        thread1 = threading.Thread(target=load_first)
        thread1.start()

        # Poczekaj aż pierwsze ładowanie się zacznie
        loading_started.wait(timeout=5)

        # Próba drugiego ładowania (powinna zwrócić None)
        result = self.loader.get_resource("slow")
        self.assertIsNone(result)

        # Pozwól pierwszemu ładowaniu się zakończyć
        can_complete.set()
        thread1.join(timeout=5)


class TestAsyncResourceLoaderWithQt(unittest.TestCase):
    """Test klasy AsyncResourceLoader z Qt."""

    @classmethod
    def setUpClass(cls):
        """Przygotowanie aplikacji Qt."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        self.loader = AsyncResourceLoader(max_workers=2)
        self.signals_received = []

        # Połącz sygnały do śledzenia
        self.loader.progress_updated.connect(self._on_progress)
        self.loader.resource_loaded.connect(self._on_loaded)
        self.loader.loading_failed.connect(self._on_failed)
        self.loader.all_completed.connect(self._on_completed)

    def tearDown(self):
        """Czyszczenie po teście."""
        self.loader.cleanup()

    def _on_progress(self, resource_name, progress):
        self.signals_received.append(("progress", resource_name, progress))

    def _on_loaded(self, resource_name, resource):
        self.signals_received.append(("loaded", resource_name, resource))

    def _on_failed(self, resource_name, error):
        self.signals_received.append(("failed", resource_name, error))

    def _on_completed(self):
        self.signals_received.append(("completed",))

    def test_load_resource_async_success(self):
        """Should load resource asynchronously and emit signals."""

        def simple_loader():
            return {"data": "test"}

        self.loader.load_resource_async("test", simple_loader)

        # Poczekaj na zakończenie
        completed = self.loader.wait_for_completion(timeout=5)
        self.assertTrue(completed)

        # Sprawdź sygnały
        progress_signals = [s for s in self.signals_received if s[0] == "progress"]
        self.assertGreaterEqual(len(progress_signals), 2)  # 0% i 100%

        loaded_signals = [s for s in self.signals_received if s[0] == "loaded"]
        self.assertEqual(len(loaded_signals), 1)
        self.assertEqual(loaded_signals[0][1], "test")
        self.assertEqual(loaded_signals[0][2], {"data": "test"})

        completed_signals = [s for s in self.signals_received if s[0] == "completed"]
        self.assertEqual(len(completed_signals), 1)

    def test_load_resource_async_failure(self):
        """Should handle loader failure and emit error signal."""

        def failing_loader():
            raise ValueError("Loader failed")

        self.loader.load_resource_async("failing", failing_loader)

        # Poczekaj na zakończenie
        completed = self.loader.wait_for_completion(timeout=5)
        self.assertTrue(completed)

        # Sprawdź sygnały błędu
        failed_signals = [s for s in self.signals_received if s[0] == "failed"]
        self.assertEqual(len(failed_signals), 1)
        self.assertEqual(failed_signals[0][1], "failing")
        self.assertIn("Loader failed", failed_signals[0][2])

    def test_load_multiple_resources(self):
        """Should load multiple resources concurrently."""

        def loader1():
            time.sleep(0.1)
            return "resource1"

        def loader2():
            time.sleep(0.1)
            return "resource2"

        start_time = time.time()

        self.loader.load_resource_async("res1", loader1)
        self.loader.load_resource_async("res2", loader2)

        completed = self.loader.wait_for_completion(timeout=5)
        elapsed = time.time() - start_time

        self.assertTrue(completed)
        self.assertLess(elapsed, 0.3)  # Powinno być szybsze niż sekwencyjne ładowanie

        # Sprawdź że oba zasoby zostały załadowane
        loaded_signals = [s for s in self.signals_received if s[0] == "loaded"]
        self.assertEqual(len(loaded_signals), 2)

        resource_names = [s[1] for s in loaded_signals]
        self.assertIn("res1", resource_names)
        self.assertIn("res2", resource_names)

    def test_cancel_all(self):
        """Should cancel all pending tasks."""

        def slow_loader():
            time.sleep(1)
            return "slow"

        self.loader.load_resource_async("slow", slow_loader)

        # Anuluj natychmiast
        self.loader.cancel_all()

        # Sprawdź że zadania zostały anulowane
        self.assertEqual(len(self.loader.loading_tasks), 0)

    def test_duplicate_loading_warning(self):
        """Should warn about duplicate loading attempts."""

        def slow_loader():
            time.sleep(0.5)
            return "slow"

        # Pierwsze ładowanie
        self.loader.load_resource_async("duplicate", slow_loader)

        # Drugie ładowanie tego samego zasobu
        with patch("utils.performance_optimizer.logger") as mock_logger:
            self.loader.load_resource_async("duplicate", slow_loader)
            mock_logger.warning.assert_called_once()


class TestPerformanceMonitor(unittest.TestCase):
    """Test klasy PerformanceMonitor."""

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        self.monitor = PerformanceMonitor()

    def test_measure_execution_time_decorator(self):
        """Should measure and record execution time."""

        @self.monitor.measure_execution_time("test_operation")
        def test_function():
            time.sleep(0.1)
            return "result"

        result = test_function()

        self.assertEqual(result, "result")
        self.assertIn("test_operation", self.monitor.execution_times)

        times = self.monitor.execution_times["test_operation"]
        self.assertEqual(len(times), 1)
        self.assertGreater(times[0], 0.05)  # Powinno być co najmniej 50ms

    def test_performance_stats(self):
        """Should calculate correct performance statistics."""
        # Symuluj kilka wykonań
        for i in range(5):
            self.monitor._record_execution_time("test_op", 0.1 + i * 0.1)

        stats = self.monitor.get_performance_stats()

        self.assertIn("test_op", stats)
        op_stats = stats["test_op"]

        self.assertEqual(op_stats["count"], 5)
        self.assertEqual(op_stats["min_time"], 0.1)
        self.assertEqual(op_stats["max_time"], 0.5)
        self.assertAlmostEqual(op_stats["avg_time"], 0.3, places=2)
        self.assertAlmostEqual(op_stats["total_time"], 1.5, places=2)

    def test_slow_operation_warning(self):
        """Should warn about slow operations."""
        with patch("utils.performance_optimizer.logger") as mock_logger:
            self.monitor._record_execution_time("slow_op", 2.0)
            mock_logger.warning.assert_called_once()

    def test_execution_times_limit(self):
        """Should limit stored execution times to 100."""
        # Dodaj 150 pomiarów
        for i in range(150):
            self.monitor._record_execution_time("test_op", 0.1)

        times = self.monitor.execution_times["test_op"]
        self.assertEqual(len(times), 100)  # Powinno być ograniczone do 100

    def test_memory_snapshot(self):
        """Should take memory snapshot with correct data."""
        snapshot = self.monitor.take_memory_snapshot("test_label")

        self.assertIn("timestamp", snapshot)
        self.assertIn("label", snapshot)
        self.assertIn("rss_mb", snapshot)
        self.assertIn("vms_mb", snapshot)
        self.assertIn("memory_percent", snapshot)
        self.assertIn("gc_stats", snapshot)

        self.assertEqual(snapshot["label"], "test_label")
        self.assertIsInstance(snapshot["rss_mb"], float)
        self.assertGreater(snapshot["rss_mb"], 0)

    def test_memory_snapshots_limit(self):
        """Should limit stored snapshots to 50."""
        # Dodaj 60 snapshotów
        for i in range(60):
            self.monitor.take_memory_snapshot(f"snapshot_{i}")

        self.assertEqual(len(self.monitor.memory_snapshots), 50)

    def test_memory_usage_trend_insufficient_data(self):
        """Should handle insufficient data for trend analysis."""
        trend = self.monitor.get_memory_usage_trend()
        self.assertEqual(trend["trend"], "insufficient_data")

        # Jeden snapshot też nie wystarcza
        self.monitor.take_memory_snapshot("single")
        trend = self.monitor.get_memory_usage_trend()
        self.assertEqual(trend["trend"], "insufficient_data")

    def test_memory_usage_trend_analysis(self):
        """Should analyze memory usage trends correctly."""
        # Symuluj rosnące zużycie pamięci
        base_memory = 100.0
        for i in range(10):
            snapshot = {
                "timestamp": time.time() + i,
                "label": f"test_{i}",
                "rss_mb": base_memory + i * 2,  # Wzrost o 2MB na snapshot
                "vms_mb": base_memory + i * 2,
                "memory_percent": 50.0,
                "gc_stats": {},
            }
            self.monitor.memory_snapshots.append(snapshot)

        trend = self.monitor.get_memory_usage_trend()

        self.assertEqual(trend["trend"], "increasing")
        self.assertGreater(trend["trend_slope_mb"], 1)
        self.assertAlmostEqual(trend["avg_memory_mb"], 109.0, places=1)
        self.assertEqual(trend["max_memory_mb"], 118.0)
        self.assertEqual(trend["min_memory_mb"], 100.0)

    def test_force_garbage_collection(self):
        """Should force garbage collection and return stats."""
        # Stwórz kilka obiektów do zebrania
        objects = [[] for _ in range(100)]
        del objects

        gc_stats = self.monitor.force_garbage_collection()

        self.assertIn("objects_before", gc_stats)
        self.assertIn("objects_after", gc_stats)
        self.assertIn("objects_collected", gc_stats)
        self.assertIn("objects_freed", gc_stats)

        self.assertIsInstance(gc_stats["objects_collected"], int)

    def test_weak_reference_tracking(self):
        """Should track weak references for memory leak detection."""

        class TestClass:
            pass

        obj1 = TestClass()
        obj2 = TestClass()

        self.monitor.register_weak_reference(obj1)
        self.monitor.register_weak_reference(obj2)

        # Sprawdź żywe obiekty
        alive = self.monitor.check_memory_leaks()
        self.assertEqual(len(alive), 2)

        # Usuń jeden obiekt
        del obj1
        gc.collect()

        alive = self.monitor.check_memory_leaks()
        self.assertEqual(len(alive), 1)


class TestStartupOptimizer(unittest.TestCase):
    """Test klasy StartupOptimizer."""

    @classmethod
    def setUpClass(cls):
        """Przygotowanie aplikacji Qt."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        self.optimizer = StartupOptimizer()
        self.executed_tasks = []

    def test_defer_task_execution(self):
        """Should defer and execute tasks after delay."""

        def test_task():
            self.executed_tasks.append("task1")

        self.optimizer.defer_task(test_task, delay_ms=50)

        # Przed upływem czasu - zadanie nie wykonane
        self.assertEqual(len(self.executed_tasks), 0)

        # Symuluj upływ czasu
        QTest.qWait(100)

        # Po czasie - zadanie wykonane
        self.assertEqual(len(self.executed_tasks), 1)
        self.assertEqual(self.executed_tasks[0], "task1")

    def test_multiple_deferred_tasks(self):
        """Should execute multiple deferred tasks."""

        def task1():
            self.executed_tasks.append("task1")

        def task2():
            self.executed_tasks.append("task2")

        self.optimizer.defer_task(task1, delay_ms=50)
        self.optimizer.defer_task(task2, delay_ms=50)

        QTest.qWait(100)

        self.assertEqual(len(self.executed_tasks), 2)
        self.assertIn("task1", self.executed_tasks)
        self.assertIn("task2", self.executed_tasks)

    def test_task_exception_handling(self):
        """Should handle task exceptions gracefully."""

        def failing_task():
            raise ValueError("Task failed")

        def normal_task():
            self.executed_tasks.append("normal")

        with patch("utils.performance_optimizer.logger") as mock_logger:
            self.optimizer.defer_task(failing_task, delay_ms=50)
            self.optimizer.defer_task(normal_task, delay_ms=50)

            QTest.qWait(100)

            # Sprawdź że błąd został zalogowany
            mock_logger.error.assert_called_once()

        # Sprawdź że normalne zadanie zostało wykonane mimo błędu w pierwszym
        self.assertEqual(len(self.executed_tasks), 1)
        self.assertEqual(self.executed_tasks[0], "normal")


class TestHelperFunctions(unittest.TestCase):
    """Test funkcji pomocniczych."""

    def test_lazy_property_decorator(self):
        """Should create lazy properties that compute only once."""
        computation_count = 0

        class TestClass:
            @lazy_property
            def expensive_property(self):
                nonlocal computation_count
                computation_count += 1
                return f"computed_{computation_count}"

        obj = TestClass()

        # Pierwsze wywołanie
        result1 = obj.expensive_property
        self.assertEqual(result1, "computed_1")
        self.assertEqual(computation_count, 1)

        # Drugie wywołanie - powinno zwrócić cached wartość
        result2 = obj.expensive_property
        self.assertEqual(result2, "computed_1")
        self.assertEqual(computation_count, 1)  # Nie powinno liczyć ponownie

    def test_cached_file_reader_success(self):
        """Should read and cache file contents."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Pierwsze wywołanie
            content1 = cached_file_reader(temp_path)
            self.assertEqual(content1, "test content")

            # Drugie wywołanie - powinno zwrócić z cache
            content2 = cached_file_reader(temp_path)
            self.assertEqual(content2, "test content")

        finally:
            os.unlink(temp_path)

    def test_cached_file_reader_failure(self):
        """Should raise PerformanceError for missing files."""
        with self.assertRaises(PerformanceError) as cm:
            cached_file_reader("nonexistent_file.txt")

        self.assertIn("Failed to read file", str(cm.exception))

    def test_create_css_loader(self):
        """Should create CSS loader function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".css", delete=False) as f:
            f.write("body { color: red; }")
            temp_path = f.name

        try:
            loader = create_css_loader(temp_path)
            result = loader()
            self.assertEqual(result, "body { color: red; }")

        finally:
            os.unlink(temp_path)

    def test_create_translation_loader(self):
        """Should create translation loader function."""
        test_data = {"hello": "Cześć", "goodbye": "Do widzenia"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            loader = create_translation_loader(temp_path)
            result = loader()
            self.assertEqual(result, test_data)

        finally:
            os.unlink(temp_path)

    def test_create_config_loader(self):
        """Should create configuration loader function."""
        test_config = {"debug": True, "version": "1.0"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_config, f)
            temp_path = f.name

        try:
            loader = create_config_loader(temp_path)
            result = loader()
            self.assertEqual(result, test_config)

        finally:
            os.unlink(temp_path)


class TestDecorators(unittest.TestCase):
    """Test dekoratorów modułu."""

    @classmethod
    def setUpClass(cls):
        """Przygotowanie aplikacji Qt."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_defer_until_after_startup_decorator(self):
        """Should defer function execution until after startup."""
        executed_functions = []

        @defer_until_after_startup(delay_ms=50)
        def deferred_function(name):
            executed_functions.append(name)

        # Wywołaj funkcję
        deferred_function("test1")
        deferred_function("test2")

        # Przed upływem czasu - funkcje nie wykonane
        self.assertEqual(len(executed_functions), 0)

        # Poczekaj na wykonanie
        QTest.qWait(100)

        # Po czasie - funkcje wykonane
        self.assertEqual(len(executed_functions), 2)
        self.assertIn("test1", executed_functions)
        self.assertIn("test2", executed_functions)


class TestGlobalInstances(unittest.TestCase):
    """Test globalnych instancji modułu."""

    def test_global_lazy_loader_instance(self):
        """Should have working global lazy_loader instance."""

        def test_loader():
            return "global_test"

        lazy_loader.register_loader("global_test", test_loader)
        result = lazy_loader.get_resource("global_test")

        self.assertEqual(result, "global_test")

    def test_global_performance_monitor_instance(self):
        """Should have working global performance_monitor instance."""

        @performance_monitor.measure_execution_time("global_test")
        def test_function():
            return "monitored"

        result = test_function()

        self.assertEqual(result, "monitored")
        self.assertIn("global_test", performance_monitor.execution_times)

    def test_global_startup_optimizer_instance(self):
        """Should have working global startup_optimizer instance."""
        executed = []

        def test_task():
            executed.append("global")

        startup_optimizer.defer_task(test_task, delay_ms=50)

        if QApplication.instance():
            QTest.qWait(100)
            self.assertEqual(len(executed), 1)


class TestErrorHandling(unittest.TestCase):
    """Test obsługi błędów w module."""

    def test_performance_error_creation(self):
        """Should create PerformanceError with correct attributes."""
        error = PerformanceError("Test error", operation="test_op")

        self.assertEqual(error.error_code, ErrorCode.PERFORMANCE)
        self.assertEqual(error.operation, "test_op")
        self.assertIn("operation", error.details)

    def test_lazy_loader_timeout_handling(self):
        """Should handle timeout in lazy loader gracefully."""
        loader = LazyLoader()

        def slow_loader():
            time.sleep(2)  # Dłuższa niż timeout
            return "slow"

        loader.register_loader("slow", slow_loader)

        # Test z krótkim timeoutem - w rzeczywistości LazyLoader nie implementuje timeoutu
        # ale testujemy czy nie powoduje wiszenia
        start_time = time.time()
        result = loader.get_resource("slow")
        elapsed = time.time() - start_time

        # Powinno się zakończyć (bez timeoutu wynosi 2+ sekundy)
        self.assertGreater(elapsed, 1.5)
        self.assertEqual(result, "slow")

    @patch("utils.performance_optimizer.psutil.Process")
    def test_memory_snapshot_failure_handling(self, mock_process):
        """Should handle memory snapshot failures gracefully."""
        mock_process.side_effect = Exception("Process access denied")

        monitor = PerformanceMonitor()

        with patch("utils.performance_optimizer.logger") as mock_logger:
            snapshot = monitor.take_memory_snapshot("error_test")

            # Powinno zwrócić pusty dict i zalogować błąd
            self.assertEqual(snapshot, {})
            mock_logger.error.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Testy integracyjne różnych komponentów."""

    @classmethod
    def setUpClass(cls):
        """Przygotowanie aplikacji Qt."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_performance_monitoring_with_lazy_loading(self):
        """Should monitor performance of lazy loading operations."""
        loader = LazyLoader()
        monitor = PerformanceMonitor()

        @monitor.measure_execution_time("lazy_load_test")
        def measured_get_resource(resource_name):
            return loader.get_resource(resource_name)

        def expensive_loader():
            time.sleep(0.1)
            return "expensive_resource"

        loader.register_loader("expensive", expensive_loader)

        # Wywołaj monitorowane lazy loading
        result = measured_get_resource("expensive")

        self.assertEqual(result, "expensive_resource")

        # Sprawdź że został zarejestrowany pomiar
        stats = monitor.get_performance_stats()
        self.assertIn("lazy_load_test", stats)
        self.assertGreater(stats["lazy_load_test"]["avg_time"], 0.05)

    def test_async_loading_with_startup_optimization(self):
        """Should combine async loading with startup optimization."""
        loader = AsyncResourceLoader(max_workers=2)
        optimizer = StartupOptimizer()

        loaded_resources = {}

        def resource_loader():
            time.sleep(0.1)
            return {"async": "data"}

        def deferred_async_load():
            loader.load_resource_async("deferred", resource_loader)

        # Załóż ładowanie na później
        optimizer.defer_task(deferred_async_load, delay_ms=50)

        # Poczekaj na wykonanie odroczonego zadania
        QTest.qWait(100)

        # Poczekaj na zakończenie async loading
        completed = loader.wait_for_completion(timeout=5)
        self.assertTrue(completed)

        loader.cleanup()


if __name__ == "__main__":
    # Uruchom testy z verbose output
    unittest.main(verbosity=2)
