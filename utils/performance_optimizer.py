"""
Performance optimization utilities for CFAB UI Manager.

This module provides lazy loading, caching, and async resource loading capabilities
to improve application startup time and runtime performance.
"""

import asyncio
import gc
import logging
import os
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Set

import psutil
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from utils.exceptions import PerformanceError, handle_error_gracefully

logger = logging.getLogger(__name__)


class LazyLoader:
    """
    Lazy loading utility for expensive operations.

    Delays initialization of resources until they are actually needed,
    improving startup time and memory usage.
    """

    def __init__(self):
        self._loaded_resources: Dict[str, Any] = {}
        self._loaders: Dict[str, Callable] = {}
        self._loading_flags: Set[str] = set()
        self._lock = threading.Lock()

    def register_loader(self, resource_name: str, loader_func: Callable) -> None:
        """Register a lazy loader function for a resource."""
        with self._lock:
            self._loaders[resource_name] = loader_func
            logger.debug(f"Registered lazy loader for: {resource_name}")

    @handle_error_gracefully
    def get_resource(self, resource_name: str, timeout: float = 10.0) -> Any:
        """Get a resource, loading it lazily if needed."""
        with self._lock:
            # Return if already loaded
            if resource_name in self._loaded_resources:
                return self._loaded_resources[resource_name]

            # Check if loader is registered
            if resource_name not in self._loaders:
                raise PerformanceError(
                    f"No loader registered for resource: {resource_name}"
                )

            # Prevent concurrent loading
            if resource_name in self._loading_flags:
                logger.warning(f"Resource {resource_name} is already being loaded")
                return None

            self._loading_flags.add(resource_name)

        try:
            start_time = time.time()
            logger.debug(f"Lazy loading resource: {resource_name}")

            # Load the resource
            loader_func = self._loaders[resource_name]
            resource = loader_func()

            # Store the loaded resource
            with self._lock:
                self._loaded_resources[resource_name] = resource
                self._loading_flags.discard(resource_name)

            elapsed = time.time() - start_time
            logger.debug(f"Successfully loaded {resource_name} in {elapsed:.2f}s")
            return resource

        except Exception as e:
            with self._lock:
                self._loading_flags.discard(resource_name)
            logger.error(f"Failed to load resource {resource_name}: {e}")
            raise PerformanceError(f"Failed to load resource {resource_name}: {e}")

    def is_loaded(self, resource_name: str) -> bool:
        """Check if a resource is already loaded."""
        with self._lock:
            return resource_name in self._loaded_resources

    def clear_cache(self, resource_name: Optional[str] = None) -> None:
        """Clear cached resources."""
        with self._lock:
            if resource_name:
                self._loaded_resources.pop(resource_name, None)
                logger.debug(f"Cleared cache for: {resource_name}")
            else:
                self._loaded_resources.clear()
                logger.debug("Cleared all resource cache")


class AsyncResourceLoader(QObject):
    """
    Asynchronous resource loader with progress reporting.

    Loads resources in background threads while providing progress updates
    and completion notifications through Qt signals.
    """

    progress_updated = pyqtSignal(str, int)  # resource_name, progress_percentage
    resource_loaded = pyqtSignal(str, object)  # resource_name, resource_data
    loading_failed = pyqtSignal(str, str)  # resource_name, error_message
    all_completed = pyqtSignal()

    def __init__(self, max_workers: int = 4):
        super().__init__()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loading_tasks: Dict[str, Any] = {}
        self.completed_tasks = 0
        self.total_tasks = 0
        self._lock = threading.Lock()

    @handle_error_gracefully
    def load_resource_async(
        self, resource_name: str, loader_func: Callable, *args, **kwargs
    ) -> None:
        """Load a resource asynchronously."""
        with self._lock:
            if resource_name in self.loading_tasks:
                logger.warning(f"Resource {resource_name} is already being loaded")
                return

            self.total_tasks += 1

        logger.debug(f"Starting async load for: {resource_name}")

        def _load_wrapper():
            try:
                self.progress_updated.emit(resource_name, 0)

                # Load the resource
                resource = loader_func(*args, **kwargs)

                self.progress_updated.emit(resource_name, 100)
                self.resource_loaded.emit(resource_name, resource)

                with self._lock:
                    self.completed_tasks += 1
                    self.loading_tasks.pop(resource_name, None)

                    if self.completed_tasks >= self.total_tasks:
                        self.all_completed.emit()

                logger.debug(f"Successfully loaded async resource: {resource_name}")

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Failed to load async resource {resource_name}: {error_msg}"
                )
                self.loading_failed.emit(resource_name, error_msg)

                with self._lock:
                    self.completed_tasks += 1
                    self.loading_tasks.pop(resource_name, None)

        # Submit the task
        future = self.executor.submit(_load_wrapper)
        with self._lock:
            self.loading_tasks[resource_name] = future

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all loading tasks to complete."""
        try:
            # Wait for all futures to complete
            futures = list(self.loading_tasks.values())
            if futures:
                for future in futures:
                    future.result(timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Error waiting for resource loading completion: {e}")
            return False

    def cancel_all(self) -> None:
        """Cancel all pending loading tasks."""
        with self._lock:
            for future in self.loading_tasks.values():
                future.cancel()
            self.loading_tasks.clear()
            logger.debug("Cancelled all async loading tasks")

    def cleanup(self) -> None:
        """Clean up the executor and cancel pending tasks."""
        self.cancel_all()
        self.executor.shutdown(wait=False)
        logger.debug("AsyncResourceLoader cleaned up")


class PerformanceMonitor:
    """
    Performance monitoring and optimization utilities.

    Tracks execution times, memory usage, and provides optimization suggestions.
    """

    def __init__(self):
        self.execution_times: Dict[str, List[float]] = {}
        self.memory_snapshots: List[Dict] = []
        self._weak_refs: Set[weakref.ref] = set()

    def measure_execution_time(self, operation_name: str):
        """Decorator to measure execution time of functions."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.time() - start_time
                    self._record_execution_time(operation_name, elapsed)

            return wrapper

        return decorator

    def _record_execution_time(self, operation_name: str, elapsed_time: float) -> None:
        """Record execution time for an operation."""
        if operation_name not in self.execution_times:
            self.execution_times[operation_name] = []

        self.execution_times[operation_name].append(elapsed_time)

        # Keep only last 100 measurements
        if len(self.execution_times[operation_name]) > 100:
            self.execution_times[operation_name] = self.execution_times[operation_name][
                -100:
            ]

        # Log slow operations
        if elapsed_time > 1.0:
            logger.warning(
                f"Slow operation detected: {operation_name} took {elapsed_time:.2f}s"
            )

    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all monitored operations."""
        stats = {}
        for operation, times in self.execution_times.items():
            if times:
                stats[operation] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "total_time": sum(times),
                }
        return stats

    def register_weak_reference(self, obj: Any) -> None:
        """Register an object for memory leak detection."""

        def cleanup_callback(ref):
            self._weak_refs.discard(ref)

        weak_ref = weakref.ref(obj, cleanup_callback)
        self._weak_refs.add(weak_ref)

    def check_memory_leaks(self) -> List[str]:
        """Check for potential memory leaks."""
        alive_objects = []
        for ref in list(self._weak_refs):
            obj = ref()
            if obj is not None:
                alive_objects.append(str(type(obj)))

        return alive_objects

    def take_memory_snapshot(self, label: str = "") -> Dict[str, Any]:
        """Take a snapshot of current memory usage."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            snapshot = {
                "timestamp": time.time(),
                "label": label,
                "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
                "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
                "memory_percent": memory_percent,
                "gc_stats": {
                    "collected_objects": len([obj for obj in gc.get_objects()]),
                    "collections": gc.get_stats(),
                },
            }

            self.memory_snapshots.append(snapshot)

            # Keep only last 50 snapshots
            if len(self.memory_snapshots) > 50:
                self.memory_snapshots = self.memory_snapshots[-50:]

            logger.debug(
                f"Memory snapshot '{label}': {snapshot['rss_mb']:.1f}MB RSS, {memory_percent:.1f}%"
            )
            return snapshot

        except Exception as e:
            logger.error(f"Failed to take memory snapshot: {e}")
            return {}

    def get_memory_usage_trend(self) -> Dict[str, Any]:
        """Analyze memory usage trends from snapshots."""
        if len(self.memory_snapshots) < 2:
            return {"trend": "insufficient_data"}

        snapshots = self.memory_snapshots[-10:]  # Last 10 snapshots
        rss_values = [s["rss_mb"] for s in snapshots]

        # Calculate trend
        if len(rss_values) >= 2:
            trend_slope = (rss_values[-1] - rss_values[0]) / len(rss_values)
            avg_memory = sum(rss_values) / len(rss_values)
            max_memory = max(rss_values)
            min_memory = min(rss_values)

            trend_analysis = {
                "trend": (
                    "increasing"
                    if trend_slope > 1
                    else "stable" if abs(trend_slope) <= 1 else "decreasing"
                ),
                "trend_slope_mb": trend_slope,
                "avg_memory_mb": avg_memory,
                "max_memory_mb": max_memory,
                "min_memory_mb": min_memory,
                "memory_range_mb": max_memory - min_memory,
                "snapshots_analyzed": len(rss_values),
            }

            # Warning for high memory usage
            if trend_slope > 5:  # More than 5MB increase per snapshot
                logger.warning(
                    f"Memory usage increasing rapidly: {trend_slope:.1f}MB per snapshot"
                )

            return trend_analysis

        return {"trend": "insufficient_data"}

    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return statistics."""
        before_count = len(gc.get_objects())
        collected = gc.collect()
        after_count = len(gc.get_objects())

        gc_stats = {
            "objects_before": before_count,
            "objects_after": after_count,
            "objects_collected": collected,
            "objects_freed": before_count - after_count,
        }

        logger.info(
            f"Garbage collection: {collected} cycles, {gc_stats['objects_freed']} objects freed"
        )
        return gc_stats


# Global performance utilities
lazy_loader = LazyLoader()
performance_monitor = PerformanceMonitor()


def lazy_property(func):
    """
    Decorator for creating lazy properties that are computed only once.

    Example:
        @lazy_property
        def expensive_computation(self):
            return heavy_calculation()
    """
    attr_name = f"_lazy_{func.__name__}"

    @property
    @wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return wrapper


@lru_cache(maxsize=128)
def cached_file_reader(file_path: str) -> str:
    """
    Cached file reader for frequently accessed files.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read cached file {file_path}: {e}")
        raise PerformanceError(f"Failed to read file {file_path}: {e}")


class StartupOptimizer:
    """
    Optimizes application startup by deferring non-critical initialization.
    """

    def __init__(self):
        self.deferred_tasks: List[Callable] = []
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_deferred_tasks)
        self.timer.setSingleShot(True)

    def defer_task(self, task: Callable, delay_ms: int = 100) -> None:
        """Defer a task to be executed after startup."""
        self.deferred_tasks.append(task)

        # Start timer if not already running
        if not self.timer.isActive():
            self.timer.start(delay_ms)

    def _process_deferred_tasks(self) -> None:
        """Process all deferred tasks."""
        # Zmniejszono verbosity - komunikat przeniesiony na poziom DEBUG
        logger.debug(f"Processing {len(self.deferred_tasks)} deferred startup tasks")

        for task in self.deferred_tasks:
            try:
                task()
            except Exception as e:
                logger.error(f"Error in deferred task: {e}")

        self.deferred_tasks.clear()
        # Zmniejszono verbosity - komunikat przeniesiony na poziom DEBUG
        logger.debug("Deferred startup tasks completed")


# Global startup optimizer
startup_optimizer = StartupOptimizer()


def defer_until_after_startup(delay_ms: int = 100):
    """
    Decorator to defer function execution until after startup.

    Args:
        delay_ms: Delay in milliseconds before executing the function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            startup_optimizer.defer_task(lambda: func(*args, **kwargs), delay_ms)

        return wrapper

    return decorator


# Resource loading utilities
def create_css_loader(css_path: str) -> Callable:
    """Create a CSS file loader function."""

    def loader():
        return cached_file_reader(css_path)

    return loader


def create_translation_loader(lang_path: str) -> Callable:
    """Create a translation file loader function."""

    def loader():
        import json

        return json.loads(cached_file_reader(lang_path))

    return loader


def create_config_loader(config_path: str) -> Callable:
    """Create a configuration file loader function."""

    def loader():
        import json

        return json.loads(cached_file_reader(config_path))

    return loader


if __name__ == "__main__":
    # Example usage and testing
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Example: Register lazy loaders
    lazy_loader.register_loader("test_config", create_config_loader("config.json"))

    # Example: Async loading
    async_loader = AsyncResourceLoader()

    def example_loader():
        time.sleep(1)  # Simulate heavy loading
        return {"loaded": True}

    async_loader.load_resource_async("example", example_loader)

    # Example: Performance monitoring
    @performance_monitor.measure_execution_time("test_operation")
    def test_function():
        time.sleep(0.1)
        return "test result"

    result = test_function()
    print(f"Performance stats: {performance_monitor.get_performance_stats()}")

    app.exec()
