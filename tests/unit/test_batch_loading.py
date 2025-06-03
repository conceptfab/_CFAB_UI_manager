"""
Testy dla funkcji wsadowego ładowania w AsyncResourceLoader.

Te testy weryfikują funkcjonalność:
- batch_load
- priorytetyzację zasobów
"""

import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import QThread
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtWidgets import QApplication

from utils.performance_optimizer import AsyncResourceLoader


class TestBatchLoading(unittest.TestCase):
    """Testy dla funkcji batch_load w AsyncResourceLoader."""

    @classmethod
    def setUpClass(cls):
        """Przygotowanie aplikacji Qt."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Przygotowanie przed każdym testem."""
        self.loader = AsyncResourceLoader(max_workers=4)
        self.batch_completed = threading.Event()

    def tearDown(self):
        """Czyszczenie po teście."""
        self.loader.cleanup()

    def test_batch_load_functionality(self):
        """Test, czy wsadowe ładowanie działa poprawnie."""
        loaded_resources = []

        def simple_loader(id, delay=0.1):
            time.sleep(delay)
            return f"resource_{id}"

        def on_batch_done():
            self.batch_completed.set()

        # Przygotuj resources z różnymi priorytetami
        resources = {
            "res1": (simple_loader, {"id": 1, "delay": 0.1, "priority": 9}),
            "res2": (simple_loader, {"id": 2, "delay": 0.1, "priority": 5}),
            "res3": (simple_loader, {"id": 3, "delay": 0.1, "priority": 3}),
            "res4": (simple_loader, {"id": 4, "delay": 0.1, "priority": 10}),
            "res5": (simple_loader, {"id": 5, "delay": 0.1, "priority": 1}),
        }

        # Śledź ładowane zasoby
        resource_spy = QSignalSpy(self.loader.resource_loaded)

        # Wywołaj batch_load
        start_time = time.time()
        self.loader.batch_load(resources, on_batch_completed=on_batch_done)

        # Poczekaj na zakończenie wsadowego ładowania
        self.batch_completed.wait(timeout=5)
        total_time = time.time() - start_time

        # Sprawdź, czy wszystkie zasoby zostały załadowane
        self.assertEqual(len(resource_spy), 5, "Powinno być załadowanych 5 zasobów")

        # Sprawdź całkowity czas - powinien być mniejszy niż suma czasów sekwencyjnych
        sequential_time = sum(res[1].get("delay", 0) for res in resources.values())
        print(
            f"Czas wsadowego ładowania: {total_time:.4f}s vs. sekwencyjnie: {sequential_time:.4f}s"
        )
        self.assertLess(
            total_time,
            sequential_time * 0.8,
            "Wsadowe ładowanie powinno być szybsze niż sekwencyjne",
        )

    def test_priority_ordering(self):
        """Test, czy zasoby z wyższym priorytetem są ładowane wcześniej."""
        loaded_order = []

        def mock_loader(id, priority, delay=0):
            loaded_order.append((id, priority))
            time.sleep(delay)
            return f"resource_{id}"

        # Ustawienie tylko jednego wątku wymusza sekwencyjne ładowanie
        self.loader = AsyncResourceLoader(max_workers=1)

        # Przygotuj resources z różnymi priorytetami, ale zamieniając kolejność
        resources = {
            "res1": (mock_loader, {"id": 1, "priority": 5, "delay": 0.1}),
            "res2": (mock_loader, {"id": 2, "priority": 8, "delay": 0.1}),
            "res3": (mock_loader, {"id": 3, "priority": 2, "delay": 0.1}),
            "res4": (mock_loader, {"id": 4, "priority": 10, "delay": 0.1}),
        }

        # Wywołaj batch_load
        self.loader.batch_load(resources)

        # Poczekaj na zakończenie wsadowego ładowania
        self.loader.wait_for_completion(timeout=5)

        # Sprawdź kolejność ładowania - powinna być od najwyższego do najniższego priorytetu
        expected_order = [(4, 10), (2, 8), (1, 5), (3, 2)]

        # Porównaj tylko ID w rzeczywistej kolejności z oczekiwaną
        actual_ids = [item[0] for item in loaded_order]
        expected_ids = [item[0] for item in expected_order]

        print(f"Kolejność ładowania: {loaded_order}")
        self.assertEqual(
            actual_ids,
            expected_ids,
            "Zasoby powinny być ładowane zgodnie z priorytetem (od najwyższego)",
        )


if __name__ == "__main__":
    unittest.main()
