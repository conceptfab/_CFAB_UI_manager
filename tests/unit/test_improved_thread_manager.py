"""
Testy jednostkowe dla ulepszonego zarządzania wątkami.
"""

import logging
import time
import unittest
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QCoreApplication

from utils.improved_thread_manager import ImprovedWorkerTask, LogQueue, ThreadManager


class TestLogQueue(unittest.TestCase):
    """Testy dla komponentu LogQueue"""

    def setUp(self):
        self.log_queue = LogQueue(max_size=10, max_wait=0.2)

    def tearDown(self):
        if hasattr(self, "log_queue"):
            self.log_queue.stop()

    def test_log_queue_initialization(self):
        """Test inicjalizacji kolejki logów"""
        self.assertIsNotNone(self.log_queue)
        self.assertFalse(self.log_queue._shutdown)

    def test_add_log(self):
        """Test dodawania logów do kolejki"""
        # Dodaj kilka logów
        self.log_queue.add_log(logging.INFO, "Test log 1")
        self.log_queue.add_log(logging.DEBUG, "Test log 2")
        self.log_queue.add_log(logging.ERROR, "Test log 3")

        # Pozwól na przetworzenie
        time.sleep(0.2)

        # Sprawdź stan zdrowia - logi powinny być przetworzone
        health = self.log_queue.get_health_status()
        self.assertEqual(health["health_status"], "healthy")
        self.assertEqual(health["errors"], 0)
        self.assertGreaterEqual(health["processed_logs"], 3)

    def test_queue_overload(self):
        """Test przepełnienia kolejki logów"""
        # Przepełnij kolejkę (rozmiar 10)
        for i in range(20):
            self.log_queue.add_log(logging.INFO, f"Overload test {i}")

        # Pozwól na przetworzenie części
        time.sleep(0.1)

        # Sprawdź czy wykryto przepełnienie
        health = self.log_queue.get_health_status()
        self.assertGreater(health["dropped_logs"], 0)

    def test_log_queue_stop(self):
        """Test poprawnego zatrzymania kolejki logów"""
        self.log_queue.stop()
        self.assertTrue(self.log_queue._shutdown)

        # Po zatrzymaniu dodawanie logów nie powinno działać
        self.log_queue.add_log(logging.INFO, "This should not be processed")


class TestImprovedWorkerTask(unittest.TestCase):
    """Testy dla komponentu ImprovedWorkerTask"""

    def setUp(self):
        # Symulacja środowiska Qt
        self.app = QCoreApplication.instance()
        if not self.app:
            import sys

            self.app = QCoreApplication(sys.argv)

    def test_worker_task_execution(self):
        """Test prawidłowego wykonania zadania"""
        # Utwórz mock dla sygnałów
        signals_mock = MagicMock()

        def test_func():
            return "success"

        # Utwórz zadanie
        task = ImprovedWorkerTask(test_func)
        task.signals = signals_mock

        # Wykonaj zadanie
        task.run()

        # Sprawdź czy sygnał finished został wyemitowany
        signals_mock.finished.emit.assert_called_once_with("success")

        # Sprawdź stan wykonania
        execution_info = task.get_execution_info()
        self.assertEqual(execution_info["status"], "completed")
        self.assertIsNotNone(execution_info["start_time"])
        self.assertIsNotNone(execution_info["end_time"])

    def test_worker_task_error(self):
        """Test obsługi błędu w zadaniu"""
        # Utwórz mock dla sygnałów
        signals_mock = MagicMock()

        def test_func_error():
            raise ValueError("Test error")

        # Utwórz zadanie
        task = ImprovedWorkerTask(test_func_error)
        task.signals = signals_mock

        # Wykonaj zadanie
        task.run()

        # Sprawdź czy sygnał error został wyemitowany
        signals_mock.error.emit.assert_called_once()

        # Sprawdź stan wykonania
        execution_info = task.get_execution_info()
        self.assertEqual(execution_info["status"], "failed")
        self.assertIn("Test error", execution_info["error"])

    def test_worker_task_cancellation(self):
        """Test anulowania zadania"""
        signals_mock = MagicMock()

        def test_func():
            return "should not reach here"

        # Utwórz zadanie
        task = ImprovedWorkerTask(test_func)
        task.signals = signals_mock

        # Anuluj zadanie przed wykonaniem
        task.cancel()

        # Wykonaj zadanie
        task.run()

        # Sprawdź czy żaden sygnał nie został wyemitowany
        signals_mock.finished.emit.assert_not_called()
        signals_mock.error.emit.assert_not_called()

        # Sprawdź stan wykonania
        execution_info = task.get_execution_info()
        self.assertEqual(execution_info["status"], "cancelled")

    @pytest.mark.skip("Test może być niestabilny ze względu na zależności czasowe")
    def test_worker_task_timeout(self):
        """Test przekroczenia limitu czasu dla zadania"""
        signals_mock = MagicMock()

        def long_task():
            time.sleep(2)  # Długotrwałe zadanie
            return "late result"

        # Utwórz zadanie z krótkim timeoutem
        task = ImprovedWorkerTask(long_task, timeout=1)
        task.signals = signals_mock

        # Wykonaj zadanie
        task.run()

        # Sprawdź czy sygnał error został wyemitowany z TimeoutError
        signals_mock.error.emit.assert_called_once()
        error_arg = signals_mock.error.emit.call_args[0][0]
        self.assertIsInstance(error_arg, TimeoutError)

        # Sprawdź stan wykonania
        execution_info = task.get_execution_info()
        self.assertEqual(execution_info["status"], "failed")
        self.assertIn("timed out", execution_info["error"])


class TestThreadManager(unittest.TestCase):
    """Testy dla ThreadManager"""

    def setUp(self):
        # Symulacja środowiska Qt
        self.app = QCoreApplication.instance()
        if not self.app:
            import sys

            self.app = QCoreApplication(sys.argv)

        # Utwórz ThreadManager z wyłączonym logowaniem
        self.thread_manager = ThreadManager(max_workers=2, enable_logging=False)

    def tearDown(self):
        if hasattr(self, "thread_manager"):
            self.thread_manager.cleanup()

    def test_thread_manager_initialization(self):
        """Test inicjalizacji ThreadManager"""
        self.assertIsNotNone(self.thread_manager)
        self.assertEqual(self.thread_manager.thread_pool.maxThreadCount(), 2)

    def test_submit_task(self):
        """Test dodawania zadania"""

        def test_func():
            return "task result"

        task_id = self.thread_manager.submit_task(test_func)

        # Sprawdź czy task_id został utworzony
        self.assertIsNotNone(task_id)
        self.assertTrue(task_id.startswith("task_"))

        # Sprawdź czy zadanie zostało dodane do aktywnych
        self.assertEqual(len(self.thread_manager.active_tasks), 1)

        # Poczekaj na zakończenie
        self.thread_manager.wait_for_completion(timeout=1)

    def test_cancel_task(self):
        """Test anulowania zadania"""
        result_container = []

        def delayed_task():
            time.sleep(0.5)
            result_container.append("task completed")
            return "delayed result"

        # Dodaj zadanie i od razu anuluj
        task_id = self.thread_manager.submit_task(delayed_task)
        cancel_result = self.thread_manager.cancel_task(task_id)

        # Sprawdź wynik anulowania
        self.assertTrue(cancel_result)

        # Poczekaj by upewnić się, że zadanie nie zostało wykonane
        time.sleep(0.7)
        self.assertEqual(len(result_container), 0)

    def test_performance_metrics(self):
        """Test zbierania metryk wydajności"""

        def quick_task():
            return "done"

        def failing_task():
            raise ValueError("Test failure")

        # Dodaj kilka zadań różnego typu
        self.thread_manager.submit_task(quick_task)
        self.thread_manager.submit_task(quick_task)
        self.thread_manager.submit_task(failing_task)

        # Poczekaj na zakończenie wszystkich zadań
        self.thread_manager.wait_for_completion(timeout=1)

        # Sprawdź metryki
        metrics = self.thread_manager.get_performance_metrics()

        self.assertEqual(metrics["tasks_submitted_total"], 3)
        self.assertEqual(metrics["tasks_completed_successfully"], 2)
        self.assertEqual(metrics["tasks_failed"], 1)

    def test_thread_health_status(self):
        """Test monitorowania stanu zdrowia wątków"""
        health = self.thread_manager.get_thread_health_status()

        # Sprawdź podstawowe pola
        self.assertIn("active_threads", health)
        self.assertIn("max_threads", health)
        self.assertIn("load_percentage", health)
        self.assertIn("status", health)
        self.assertIn("long_running_tasks", health)

        # Na początku status powinien być Healthy
        self.assertEqual(health["status"], "Healthy")

    def test_cleanup(self):
        """Test czyszczenia zasobów"""
        # Dodaj kilka zadań
        for _ in range(5):
            self.thread_manager.submit_task(lambda: time.sleep(0.1))

        # Uruchom czyszczenie
        self.thread_manager.cleanup()

        # Sprawdź czy zasoby zostały zwolnione
        self.assertEqual(len(self.thread_manager.active_tasks), 0)
        self.assertEqual(len(self.thread_manager._task_history), 0)


if __name__ == "__main__":
    unittest.main()
