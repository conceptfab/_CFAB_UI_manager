#!/usr/bin/env python3
"""
Performance benchmarking script for CFAB UI Manager.

This script measures the performance improvements achieved by the optimization system.
"""

import json
import os
import sys
import time
from pathlib import Path

import psutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_cache import config_cache
from utils.performance_optimizer import (
    lazy_loader,
    performance_monitor,
    startup_optimizer,
)


def measure_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def benchmark_config_loading():
    """Benchmark configuration loading with and without caching."""
    config_file = "config.json"

    print("\n=== Configuration Loading Benchmark ===")

    # Test without cache (direct file loading)
    start_time = time.time()
    start_memory = measure_memory_usage()

    for i in range(100):
        with open(config_file, "r") as f:
            json.load(f)

    direct_time = time.time() - start_time
    direct_memory = measure_memory_usage() - start_memory

    print(f"Direct loading (100x): {direct_time:.3f}s, Memory: {direct_memory:.2f}MB")

    # Test with cache
    start_time = time.time()
    start_memory = measure_memory_usage()

    for i in range(100):
        config_cache.get_config(config_file)

    cached_time = time.time() - start_time
    cached_memory = measure_memory_usage() - start_memory

    print(f"Cached loading (100x): {cached_time:.3f}s, Memory: {cached_memory:.2f}MB")

    if cached_time > 0:
        speedup = direct_time / cached_time
        print(f"Speedup: {speedup:.2f}x faster with caching")

    return {
        "direct_time": direct_time,
        "cached_time": cached_time,
        "direct_memory": direct_memory,
        "cached_memory": cached_memory,
        "speedup": speedup if cached_time > 0 else 0,
    }


def benchmark_lazy_loading():
    """Benchmark lazy loading performance."""
    print("\n=== Lazy Loading Benchmark ===")

    def expensive_resource():
        # Simulate expensive resource creation
        time.sleep(0.01)
        return {"data": "expensive_computation", "size": 1024}

    # Register lazy resource
    lazy_loader.register_loader("expensive_data", expensive_resource)

    # Test immediate loading
    start_time = time.time()
    for i in range(10):
        expensive_resource()
    immediate_time = time.time() - start_time

    print(f"Immediate loading (10x): {immediate_time:.3f}s")

    # Test lazy loading (first access)
    start_time = time.time()
    data = lazy_loader.get_resource("expensive_data")
    first_lazy_time = time.time() - start_time

    print(f"First lazy access: {first_lazy_time:.3f}s")

    # Test subsequent lazy access
    start_time = time.time()
    for i in range(10):
        lazy_loader.get_resource("expensive_data")
    subsequent_lazy_time = time.time() - start_time

    print(f"Subsequent lazy access (10x): {subsequent_lazy_time:.3f}s")

    return {
        "immediate_time": immediate_time,
        "first_lazy_time": first_lazy_time,
        "subsequent_lazy_time": subsequent_lazy_time,
    }


def benchmark_memory_monitoring():
    """Benchmark memory monitoring overhead."""
    print("\n=== Memory Monitoring Benchmark ===")

    @performance_monitor.measure_execution_time("test_function")
    def test_function():
        # Simulate some work
        data = [i * i for i in range(1000)]
        return sum(data)

    # Test without monitoring
    start_time = time.time()
    for i in range(100):
        test_data = [i * i for i in range(1000)]
        result = sum(test_data)
    unmonitored_time = time.time() - start_time

    print(f"Unmonitored function (100x): {unmonitored_time:.3f}s")

    # Test with monitoring
    start_time = time.time()
    for i in range(100):
        test_function()
    monitored_time = time.time() - start_time

    print(f"Monitored function (100x): {monitored_time:.3f}s")

    overhead = monitored_time - unmonitored_time
    overhead_percent = (
        (overhead / unmonitored_time) * 100 if unmonitored_time > 0 else 0
    )

    print(f"Monitoring overhead: {overhead:.3f}s ({overhead_percent:.1f}%)")

    # Show monitoring statistics
    stats = performance_monitor.get_performance_stats()
    if "test_function" in stats:
        test_stats = stats["test_function"]
        print(f"Average execution time: {test_stats['avg_time']:.6f}s")
        print(f"Total calls: {test_stats['count']}")

    return {
        "unmonitored_time": unmonitored_time,
        "monitored_time": monitored_time,
        "overhead": overhead,
        "overhead_percent": overhead_percent,
    }


def run_comprehensive_benchmark():
    """Run comprehensive performance benchmarks."""
    print("🚀 CFAB UI Manager Performance Benchmark")
    print("=" * 50)

    initial_memory = measure_memory_usage()
    print(f"Initial memory usage: {initial_memory:.2f}MB")

    # Run benchmarks
    config_results = benchmark_config_loading()
    lazy_results = benchmark_lazy_loading()
    monitoring_results = benchmark_memory_monitoring()

    final_memory = measure_memory_usage()
    memory_usage = final_memory - initial_memory

    print(f"\n=== Summary ===")
    print(f"Configuration caching speedup: {config_results['speedup']:.2f}x")
    print(
        f"Lazy loading efficiency: {lazy_results['subsequent_lazy_time']:.3f}s vs {lazy_results['immediate_time']:.3f}s"
    )
    print(f"Monitoring overhead: {monitoring_results['overhead_percent']:.1f}%")
    print(f"Memory usage during benchmark: {memory_usage:.2f}MB")
    print(f"Final memory usage: {final_memory:.2f}MB")

    return {
        "config_loading": config_results,
        "lazy_loading": lazy_results,
        "memory_monitoring": monitoring_results,
        "memory_usage": {
            "initial": initial_memory,
            "final": final_memory,
            "used": memory_usage,
        },
    }


if __name__ == "__main__":
    try:
        results = run_comprehensive_benchmark()

        # Save results to file
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Benchmark complete! Results saved to benchmark_results.json")

    except KeyboardInterrupt:
        print("\n⏹️ Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback

        traceback.print_exc()
