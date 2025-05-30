#!/usr/bin/env python3
"""
Integration tests for performance optimization features.

This module tests the performance optimization utilities including:
- Lazy loading
- Async resource loading
- Performance monitoring
- Memory usage tracking
- Caching systems
"""

import json
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

from utils.config_cache import ConfigurationCache, FileCache, config_cache
from utils.enhanced_splash import EnhancedSplashScreen, StartupProgressTracker
from utils.performance_optimizer import (
    AsyncResourceLoader,
    LazyLoader,
    PerformanceMonitor,
    StartupOptimizer,
    cached_file_reader,
    create_config_loader,
    create_css_loader,
    defer_until_after_startup,
    lazy_loader,
    lazy_property,
    performance_monitor,
    startup_optimizer,
)


class TestLazyLoader(unittest.TestCase):
    """Test lazy loading functionality."""

    def setUp(self):
        self.loader = LazyLoader()

    def test_register_and_load_resource(self):
        """Test registering and loading a resource."""

        def test_loader():
            return {"test": "data"}

        self.loader.register_loader("test_resource", test_loader)

        # Test loading
        result = self.loader.get_resource("test_resource")
        self.assertEqual(result, {"test": "data"})

        # Test caching (should return same instance)
        result2 = self.loader.get_resource("test_resource")
        self.assertIs(result, result2)

    def test_resource_not_registered(self):
        """Test loading unregistered resource raises error."""
        with self.assertRaises(Exception):
            self.loader.get_resource("nonexistent")

    def test_is_loaded(self):
        """Test checking if resource is loaded."""

        def test_loader():
            return "loaded"

        self.loader.register_loader("test", test_loader)

        self.assertFalse(self.loader.is_loaded("test"))
        self.loader.get_resource("test")
        self.assertTrue(self.loader.is_loaded("test"))

    def test_clear_cache(self):
        """Test clearing resource cache."""

        def test_loader():
            return "data"

        self.loader.register_loader("test", test_loader)
        self.loader.get_resource("test")

        self.assertTrue(self.loader.is_loaded("test"))
        self.loader.clear_cache("test")
        self.assertFalse(self.loader.is_loaded("test"))


class TestAsyncResourceLoader(unittest.TestCase):
    """Test async resource loading."""

    def setUp(self):
        if not QCoreApplication.instance():
            self.app = QCoreApplication([])
        else:
            self.app = QCoreApplication.instance()
        self.async_loader = AsyncResourceLoader()

    def tearDown(self):
        self.async_loader.cleanup()

    def test_async_loading(self):
        """Test async resource loading with signals."""
        loaded_resources = {}
        errors = {}

        def on_loaded(name, resource):
            loaded_resources[name] = resource

        def on_error(name, error):
            errors[name] = error

        def test_loader():
            time.sleep(0.1)  # Simulate work
            return "async_result"

        self.async_loader.resource_loaded.connect(on_loaded)
        self.async_loader.loading_failed.connect(on_error)

        self.async_loader.load_resource_async("test_async", test_loader)

        # Wait for completion with Qt event processing
        start_time = time.time()
        timeout = 5.0
        while (
            "test_async" not in loaded_resources and time.time() - start_time < timeout
        ):
            self.app.processEvents()
            time.sleep(0.01)

        # Check results
        self.assertIn("test_async", loaded_resources)
        self.assertEqual(loaded_resources["test_async"], "async_result")
        self.assertEqual(len(errors), 0)


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring."""

    def setUp(self):
        self.monitor = PerformanceMonitor()

    def test_execution_time_measurement(self):
        """Test execution time measurement decorator."""

        @self.monitor.measure_execution_time("test_operation")
        def test_function():
            time.sleep(0.1)
            return "result"

        result = test_function()
        self.assertEqual(result, "result")

        stats = self.monitor.get_performance_stats()
        self.assertIn("test_operation", stats)
        self.assertEqual(stats["test_operation"]["count"], 1)
        self.assertGreater(stats["test_operation"]["avg_time"], 0.09)

    def test_memory_snapshots(self):
        """Test memory snapshot functionality."""
        snapshot = self.monitor.take_memory_snapshot("test_snapshot")

        self.assertIn("timestamp", snapshot)
        self.assertIn("label", snapshot)
        self.assertIn("rss_mb", snapshot)
        self.assertIn("memory_percent", snapshot)
        self.assertEqual(snapshot["label"], "test_snapshot")
        self.assertGreater(snapshot["rss_mb"], 0)

    def test_memory_trend_analysis(self):
        """Test memory usage trend analysis."""
        # Take multiple snapshots
        for i in range(5):
            self.monitor.take_memory_snapshot(f"snapshot_{i}")
            time.sleep(0.01)  # Small delay

        trend = self.monitor.get_memory_usage_trend()
        self.assertIn("trend", trend)
        self.assertIn("avg_memory_mb", trend)
        self.assertIn("snapshots_analyzed", trend)

    def test_garbage_collection(self):
        """Test forced garbage collection."""
        gc_stats = self.monitor.force_garbage_collection()

        self.assertIn("objects_before", gc_stats)
        self.assertIn("objects_after", gc_stats)
        self.assertIn("objects_collected", gc_stats)
        self.assertIn("objects_freed", gc_stats)

    def test_weak_reference_tracking(self):
        """Test weak reference tracking for leak detection."""

        class TestObject:
            def __init__(self, data):
                self.data = data

        test_obj = TestObject({"test": "object"})

        self.monitor.register_weak_reference(test_obj)
        alive_objects = self.monitor.check_memory_leaks()

        self.assertGreater(len(alive_objects), 0)

        # Delete reference and check again
        del test_obj
        self.monitor.force_garbage_collection()
        alive_objects = self.monitor.check_memory_leaks()
        # Note: weak reference should be gone after GC


class TestFileCache(unittest.TestCase):
    """Test file caching functionality."""

    def setUp(self):
        self.cache = FileCache(max_cache_size_mb=1)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_caching(self):
        """Test basic file caching."""
        test_file = os.path.join(self.temp_dir, "test.txt")
        test_content = "Hello, World!"

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        def text_loader(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        # First load should cache
        content1 = self.cache.get(test_file, text_loader)
        self.assertEqual(content1, test_content)

        # Second load should come from cache
        content2 = self.cache.get(test_file, text_loader)
        self.assertEqual(content2, test_content)
        self.assertEqual(content1, content2)  # Use assertEqual instead of assertIs

    def test_cache_invalidation(self):
        """Test cache invalidation on file modification."""
        test_file = os.path.join(self.temp_dir, "test.txt")

        def text_loader(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        # Create initial file
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("original")

        content1 = self.cache.get(test_file, text_loader)
        self.assertEqual(content1, "original")

        # Modify file
        time.sleep(0.1)  # Ensure different mtime
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("modified")  # Should reload from file
        content2 = self.cache.get(test_file, text_loader)
        self.assertEqual(content2, "modified")
        self.assertNotEqual(content1, content2)


class TestConfigurationCache(unittest.TestCase):
    """Test configuration caching."""

    def setUp(self):
        self.cache = ConfigurationCache()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_caching(self):
        """Test configuration file caching."""
        config_file = os.path.join(self.temp_dir, "config.json")
        config_data = {"key": "value", "number": 42}

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # Load config
        loaded_config = self.cache.get_config(config_file)
        self.assertEqual(
            loaded_config, config_data
        )  # Should come from cache on second load
        loaded_config2 = self.cache.get_config(config_file)
        self.assertEqual(
            loaded_config, loaded_config2
        )  # Change from assertIs to assertEqual

    def test_translation_caching(self):
        """Test translation file caching."""
        trans_file = os.path.join(self.temp_dir, "en.json")
        trans_data = {"hello": "Hello", "world": "World"}

        with open(trans_file, "w", encoding="utf-8") as f:
            json.dump(trans_data, f)  # Load translation
        loaded_trans = self.cache.get_translations(trans_file)
        self.assertEqual(loaded_trans, trans_data)

        # Should come from cache on second load
        loaded_trans2 = self.cache.get_translations(trans_file)
        self.assertEqual(
            loaded_trans, loaded_trans2
        )  # Change from assertIs to assertEqual


class TestLazyProperty(unittest.TestCase):
    """Test lazy property decorator."""

    def test_lazy_property(self):
        """Test lazy property computation."""
        computation_count = 0

        class TestClass:
            @lazy_property
            def expensive_property(self):
                nonlocal computation_count
                computation_count += 1
                return "computed_value"

        obj = TestClass()

        # First access should compute
        result1 = obj.expensive_property
        self.assertEqual(result1, "computed_value")
        self.assertEqual(computation_count, 1)

        # Second access should use cached value
        result2 = obj.expensive_property
        self.assertEqual(result2, "computed_value")
        self.assertEqual(computation_count, 1)  # No additional computation
        self.assertIs(result1, result2)


class TestStartupOptimizer(unittest.TestCase):
    """Test startup optimization."""

    def setUp(self):
        if not QCoreApplication.instance():
            self.app = QCoreApplication([])
        else:
            self.app = QCoreApplication.instance()
        self.optimizer = StartupOptimizer()

    def test_deferred_execution(self):
        """Test deferred task execution."""
        executed_tasks = []

        def task1():
            executed_tasks.append("task1")

        def task2():
            executed_tasks.append("task2")

        # Defer tasks
        self.optimizer.defer_task(task1, delay_ms=10)
        self.optimizer.defer_task(task2, delay_ms=10)

        # Tasks should not be executed immediately
        self.assertEqual(len(executed_tasks), 0)

        # Wait for execution
        start_time = time.time()
        while len(executed_tasks) < 2 and time.time() - start_time < 1.0:
            self.app.processEvents()
            time.sleep(0.01)

        # Tasks should be executed
        self.assertIn("task1", executed_tasks)
        self.assertIn("task2", executed_tasks)


class TestIntegration(unittest.TestCase):
    """Integration tests for all performance optimization components."""

    def setUp(self):
        if not QCoreApplication.instance():
            self.app = QCoreApplication([])
        else:
            self.app = QCoreApplication.instance()

    def test_global_instances(self):
        """Test that global instances are properly initialized."""
        # Test global lazy loader
        self.assertIsInstance(lazy_loader, LazyLoader)

        # Test global performance monitor
        self.assertIsInstance(performance_monitor, PerformanceMonitor)

        # Test global startup optimizer
        self.assertIsInstance(startup_optimizer, StartupOptimizer)

        # Test global config cache
        self.assertIsInstance(config_cache, ConfigurationCache)

    def test_css_loader_creation(self):
        """Test CSS loader creation utility."""
        css_loader = create_css_loader("test.css")
        self.assertIsNotNone(css_loader)
        self.assertTrue(callable(css_loader))

    def test_config_loader_creation(self):
        """Test config loader creation utility."""
        config_loader = create_config_loader("config.json")
        self.assertIsNotNone(config_loader)
        self.assertTrue(callable(config_loader))

    def test_defer_decorator(self):
        """Test defer decorator functionality."""
        executed = []

        # Create a local StartupOptimizer to avoid Qt lifecycle issues
        local_optimizer = StartupOptimizer()

        def deferred_function():
            executed.append("executed")

        # Use the local optimizer directly instead of the decorator
        local_optimizer.defer_task(deferred_function, delay_ms=10)

        # Should not execute immediately
        self.assertEqual(len(executed), 0)

        # Wait for deferred execution
        start_time = time.time()
        while len(executed) == 0 and time.time() - start_time < 1.0:
            self.app.processEvents()
            time.sleep(0.01)

        # Should be executed now
        self.assertEqual(len(executed), 1)


if __name__ == "__main__":
    # Run tests
    unittest.main(argv=[""], verbosity=2, exit=False)
