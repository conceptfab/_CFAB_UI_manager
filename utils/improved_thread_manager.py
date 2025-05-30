# Improved Thread Manager
# Ulepszony menedżer wątków z proper cleanup i limitami

import logging
import queue
import threading
import time
import weakref
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QObject, QRunnable, QThread, QThreadPool, QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """
    Sygnały dla QRunnable workers
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(str)


class ImprovedWorkerTask(QRunnable):
    """
    Ulepszone zadanie robocze z timeoutami i lepszą obsługą błędów
    """

    def __init__(self, func: Callable, timeout: int = 300, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.timeout = timeout
        self.signals = WorkerSignals()
        self._is_cancelled = False

    def run(self):
        """
        Wykonuje zadanie z timeoutem i obsługą błędów
        """
        try:
            logger.debug(f"Starting task: {self.func.__name__}")

            # Sprawdź czy zadanie zostało anulowane
            if self._is_cancelled:
                return

            result = self.func(*self.args, **self.kwargs)

            if not self._is_cancelled:
                self.signals.finished.emit(result)
                logger.debug(f"Task completed: {self.func.__name__}")

        except Exception as e:
            logger.error(f"Task failed: {self.func.__name__}: {e}")
            if not self._is_cancelled:
                self.signals.error.emit(e)

    def cancel(self):
        """
        Anuluje zadanie
        """
        self._is_cancelled = True


class ImprovedLogQueue:
    """
    Ulepszona kolejka logów z lepszym zarządzaniem zasobami
    """

    def __init__(self, max_size: int = 1000):
        self.queue = queue.Queue(maxsize=max_size)
        self._shutdown = False
        self.thread = threading.Thread(
            target=self._process_logs, daemon=True, name="LogProcessor"
        )
        self.thread.start()
        logger.debug("LogQueue initialized")

    def _process_logs(self):
        """
        Przetwarza logi z kolejki z lepszą obsługą błędów
        """
        while not self._shutdown:
            try:
                try:
                    log_entry = self.queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if log_entry is None:  # Shutdown signal
                    break

                level, message = log_entry
                # Tutaj można dodać właściwe logowanie
                logger.log(level, message)
                self.queue.task_done()

            except Exception as e:
                logger.error(f"Error processing log: {e}")
                time.sleep(0.1)

        logger.debug("LogQueue processor stopped")

    def add_log(self, level: int, message: str):
        """
        Dodaje wpis do kolejki logów
        """
        if self._shutdown:
            return

        try:
            self.queue.put_nowait((level, message))
        except queue.Full:
            logger.warning("Log queue is full, dropping message")

    def stop(self):
        """
        Zatrzymuje przetwarzanie logów
        """
        logger.debug("Stopping LogQueue")
        self._shutdown = True
        self.queue.put(None)

        if self.thread.is_alive():
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning("LogQueue thread did not stop gracefully")


class ImprovedThreadManager(QObject):
    """
    Ulepszony menedżer wątków z pool management i lepszym cleanup
    """

    def __init__(self, max_workers: int = 4, task_timeout: int = 300):
        super().__init__()
        self.max_workers = max_workers
        self.task_timeout = task_timeout

        # Thread pool zamiast ręcznego zarządzania wątkami
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(max_workers)

        # Tracking aktywnych zadań
        self.active_tasks: Dict[str, ImprovedWorkerTask] = {}
        self.task_counter = 0

        # Log queue
        self.log_queue = ImprovedLogQueue()

        # Cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(30000)  # Cleanup co 30 sekund

        logger.info(f"ThreadManager initialized with {max_workers} workers")

    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """
        Dodaje zadanie do pool'a

        Args:
            func: Funkcja do wykonania
            *args, **kwargs: Argumenty dla funkcji

        Returns:
            str: ID zadania
        """
        timeout = self.task_timeout
        # If the first argument is an integer and there are at least two args, treat as timeout
        if args and isinstance(args[0], int) and len(args) > 1:
            timeout = args[0]
            args = args[1:]
        if "timeout" in kwargs:
            timeout = kwargs.pop("timeout")

        self.task_counter += 1
        task_id = f"task_{self.task_counter}"

        task = ImprovedWorkerTask(func, timeout, *args, **kwargs)

        # Weak reference cleanup po zakończeniu
        def on_finished(result):
            self._remove_task(task_id)

        def on_error(error):
            self._remove_task(task_id)

        task.signals.finished.connect(on_finished)
        task.signals.error.connect(on_error)

        self.active_tasks[task_id] = task
        self.thread_pool.start(task)

        logger.debug(f"Submitted task {task_id}: {func.__name__}")
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """
        Anuluje zadanie

        Args:
            task_id: ID zadania do anulowania

        Returns:
            bool: True jeśli zadanie zostało anulowane
        """
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.cancel()
            self._remove_task(task_id)
            logger.debug(f"Cancelled task {task_id}")
            return True
        return False

    def get_active_task_count(self) -> int:
        """
        Zwraca liczbę aktywnych zadań
        """
        return len(self.active_tasks)

    def get_pool_info(self) -> Dict[str, Any]:
        """
        Zwraca informacje o thread pool
        """
        return {
            "max_workers": self.thread_pool.maxThreadCount(),
            "active_threads": self.thread_pool.activeThreadCount(),
            "active_tasks": len(self.active_tasks),
            "pool_size": self.thread_pool.maxThreadCount(),
        }

    def _remove_task(self, task_id: str):
        """
        Usuwa zadanie z tracking
        """
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            logger.debug(f"Removed task {task_id}")

    def _periodic_cleanup(self):
        """
        Okresowe czyszczenie nieaktywnych zadań
        """
        # Usuń zadania które już się zakończyły ale nie zostały usunięte
        finished_tasks = []
        for task_id, task in self.active_tasks.items():
            if task._is_cancelled:
                finished_tasks.append(task_id)

        for task_id in finished_tasks:
            self._remove_task(task_id)

        if finished_tasks:
            logger.debug(f"Cleaned up {len(finished_tasks)} finished tasks")

    def wait_for_completion(self, timeout: int = 30) -> bool:
        """
        Czeka na zakończenie wszystkich zadań

        Args:
            timeout: Maksymalny czas oczekiwania w sekundach

        Returns:
            bool: True jeśli wszystkie zadania się zakończyły
        """
        return self.thread_pool.waitForDone(timeout * 1000)

    def cleanup(self):
        """
        Czyści wszystkie zasoby
        """
        logger.info("Starting ThreadManager cleanup")

        # Zatrzymaj timer cleanup
        self.cleanup_timer.stop()

        # Anuluj wszystkie aktywne zadania
        for task_id in list(self.active_tasks.keys()):
            self.cancel_task(task_id)

        # Poczekaj na zakończenie zadań
        if not self.wait_for_completion(10):
            logger.warning("Some tasks did not complete within timeout")

        # Zatrzymaj log queue
        self.log_queue.stop()

        # Wyczyść pool
        self.thread_pool.clear()

        logger.info("ThreadManager cleanup completed")


# Backward compatibility - wrapper dla starego API
class ThreadManager(ImprovedThreadManager):
    """
    Wrapper dla zachowania kompatybilności ze starym API
    """

    def __init__(self):
        super().__init__(max_workers=4)
        self.workers = []  # Dla kompatybilności

    def run_in_thread(self, func, *args, **kwargs):
        """
        Kompatybilność ze starym API
        """

        class LegacyWorker:
            def __init__(self, task_id, manager):
                self.task_id = task_id
                self.manager = manager
                self.finished = pyqtSignal(object)
                self.error = pyqtSignal(Exception)

        task_id = self.submit_task(func, *args, **kwargs)
        worker = LegacyWorker(task_id, self)
        self.workers.append(worker)

        return worker
