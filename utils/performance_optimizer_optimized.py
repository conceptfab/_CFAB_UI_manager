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
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

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
        self._lock = (
            threading.RLock()
        )  # Zmieniono na RLock dla lepszego zarządzania zagnieżdżonymi wywołaniami
        self._resource_stats: Dict[str, Dict[str, float]] = (
            {}
        )  # Statystyki dla optymalizacji

    def register_loader(self, resource_name: str, loader_func: Callable) -> None:
        """Register a lazy loader function for a resource."""
        with self._lock:
            self._loaders[resource_name] = loader_func
            self._resource_stats[resource_name] = {
                "access_count": 0,
                "last_access": 0,
                "load_time": 0,
            }
            logger.debug(f"Registered lazy loader for: {resource_name}")

    @handle_error_gracefully
    def get_resource(self, resource_name: str, timeout: float = 10.0) -> Any:
        """Get a resource, loading it lazily if needed."""
        with self._lock:
            # Return if already loaded
            if resource_name in self._loaded_resources:
                # Aktualizuj statystyki dostępu
                if resource_name in self._resource_stats:
                    self._resource_stats[resource_name]["access_count"] += 1
                    self._resource_stats[resource_name]["last_access"] = time.time()
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
            elapsed = time.time() - start_time
            with self._lock:
                self._loaded_resources[resource_name] = resource
                self._loading_flags.discard(resource_name)

                # Aktualizuj statystyki
                if resource_name in self._resource_stats:
                    self._resource_stats[resource_name]["access_count"] = 1
                    self._resource_stats[resource_name]["last_access"] = time.time()
                    self._resource_stats[resource_name]["load_time"] = elapsed

            # Użyj debug zamiast info dla rutynowych operacji - zmniejszenie verbosity
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

    def get_resource_stats(self) -> Dict[str, Dict[str, Any]]:
        """Pobierz statystyki dostępu i ładowania dla zasobów."""
        with self._lock:
            stats = {}
            for resource_name, resource_stats in self._resource_stats.items():
                is_loaded = resource_name in self._loaded_resources
                stats[resource_name] = {
                    **resource_stats,
                    "is_loaded": is_loaded,
                    "is_loading": resource_name in self._loading_flags,
                }
            return stats

    def preload_resources(self, resource_names: List[str]) -> Dict[str, bool]:
        """Preładuj grupę zasobów równolegle, zwróć status powodzenia."""
        results = {}

        # Użyj ThreadPoolExecutor do równoległego ładowania
        with ThreadPoolExecutor(max_workers=min(len(resource_names), 8)) as executor:
            futures = {}

            for name in resource_names:
                if name in self._loaders and name not in self._loaded_resources:
                    futures[executor.submit(self.get_resource, name)] = name

            for future in futures:
                name = futures[future]
                try:
                    future.result(timeout=10.0)
                    results[name] = True
                except Exception:
                    results[name] = False

        return results


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
        # Automatycznie dostosuj ilość wątków do ilości rdzeni procesora, ale nie więcej niż podany max
        self.max_workers = min(max_workers, os.cpu_count() or 4)
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers, thread_name_prefix="AsyncLoader"
        )
        self.loading_tasks: Dict[str, Any] = {}
        self.completed_tasks = 0
        self.total_tasks = 0
        self._lock = (
            threading.RLock()
        )  # RLock dla lepszej obsługi zagnieżdżonych wywołań
        self.resource_priorities: Dict[str, int] = (
            {}
        )  # Priorytety zasobów (1-10, 10 najwyższy)

    @handle_error_gracefully
    def load_resource_async(
        self, resource_name: str, loader_func: Callable, *args, **kwargs
    ) -> None:
        """Load a resource asynchronously."""
        # Sprawdź czy priority zostało podane jako kwargs i usuń go, aby nie powodować konfliktów
        priority = 5
        if "priority" in kwargs:
            priority = kwargs.pop("priority")

        with self._lock:
            if resource_name in self.loading_tasks:
                logger.warning(f"Resource {resource_name} is already being loaded")
                return

            self.total_tasks += 1
            self.resource_priorities[resource_name] = max(1, min(10, priority))

        logger.debug(f"Starting async load for: {resource_name}")

        def _load_wrapper():
            start_time = time.time()
            try:
                self.progress_updated.emit(resource_name, 0)

                # Load the resource
                resource = loader_func(*args, **kwargs)

                self.progress_updated.emit(resource_name, 100)
                self.resource_loaded.emit(resource_name, resource)

                elapsed = time.time() - start_time

                with self._lock:
                    self.completed_tasks += 1
                    self.loading_tasks.pop(resource_name, None)
                    self.resource_priorities.pop(resource_name, None)

                    if self.completed_tasks >= self.total_tasks:
                        self.all_completed.emit()

                logger.debug(
                    f"Successfully loaded async resource: {resource_name} in {elapsed:.2f}s"
                )

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Failed to load async resource {resource_name}: {error_msg}"
                )
                self.loading_failed.emit(resource_name, error_msg)

                with self._lock:
                    self.completed_tasks += 1
                    self.loading_tasks.pop(resource_name, None)
                    self.resource_priorities.pop(resource_name, None)

        # Submit the task
        future = self.executor.submit(_load_wrapper)
        with self._lock:
            self.loading_tasks[resource_name] = future

    def batch_load(
        self,
        resources: Dict[str, Tuple[Callable, Dict[str, Any]]],
        on_batch_completed: Optional[Callable] = None,
    ) -> None:
        """
        Załaduj wiele zasobów asynchronicznie jako wsadową operację.

        Args:
            resources: Słownik {nazwa_zasobu: (funkcja_ładująca, parametry)}
            on_batch_completed: Opcjonalna funkcja wywoływana po ukończeniu wsadu
        """
        if not resources:
            return

        # Śledź grupę zasobów
        batch_id = str(time.time())
        batch_size = len(resources)
        completed_count = 0
        batch_lock = threading.Lock()

        def on_resource_complete():
            nonlocal completed_count
            with batch_lock:
                completed_count += 1
                if completed_count >= batch_size and on_batch_completed:
                    on_batch_completed()

        # Załaduj wszystkie zasoby, rozpoczynając od tych o wyższym priorytecie
        sorted_resources = sorted(
            resources.items(),
            key=lambda x: x[1].get("priority", 5) if isinstance(x[1], dict) else 5,
            reverse=True,  # Najpierw najwyższy priorytet
        )

        for resource_name, (loader_func, params) in sorted_resources:
            # Wyodrębnij priorytet jeśli istnieje
            priority = 5
            if isinstance(params, dict) and "priority" in params:
                priority = params.pop("priority")

            # Modyfikacja funkcji ładującej aby śledzić zakończenie wsadu
            original_loader = loader_func

            def batch_aware_loader(*args, **kwargs):
                result = original_loader(*args, **kwargs)
                on_resource_complete()
                return result

            # Przekaż parametry jako kwargs
            self.load_resource_async(
                resource_name, batch_aware_loader, priority=priority, **params
            )

    def get_loading_status(self) -> Dict[str, Any]:
        """
        Pobierz status ładowania wszystkich zasobów.

        Returns:
            Dict zawierający informacje o statusie ładowania
        """
        with self._lock:
            return {
                "active_tasks": list(self.loading_tasks.keys()),
                "completed": self.completed_tasks,
                "total": self.total_tasks,
                "percent_complete": int(
                    self.completed_tasks / max(1, self.total_tasks) * 100
                ),
                "priorities": {k: v for k, v in self.resource_priorities.items()},
            }

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
        self._hot_functions: Dict[str, int] = {}  # Śledzenie "gorących" funkcji
        self._optimization_suggestions: Dict[str, str] = {}  # Sugestie optymalizacyjne
        self._last_gc_time: float = time.time()

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

    def identify_optimization_targets(self) -> List[Dict[str, Any]]:
        """
        Zidentyfikuj funkcje, które mogą potrzebować optymalizacji.

        Returns:
            Lista funkcji z czasami wykonania i sugestiami optymalizacji.
        """
        targets = []

        for operation, times in self.execution_times.items():
            if not times:
                continue

            avg_time = sum(times) / len(times)
            max_time = max(times)
            call_count = len(times)

            # Identyfikuj funkcje, które są wolne lub często wywoływane
            if (
                avg_time > 0.1
                or max_time > 0.5
                or (avg_time > 0.01 and call_count > 50)
            ):
                suggestion = ""

                if avg_time > 0.5:
                    suggestion = "Rozważ użycie cachetowania lub lazy loading"
                elif max_time > 1.0:
                    suggestion = (
                        "Sprawdź przypadki brzegowe powodujące długie wykonanie"
                    )
                elif call_count > 100 and avg_time > 0.01:
                    suggestion = (
                        "Często wywoływana funkcja - optymalizuj wewnętrzne algorytmy"
                    )

                targets.append(
                    {
                        "operation": operation,
                        "avg_time": avg_time,
                        "max_time": max_time,
                        "call_count": call_count,
                        "total_time": sum(times),
                        "suggestion": suggestion,
                    }
                )

        # Sortuj według całkowitego czasu (impact)
        targets.sort(key=lambda x: x["total_time"], reverse=True)
        return targets

    def smart_garbage_collection(
        self, threshold_mb: float = 10.0, min_interval: float = 60.0
    ) -> bool:
        """
        Inteligentne zarządzanie garbage collection, uruchamiane tylko gdy potrzebne.

        Args:
            threshold_mb: Próg wzrostu pamięci w MB, który wyzwala GC
            min_interval: Minimalny odstęp czasowy między GC w sekundach

        Returns:
            bool: True jeśli GC zostało wykonane, False w przeciwnym razie
        """
        current_time = time.time()

        # Sprawdź czy minął minimalny interwał
        if current_time - self._last_gc_time < min_interval:
            return False

        process = psutil.Process()
        current_memory = process.memory_info().rss / (1024 * 1024)  # MB

        # Sprawdź ostatni snapshot (jeśli dostępny)
        if self.memory_snapshots:
            last_memory = self.memory_snapshots[-1].get("rss_mb", 0)
            memory_increase = current_memory - last_memory

            if memory_increase > threshold_mb:
                # Znaczący wzrost pamięci - uruchom GC
                self.force_garbage_collection()
                self._last_gc_time = current_time
                return True

        return False

    def get_optimization_report(self) -> Dict[str, Any]:
        """
        Generuj raport z sugestiami optymalizacji na podstawie zebranych danych.

        Returns:
            Raport zawierający sugestie optymalizacji i analizę wydajności
        """
        optimization_targets = self.identify_optimization_targets()
        memory_trend = self.get_memory_usage_trend()

        # Wygeneruj sugestie dotyczące optymalizacji pamięci
        memory_suggestions = []
        if (
            memory_trend.get("trend") == "increasing"
            and memory_trend.get("trend_slope_mb", 0) > 2
        ):
            memory_suggestions.append(
                f"Wykryto stały wzrost zużycia pamięci: {memory_trend.get('trend_slope_mb', 0):.1f}MB/snapshot. "
                f"Sprawdź wycieki pamięci i rozważ częstsze wywoływanie garbage collection."
            )

        potential_leaks = self.check_memory_leaks()
        if potential_leaks:
            top_leaks = {}
            for obj_type in potential_leaks:
                if obj_type not in top_leaks:
                    top_leaks[obj_type] = 0
                top_leaks[obj_type] += 1

            top_leak_types = sorted(
                top_leaks.items(), key=lambda x: x[1], reverse=True
            )[:5]
            leak_suggestions = [
                f"{obj_type}: {count} instancji" for obj_type, count in top_leak_types
            ]

            if leak_suggestions:
                memory_suggestions.append(
                    f"Potencjalne wycieki pamięci w typach obiektów: {', '.join(leak_suggestions)}"
                )

        return {
            "timestamp": time.time(),
            "operation_optimization_targets": optimization_targets[
                :10
            ],  # Top 10 operacji do optymalizacji
            "memory_analysis": memory_trend,
            "memory_suggestions": memory_suggestions,
            "total_operations_tracked": sum(
                len(times) for times in self.execution_times.values()
            ),
            "total_memory_snapshots": len(self.memory_snapshots),
        }


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


# Global performance utilities
lazy_loader = LazyLoader()
performance_monitor = PerformanceMonitor()
startup_optimizer = StartupOptimizer()


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
