"""
Benchmark tests dla modułu utils.performance_optimizer.

Ten moduł zawiera testy wydajnościowe dla:
- LazyLoader
- AsyncResourceLoader
- PerformanceMonitor
- StartupOptimizer
"""

import gc
import json
import os
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, Mock, patch

import psutil
from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from utils.exceptions import PerformanceError
from utils.performance_optimizer import (
    AsyncResourceLoader,
    LazyLoader,
    PerformanceMonitor,
    StartupOptimizer,
    cached_file_reader,
    create_config_loader,
    create_css_loader,
    lazy_loader,
    lazy_property,
    performance_monitor,
    startup_optimizer,
)


class TestLazyLoaderBenchmark(unittest.TestCase):
    """Testy benchmark dla LazyLoader."""

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        # Oczyść GC przed benchmarkiem
        gc.collect()
        self.loader = LazyLoader()

    def test_lazy_loader_memory_usage(self):
        """Test zużycia pamięci przez LazyLoader."""
        # Zarejestruj dużą liczbę loaderów
        for i in range(100):
            resource_name = f"resource_{i}"
            self.loader.register_loader(resource_name, lambda i=i: f"data_{i}")

        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Załaduj wszystkie zasoby
        for i in range(100):
            resource_name = f"resource_{i}"
            self.loader.get_resource(resource_name)

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = memory_after - memory_before

        print(f"LazyLoader memory usage for 100 resources: {memory_diff:.2f} MB")
        self.assertLess(
            memory_diff, 10.0, "Zużycie pamięci powinno być mniejsze niż 10MB"
        )

    def test_lazy_loader_performance(self):
        """Test wydajności LazyLoader."""
        # Utwórz i zarejestruj 100 loaderów
        for i in range(100):
            # Symuluj różne czasy ładowania
            delay = 0.001 * (i % 5)  # 0 do 0.004 sekundy
            self.loader.register_loader(
                f"resource_{i}", lambda delay=delay: time.sleep(delay) or f"data"
            )

        # Mierz czas dostępu do zasobów
        start_time = time.time()

        # Dostęp sekwencyjny
        for i in range(100):
            self.loader.get_resource(f"resource_{i}")

        # Drugi dostęp powinien być z cache (szybszy)
        second_start = time.time()
        for i in range(100):
            self.loader.get_resource(f"resource_{i}")

        first_load_time = second_start - start_time
        second_load_time = time.time() - second_start

        print(f"LazyLoader pierwszego dostępu: {first_load_time:.4f}s")
        print(f"LazyLoader dostępu z cache: {second_load_time:.4f}s")

        # Drugi dostęp powinien być co najmniej 10x szybszy (z cache)
        self.assertLess(
            second_load_time,
            first_load_time / 10,
            "Dostęp z cache powinien być co najmniej 10x szybszy",
        )


class TestAsyncResourceLoaderBenchmark(unittest.TestCase):
    """Testy benchmark dla AsyncResourceLoader."""

    @classmethod
    def setUpClass(cls):
        """Przygotowanie aplikacji Qt."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        # Oczyść GC przed benchmarkiem
        gc.collect()
        self.loader = AsyncResourceLoader(max_workers=4)

    def tearDown(self):
        """Czyszczenie po teście."""
        self.loader.cleanup()

    def test_async_loader_concurrency(self):
        """Test wydajności równoległego ładowania."""

        # Utwórz 20 zasobów z opóźnieniem 0.1s każdy
        def slow_loader(i):
            time.sleep(0.1)
            return f"resource_{i}"

        # Mierz czas sekwencyjnego ładowania
        seq_start = time.time()
        for i in range(20):
            slow_loader(i)
        seq_time = time.time() - seq_start

        # Teraz równolegle z AsyncResourceLoader
        async_start = time.time()
        for i in range(20):
            self.loader.load_resource_async(f"res_{i}", lambda i=i: slow_loader(i))

        # Poczekaj na zakończenie wszystkich zadań
        self.loader.wait_for_completion(timeout=10)
        async_time = time.time() - async_start

        print(f"Sekwencyjne ładowanie 20 zasobów: {seq_time:.4f}s")
        print(f"Asynchroniczne ładowanie 20 zasobów: {async_time:.4f}s")
        print(f"Przyspieszenie: {seq_time / async_time:.2f}x")

        # Przy 4 wątkach powinniśmy osiągnąć przyspieszenie co najmniej 2x
        self.assertLess(
            async_time,
            seq_time / 2,
            "Równoległe ładowanie powinno być co najmniej 2x szybsze",
        )

    def test_async_loader_memory_usage(self):
        """Test zużycia pamięci podczas równoległego ładowania."""
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Załaduj 50 zasobów równolegle
        for i in range(50):
            self.loader.load_resource_async(
                f"res_{i}", lambda i=i: [f"data_{j}" for j in range(1000)]
            )

        # Poczekaj na zakończenie
        self.loader.wait_for_completion(timeout=10)

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = memory_after - memory_before

        print(f"AsyncResourceLoader pamięć dla 50 zasobów: {memory_diff:.2f} MB")
        self.assertLess(
            memory_diff, 50.0, "Zużycie pamięci powinno być mniejsze niż 50MB"
        )


class TestPerformanceMonitorBenchmark(unittest.TestCase):
    """Testy benchmark dla PerformanceMonitor."""

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        # Oczyść GC przed benchmarkiem
        gc.collect()
        self.monitor = PerformanceMonitor()

    def test_monitor_memory_snapshots(self):
        """Test wydajności robienia memory snapshots."""
        snapshots_count = 100

        # Zmierz czas wykonania wielu snapshotów
        start_time = time.time()
        for i in range(snapshots_count):
            self.monitor.take_memory_snapshot(f"snapshot_{i}")
        total_time = time.time() - start_time

        print(f"Czas wykonania {snapshots_count} memory snapshots: {total_time:.4f}s")
        print(f"Średni czas na snapshot: {total_time/snapshots_count*1000:.2f}ms")

        # Każdy snapshot powinien zajmować mniej niż 10ms
        self.assertLess(
            total_time / snapshots_count,
            0.01,
            "Pojedynczy snapshot powinien trwać < 10ms",
        )

    def test_gc_collection_performance(self):
        """Test wydajności garbage collection."""
        # Utwórz wiele obiektów do zebrania
        objects = []
        for i in range(10000):
            objects.append({"data": f"temp_{i}", "more": [1, 2, 3, 4, 5]})

        # Usuń referencje
        objects = None

        # Zmierz czas GC
        start_time = time.time()
        stats = self.monitor.force_garbage_collection()
        gc_time = time.time() - start_time

        print(f"Czas wykonania force_garbage_collection: {gc_time:.4f}s")
        print(f"Zebrane obiekty: {stats['objects_collected']}")
        print(f"Zwolnione obiekty: {stats['objects_freed']}")

        # GC nie powinien zajmować więcej niż 0.5s
        self.assertLess(gc_time, 0.5, "Garbage collection powinno trwać < 0.5s")


class TestStartupOptimizerBenchmark(unittest.TestCase):
    """Testy benchmark dla StartupOptimizer."""

    @classmethod
    def setUpClass(cls):
        """Przygotowanie aplikacji Qt."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        # Oczyść GC przed benchmarkiem
        gc.collect()
        self.optimizer = StartupOptimizer()
        self.task_completed = threading.Event()

    def test_deferred_tasks_overhead(self):
        """Test narzutu czasowego dla odroczonych zadań."""
        task_count = 100
        executed_count = 0

        def simple_task():
            nonlocal executed_count
            executed_count += 1
            if executed_count >= task_count:
                self.task_completed.set()

        # Zmierz czas rejestracji zadań
        start_time = time.time()
        for i in range(task_count):
            self.optimizer.defer_task(simple_task, delay_ms=10)
        registration_time = time.time() - start_time

        # Poczekaj na wykonanie wszystkich zadań
        self.task_completed.wait(timeout=5)

        print(
            f"Czas rejestracji {task_count} odroczonych zadań: {registration_time:.4f}s"
        )
        print(f"Średni czas na zadanie: {registration_time*1000/task_count:.2f}μs")

        # Rejestracja zadania powinna być bardzo szybka (<10μs na zadanie)
        self.assertLess(
            registration_time / task_count,
            0.00001,
            "Rejestracja zadania powinna trwać < 10μs",
        )

        # Wszystkie zadania powinny zostać wykonane
        self.assertEqual(executed_count, task_count)


class TestCachedFileReaderBenchmark(unittest.TestCase):
    """Testy benchmark dla cached_file_reader."""

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        # Utwórz tymczasowy plik do testów
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w")
        # Zapisz 100KB danych do pliku
        data = "x" * 1024  # 1KB string
        for i in range(100):
            self.temp_file.write(data)
        self.temp_file.close()

    def tearDown(self):
        """Czyszczenie po teście."""
        # Usuń tymczasowy plik
        os.unlink(self.temp_file.name)

    def test_file_reader_caching(self):
        """Test wydajności cache dla odczytywania plików."""
        # Pierwszy odczyt (brak cache)
        start_time = time.time()
        content1 = cached_file_reader(self.temp_file.name)
        first_read_time = time.time() - start_time

        # Drugi odczyt (z cache)
        start_time = time.time()
        content2 = cached_file_reader(self.temp_file.name)
        cached_read_time = time.time() - start_time

        # Bezpośredni odczyt dla porównania
        start_time = time.time()
        with open(self.temp_file.name, "r") as f:
            direct_content = f.read()
        direct_read_time = time.time() - start_time

        print(f"Czas pierwszego odczytu (100KB): {first_read_time:.6f}s")
        print(f"Czas odczytu z cache: {cached_read_time:.6f}s")
        print(f"Czas bezpośredniego odczytu: {direct_read_time:.6f}s")
        print(
            f"Przyspieszenie cache vs. pierwszy odczyt: {first_read_time/cached_read_time:.1f}x"
        )
        print(
            f"Przyspieszenie cache vs. bezpośredni odczyt: {direct_read_time/cached_read_time:.1f}x"
        )

        # Cache powinien być co najmniej 100x szybszy od bezpośredniego odczytu
        self.assertLess(
            cached_read_time,
            direct_read_time / 100,
            "Odczyt z cache powinien być co najmniej 100x szybszy",
        )

        # Zawartość powinna być identyczna
        self.assertEqual(content1, content2)
        self.assertEqual(content1, direct_content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
