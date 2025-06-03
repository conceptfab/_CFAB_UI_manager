"""
Testy dla funkcjonalności identyfikacji celów optymalizacji i raportowania.

Te testy weryfikują funkcjonalność:
- identify_optimization_targets
- get_optimization_report
- smart_garbage_collection
"""

import gc
import time
import unittest
from unittest.mock import MagicMock, patch

import psutil

from utils.performance_optimizer import PerformanceMonitor


class TestOptimizationTargetsIdentification(unittest.TestCase):
    """Testy dla identyfikacji celów optymalizacji."""

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        self.monitor = PerformanceMonitor()

    def test_identify_optimization_targets(self):
        """Test identyfikacji funkcji do optymalizacji."""
        # Przygotuj dane testowe
        self.monitor.execution_times = {
            "fast_func": [0.001, 0.002, 0.001, 0.001],  # Szybka funkcja
            "slow_func": [0.3, 0.4, 0.5, 0.6],  # Wolna funkcja
            "normal_func": [0.01, 0.02, 0.01],  # Normalna funkcja
            "spike_func": [0.05, 0.04, 1.5, 0.03],  # Funkcja z jednorazowym spikiem
            "frequent_func": [0.02] * 200,  # Często wywoływana funkcja
        }

        # Wywołaj funkcję
        targets = self.monitor.identify_optimization_targets()

        # Weryfikuj wyniki
        self.assertGreater(
            len(targets), 0, "Powinny być zidentyfikowane cele optymalizacji"
        )

        # Sprawdź, czy wolna funkcja jest w wynikach
        slow_targets = [t for t in targets if t["operation"] == "slow_func"]
        self.assertEqual(
            len(slow_targets), 1, "Wolna funkcja powinna być celem optymalizacji"
        )
        self.assertGreater(
            slow_targets[0]["avg_time"],
            0.1,
            "Średni czas wolnej funkcji powinien być >0.1s",
        )

        # Sprawdź, czy funkcja ze spikiem jest w wynikach
        spike_targets = [t for t in targets if t["operation"] == "spike_func"]
        self.assertEqual(
            len(spike_targets), 1, "Funkcja ze spikiem powinna być celem optymalizacji"
        )
        self.assertGreater(
            spike_targets[0]["max_time"],
            1.0,
            "Max czas funkcji ze spikiem powinien być >1.0s",
        )

        # Sprawdź, czy często wywoływana funkcja jest w wynikach
        frequent_targets = [t for t in targets if t["operation"] == "frequent_func"]
        self.assertEqual(
            len(frequent_targets),
            1,
            "Często wywoływana funkcja powinna być celem optymalizacji",
        )

        # Sprawdź, czy szybka funkcja NIE jest w wynikach
        fast_targets = [t for t in targets if t["operation"] == "fast_func"]
        self.assertEqual(
            len(fast_targets), 0, "Szybka funkcja nie powinna być celem optymalizacji"
        )

        # Sprawdź, czy sugestie są sensowne
        for target in targets:
            self.assertIsNotNone(
                target.get("suggestion"),
                "Każdy cel powinien mieć sugestię optymalizacji",
            )
            self.assertGreater(
                len(target.get("suggestion", "")), 0, "Sugestia nie powinna być pusta"
            )

    def test_get_optimization_report(self):
        """Test generowania raportu optymalizacji."""
        # Przygotuj dane testowe
        self.monitor.execution_times = {
            "slow_func": [0.3, 0.4, 0.5],  # Wolna funkcja
            "normal_func": [0.01, 0.02, 0.01],  # Normalna funkcja
        }

        # Dodaj snapshoty pamięci pokazujące wzrost
        self.monitor.memory_snapshots = [
            {
                "timestamp": time.time() - 300,
                "rss_mb": 100,
                "vms_mb": 200,
                "memory_percent": 5,
            },
            {
                "timestamp": time.time() - 200,
                "rss_mb": 105,
                "vms_mb": 210,
                "memory_percent": 5.5,
            },
            {
                "timestamp": time.time() - 100,
                "rss_mb": 115,
                "vms_mb": 220,
                "memory_percent": 6,
            },
            {
                "timestamp": time.time(),
                "rss_mb": 130,
                "vms_mb": 240,
                "memory_percent": 7,
            },
        ]

        # Symuluj potencjalny wyciek pamięci
        class LeakableObject:
            def __init__(self, name):
                self.name = name
                self.data = [1] * 1000

        leak_objects = [LeakableObject("leak_obj") for _ in range(5)]
        for obj in leak_objects:
            self.monitor.register_weak_reference(obj)

        # Wywołaj funkcję
        report = self.monitor.get_optimization_report()

        # Weryfikuj wyniki
        self.assertIsNotNone(report, "Raport nie powinien być None")
        self.assertIn("timestamp", report, "Raport powinien zawierać timestamp")
        self.assertIn(
            "operation_optimization_targets",
            report,
            "Raport powinien zawierać cele optymalizacji",
        )
        self.assertIn(
            "memory_analysis", report, "Raport powinien zawierać analizę pamięci"
        )
        self.assertIn(
            "memory_suggestions",
            report,
            "Raport powinien zawierać sugestie dotyczące pamięci",
        )

        # Sprawdź trend pamięci
        self.assertEqual(
            report["memory_analysis"]["trend"],
            "increasing",
            "Trend pamięci powinien być rosnący",
        )

        # Sprawdź, czy widzimy potencjalne wycieki
        self.assertGreater(
            len(report["memory_suggestions"]),
            0,
            "Powinny być sugestie dotyczące pamięci",
        )

    def test_smart_garbage_collection(self):
        """Test inteligentnego garbage collection."""
        with patch.object(self.monitor, "force_garbage_collection") as mock_gc:
            # Ustaw czas ostatniego GC
            self.monitor._last_gc_time = time.time() - 120  # 2 minuty temu

            # Przygotuj snapshoty pamięci pokazujące duży wzrost
            self.monitor.memory_snapshots = [
                {"timestamp": time.time() - 60, "rss_mb": 100},
                {"timestamp": time.time(), "rss_mb": 110},  # 110MB ostatni snapshot
            ]

            # Wywołaj z progiem 15MB (powinno wykonać GC)
            with patch.object(psutil, "Process") as mock_process:
                mock_process.return_value.memory_info.return_value.rss = (
                    126 * 1024 * 1024
                )  # 126MB
                result = self.monitor.smart_garbage_collection(
                    threshold_mb=15.0, min_interval=60.0
                )

            # Sprawdź, czy GC zostało wykonane
            self.assertTrue(
                result, "GC powinno być wykonane przy wzroście powyżej progu"
            )
            mock_gc.assert_called_once()

            # Reset
            mock_gc.reset_mock()
            self.monitor._last_gc_time = time.time()  # Dopiero co wykonane

            # Wywołaj ponownie - nie powinno wykonać GC z powodu zbyt krótkiego interwału
            result = self.monitor.smart_garbage_collection(
                threshold_mb=15.0, min_interval=60.0
            )
            self.assertFalse(
                result, "GC nie powinno być wykonane przy krótkim interwale"
            )
            mock_gc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
