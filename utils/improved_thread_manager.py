import logging
import queue
import threading
import time
import weakref
from typing import Any, Callable, Dict, List, Optional, Set
from weakref import WeakValueDictionary

from PyQt6.QtCore import QObject, QRunnable, QThread, QThreadPool, QTimer, pyqtSignal

# Bezpośredni import klasy AsyncLogger z logger
try:
    from .logger import AsyncLogger
except ImportError:
    # Fallback dla testów lub gdy ścieżka importu jest inna
    AsyncLogger = None

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """
    Sygnały dla QRunnable workers
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(str)
    # Nowy sygnał dla monitorowania
    status_update = pyqtSignal(dict)


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
        self._start_time = None
        self._end_time = None
        self._thread_id = None
        self._execution_status = (
            "queued"  # ['queued', 'running', 'completed', 'failed', 'cancelled']
        )
        self._exception = None

    def run(self):
        """
        Wykonuje zadanie z timeoutem i obsługą błędów
        """
        try:
            self._start_time = time.time()
            self._thread_id = threading.get_ident()
            self._execution_status = "running"

            # Emituj aktualizację statusu
            self._emit_status_update()

            logger.debug(
                f"Starting task: {self.func.__name__} [Thread ID: {self._thread_id}]"
            )

            # Sprawdź czy zadanie zostało anulowane
            if self._is_cancelled:
                self._execution_status = "cancelled"
                self._emit_status_update()
                return

            # Sprawdź czy zadanie ma ustawiony timeout
            if self.timeout > 0:
                # Wykonaj funkcję z timeoutem używając osobnego wątku
                result_queue = queue.Queue(1)
                execution_thread = threading.Thread(
                    target=self._execute_with_timeout,
                    args=(result_queue,),
                    daemon=True,
                )
                execution_thread.start()
                execution_thread.join(self.timeout)

                if execution_thread.is_alive():
                    # Timeout - zadanie trwa zbyt długo
                    self._is_cancelled = True
                    self._execution_status = "failed"
                    self._exception = TimeoutError(
                        f"Task {self.func.__name__} timed out after {self.timeout} seconds"
                    )
                    logger.error(str(self._exception))
                    self._emit_status_update()
                    self.signals.error.emit(self._exception)
                    return

                if not result_queue.empty():
                    result_type, result = result_queue.get()
                    if result_type == "success":
                        if not self._is_cancelled:
                            self._execution_status = "completed"
                            self._end_time = time.time()
                            self._emit_status_update()
                            self.signals.finished.emit(result)
                            logger.debug(
                                f"Task completed: {self.func.__name__} in {self._end_time - self._start_time:.2f}s"
                            )
                    elif result_type == "error":
                        self._execution_status = "failed"
                        self._exception = result
                        self._end_time = time.time()
                        self._emit_status_update()
                        logger.error(f"Task failed: {self.func.__name__}: {result}")
                        self.signals.error.emit(result)
            else:
                # Standardowe wykonanie bez timeoutu
                result = self.func(*self.args, **self.kwargs)

                if not self._is_cancelled:
                    self._execution_status = "completed"
                    self._end_time = time.time()
                    self._emit_status_update()
                    self.signals.finished.emit(result)
                    logger.debug(
                        f"Task completed: {self.func.__name__} in {self._end_time - self._start_time:.2f}s"
                    )

        except Exception as e:
            self._exception = e
            self._execution_status = "failed"
            self._end_time = time.time()
            self._emit_status_update()
            logger.error(f"Task failed: {self.func.__name__}: {e}")
            if not self._is_cancelled:
                self.signals.error.emit(e)

    def _execute_with_timeout(self, result_queue):
        """
        Wykonuje funkcję i umieszcza wynik w kolejce
        """
        try:
            result = self.func(*self.args, **self.kwargs)
            if not self._is_cancelled:
                result_queue.put(("success", result))
        except Exception as e:
            if not self._is_cancelled:
                result_queue.put(("error", e))

    def cancel(self):
        """
        Anuluje zadanie i oznacza jako anulowane
        """
        if self._execution_status == "running":
            logger.debug(f"Attempting to cancel running task: {self.func.__name__}")
            # Tu można by dodać bardziej zaawansowaną logikę przerywania zadania

        self._is_cancelled = True
        self._execution_status = "cancelled"
        self._end_time = time.time() if self._start_time else None
        self._emit_status_update()

    def _emit_status_update(self):
        """
        Emituje aktualizację statusu zadania
        """
        status_data = {
            "task_name": getattr(self.func, "__name__", "unknown"),
            "status": self._execution_status,
            "thread_id": self._thread_id,
            "start_time": self._start_time,
            "duration": (
                (self._end_time - self._start_time)
                if self._end_time and self._start_time
                else None
            ),
            "error": str(self._exception) if self._exception else None,
        }
        self.signals.status_update.emit(status_data)

    def get_execution_info(self) -> Dict[str, Any]:
        """
        Zwraca informacje o wykonaniu zadania
        """
        return {
            "task_name": getattr(self.func, "__name__", "unknown"),
            "status": self._execution_status,
            "thread_id": self._thread_id,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "duration": (
                (self._end_time - self._start_time)
                if self._end_time and self._start_time
                else None
            ),
            "error": str(self._exception) if self._exception else None,
            "is_cancelled": self._is_cancelled,
        }


class LogQueue:
    """
    Ulepszona kolejka logów z lepszym zarządzaniem zasobami
    """

    def __init__(self, max_size: int = 1000, max_wait: float = 0.5):
        self.queue = queue.Queue(maxsize=max_size)
        self._shutdown = False
        self._health_checks = {
            "last_processed_time": time.time(),
            "processed_logs": 0,
            "dropped_logs": 0,
            "errors": 0,
            "blocked_seconds": 0,
        }
        self._health_check_lock = threading.Lock()
        self._max_wait = max_wait  # Maksymalny czas oczekiwania na przetworzenie logu

        self.thread = threading.Thread(
            target=self._process_logs, daemon=True, name="LogProcessor"
        )
        self.thread.start()
        logger.debug("LogQueue initialized")

    def _process_logs(self):
        """
        Przetwarza logi z kolejki z lepszą obsługą błędów i monitorowaniem
        """
        while not self._shutdown:
            try:
                try:
                    log_entry = self.queue.get(timeout=1.0)

                    # Aktualizacja czasów dla health check
                    with self._health_check_lock:
                        self._health_checks["last_processed_time"] = time.time()
                except queue.Empty:
                    # Nie blokujemy wątku na pustej kolejce - sprawdzamy health_checks
                    self._check_health()
                    continue

                if log_entry is None:  # Shutdown signal
                    break

                level, message = log_entry
                # Tutaj można dodać właściwe logowanie
                logger.log(level, message)
                self.queue.task_done()

                # Aktualizacja statystyk
                with self._health_check_lock:
                    self._health_checks["processed_logs"] += 1

            except Exception as e:
                logger.error(f"Error processing log: {e}")
                # Aktualizacja licznika błędów
                with self._health_check_lock:
                    self._health_checks["errors"] += 1
                time.sleep(0.1)

        logger.debug("LogQueue processor stopped")

    def _check_health(self):
        """
        Sprawdza stan zdrowia kolejki logów
        """
        with self._health_check_lock:
            now = time.time()
            last_processed = self._health_checks["last_processed_time"]
            time_since_last = now - last_processed

            # Wykrywanie blokady - jeśli ostatnie przetworzenie było dawno temu
            # a kolejka nie jest pusta
            if not self.queue.empty() and time_since_last > self._max_wait:
                self._health_checks["blocked_seconds"] += 1
                if (
                    self._health_checks["blocked_seconds"] % 10 == 0
                ):  # Log co 10 sekund blokady
                    logger.warning(
                        f"LogQueue appears to be blocked for {self._health_checks['blocked_seconds']} seconds"
                    )

    def add_log(self, level: int, message: str):
        """
        Dodaje wpis do kolejki logów z obsługą przepełnienia
        """
        if self._shutdown:
            return

        try:
            # Nie blokujemy przy dodawaniu - używamy put_nowait
            self.queue.put_nowait((level, message))
        except queue.Full:
            # Aktualizacja licznika przepełnień
            with self._health_check_lock:
                self._health_checks["dropped_logs"] += 1

            if (
                self._health_checks["dropped_logs"] % 100 == 1
            ):  # Ograniczamy częstość logowania
                logger.warning(
                    f"Log queue is full, dropping message. Total dropped: {self._health_checks['dropped_logs']}"
                )

    def get_health_status(self) -> Dict[str, Any]:
        """
        Zwraca status zdrowia kolejki logów
        """
        with self._health_check_lock:
            status = self._health_checks.copy()
            status["queue_size"] = self.queue.qsize()
            status["is_shutdown"] = self._shutdown

            # Oblicz status zdrowia na podstawie metryk
            health_status = "healthy"
            if status["dropped_logs"] > 100:
                health_status = "overloaded"
            elif status["blocked_seconds"] > 5:
                health_status = "blocked"
            elif status["errors"] > 10:
                health_status = "error_prone"

            status["health_status"] = health_status
            return status

    def stop(self):
        """
        Zatrzymuje przetwarzanie logów z timeoutem
        """
        logger.debug("Stopping LogQueue")
        self._shutdown = True

        try:
            self.queue.put(None, timeout=2.0)  # Timeout przy zatrzymywaniu
        except queue.Full:
            logger.warning("Could not send stop signal to LogQueue - queue is full")

        if self.thread.is_alive():
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning("LogQueue thread did not stop gracefully after 5s")


class ThreadManager(QObject):  # Zmieniono nazwę z ImprovedThreadManager
    """
    Ujednolicony manager wątków łączący funkcjonalność ImprovedThreadManager
    i starego ThreadManager
    """

    def __init__(
        self, max_workers: int = 4, enable_logging=True, task_timeout: int = 300
    ):  # Dodano enable_logging
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()  # Użycie globalInstance
        self.thread_pool.setMaxThreadCount(max_workers)
        self.enable_logging = enable_logging
        self.workers = []  # Dla kompatybilności
        self.active_tasks = weakref.WeakSet()  # Zmieniono z Dict na WeakSet
        self.task_id_map = WeakValueDictionary()  # Mapowanie task_id -> task

        # Użyj AsyncLogger jeśli dostępny, w przeciwnym razie używaj LogQueue
        if AsyncLogger and enable_logging:
            self._async_logger = AsyncLogger()
            self.log_queue = None
            logger.debug("Using AsyncLogger for thread management")
        else:
            self._async_logger = None
            self.log_queue = LogQueue() if enable_logging else None
            if enable_logging:
                logger.debug("Using LogQueue for thread management")

        # Historia zadań do analizy wycieków
        self._task_history = {}  # task_id -> task_info
        self._history_limit = 100  # Limit historii zadań
        self._long_running_threshold = 30  # Próg dla długotrwałych zadań (sekundy)

        if self.enable_logging:
            self._log_message(
                logging.INFO, f"ThreadManager initialized with {max_workers} workers"
            )

        self.task_timeout = task_timeout  # Dodano z ImprovedThreadManager
        self.task_counter = 0  # Dodano z ImprovedThreadManager

        # Cleanup timer - przeniesione z ImprovedThreadManager
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(30000)  # Cleanup co 30 sekund

        # Health check timer - dodatkowy timer dla częstszych kontroli zdrowia
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._check_thread_health)
        self.health_check_timer.start(5000)  # Health check co 5 sekund

        # Performance metrics
        self._start_time = time.time()
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._tasks_cancelled = 0
        self._lock = threading.Lock()

    def _log_message(self, level: int, message: str):
        """
        Centralna metoda logowania korzystająca z odpowiedniego loggera
        """
        if not self.enable_logging:
            return

        if self._async_logger:
            self._async_logger.log(level, message)
        elif self.log_queue:
            self.log_queue.add_log(level, message)
        else:
            logger.log(level, message)

    # Metody z ImprovedThreadManager
    def submit_task(
        self, func: Callable, *args, task_timeout: Optional[int] = None, **kwargs
    ) -> str:
        """
        Dodaje zadanie do pool'a

        Args:
            func: Funkcja do wykonania
            *args: Argumenty pozycyjne dla funkcji
            task_timeout: Opcjonalny timeout dla zadania (w sekundach)
            **kwargs: Argumenty nazwane dla funkcji

        Returns:
            str: ID zadania
        """
        # Użyj task_timeout, jeśli podany, w przeciwnym razie używamy domyślnego
        timeout = task_timeout if task_timeout is not None else self.task_timeout

        # Zachowaj wsteczną kompatybilność - sprawdź, czy timeout istnieje w kwargs
        if "timeout" in kwargs:
            timeout = kwargs.pop("timeout")

        self.task_counter += 1
        task_id = f"task_{self.task_counter}"

        task = ImprovedWorkerTask(func, timeout, *args, **kwargs)
        setattr(task, "task_id", task_id)  # Dodajemy atrybut task_id do obiektu zadania
        self.active_tasks.add(task)  # Dodawanie do WeakSet
        self.task_id_map[task_id] = task  # Dodajemy mapowanie task_id -> task

        # Monitorowanie statusu zadania
        task.signals.status_update.connect(
            lambda status_dict: self._on_status_update(task_id, status_dict)
        )

        # Weak reference cleanup po zakończeniu
        def on_finished(result):
            # Aktualizacja metryk
            with self._lock:
                self._tasks_completed += 1

            # Aktualizacja historii zadań
            self._update_task_history(task_id, "completed", result)

            if self.enable_logging and self._log_rate_limiter():
                self._log_message(
                    logging.DEBUG, f"Task {task_id} finished with result: {result}"
                )

        def on_error(error):
            # Aktualizacja metryk
            with self._lock:
                self._tasks_failed += 1

            # Aktualizacja historii zadań
            self._update_task_history(task_id, "failed", None, error)

            if self.enable_logging:
                self._log_message(
                    logging.ERROR, f"Task {task_id} failed with error: {error}"
                )

        task.signals.finished.connect(on_finished)
        task.signals.error.connect(on_error)

        self.thread_pool.start(task)

        # Zapisz podstawowe informacje o zadaniu w historii
        self._update_task_history(task_id, "submitted")

        if self.enable_logging:
            self._log_message(
                logging.DEBUG, f"Submitted task {task_id}: {func.__name__}"
            )
        return task_id

    def _on_status_update(self, task_id: str, status_dict: Dict[str, Any]):
        """
        Obsługuje aktualizacje statusu zadania
        """
        # Aktualizacja historii zadania w oparciu o status
        self._update_task_history(
            task_id, status_dict["status"], status_dict=status_dict
        )

        # Jesli zadanie zostało anulowane, aktualizuj licznik
        if status_dict["status"] == "cancelled":
            with self._lock:
                self._tasks_cancelled += 1

        # Loguj aktualizacje statusu dla długotrwałych zadań
        if (
            status_dict["status"] == "running"
            and status_dict.get("duration")
            and status_dict["duration"] > self._long_running_threshold
        ):
            self._log_message(
                logging.WARNING,
                f"Long running task detected: {task_id} ({status_dict.get('task_name', 'unknown')}) "
                f"running for {status_dict['duration']:.2f}s",
            )

    def _update_task_history(
        self, task_id: str, status: str, result=None, error=None, status_dict=None
    ):
        """
        Aktualizuje historię zadania
        """
        if len(self._task_history) >= self._history_limit:
            # Usuń najstarsze wpisy, gdy przekraczamy limit
            oldest_ids = sorted(
                self._task_history.keys(),
                key=lambda k: self._task_history[k].get("submit_time", 0),
            )[:10]
            for old_id in oldest_ids:
                self._task_history.pop(old_id, None)

        if task_id not in self._task_history:
            # Nowy wpis w historii
            self._task_history[task_id] = {
                "task_id": task_id,
                "submit_time": time.time(),
                "status": status,
            }
        else:
            # Aktualizacja istniejącego wpisu
            self._task_history[task_id]["status"] = status

            if status == "completed":
                self._task_history[task_id]["completion_time"] = time.time()

            elif status == "failed":
                self._task_history[task_id]["completion_time"] = time.time()
                self._task_history[task_id]["error"] = (
                    str(error) if error else "Unknown error"
                )

        # Dodaj dodatkowe dane statusu, jeśli dostępne
        if status_dict:
            self._task_history[task_id].update(status_dict)

    def cancel_task(self, task_id: str) -> bool:
        """
        Anuluje zadanie na podstawie jego ID.

        Args:
            task_id: ID zadania do anulowania

        Returns:
            bool: True jeśli zadanie zostało anulowane, False w przeciwnym wypadku
        """
        # Używamy WeakValueDictionary do szybkiego dostępu do zadania po ID
        task = self.task_id_map.get(task_id)

        if task is not None:
            task.cancel()
            # Aktualizacja historii zadania
            self._update_task_history(task_id, "cancelled")

            # WeakSet automatycznie usunie zadanie, gdy nie będzie już do niego referencji
            if self.enable_logging:
                self._log_message(logging.DEBUG, f"Cancelled task {task_id}")
            return True

        # Zadanie nie zostało znalezione
        if self.enable_logging:
            self._log_message(
                logging.WARNING, f"Task {task_id} not found for cancellation"
            )
        return False

    def get_active_task_count(self) -> int:
        """
        Zwraca liczbę aktywnych zadań
        """
        return len(self.active_tasks)  # Długość WeakSet

    def get_pool_info(self) -> Dict[str, Any]:
        """
        Zwraca informacje o thread pool
        """
        return {
            "max_workers": self.thread_pool.maxThreadCount(),
            "active_threads": self.thread_pool.activeThreadCount(),
            "active_tasks": len(self.active_tasks),  # Długość WeakSet
            "pool_size": self.thread_pool.maxThreadCount(),
        }

    def _log_rate_limiter(self) -> bool:
        """
        Ogranicza częstotliwość logowania przy wysokim obciążeniu

        Returns:
            bool: True jeśli logowanie powinno zostać wykonane, False w przeciwnym wypadku
        """
        active_count = self.get_active_task_count()
        # Ograniczenie logowania przy dużej liczbie zadań
        if active_count > 20:
            # Logowanie co 5-te zadanie przy dużym obciążeniu
            return self.task_counter % 5 == 0
        elif active_count > 10:
            # Logowanie co 3 zadania przy średnim obciążeniu
            return self.task_counter % 3 == 0
        return True

    def get_thread_health_status(self) -> Dict[str, Any]:
        """Monitor thread pool health and performance"""
        active_threads = self.thread_pool.activeThreadCount()
        max_threads = self.thread_pool.maxThreadCount()
        load_percentage = (active_threads / max_threads) * 100 if max_threads > 0 else 0

        status = "Healthy"
        if load_percentage > 90:
            status = "Overloaded"
        elif load_percentage > 70:
            status = "High Load"

        # Znajdź długotrwałe zadania
        long_running_tasks = []
        now = time.time()
        for task_id, info in self._task_history.items():
            if (
                info.get("status") == "running"
                and info.get("start_time")
                and now - info.get("start_time") > self._long_running_threshold
            ):
                long_running_tasks.append(
                    {
                        "task_id": task_id,
                        "duration": now - info.get("start_time"),
                        "task_name": info.get("task_name", "unknown"),
                    }
                )

        # Sprawdź czy mamy potencjalne wycieki wątków
        leaked_thread_count = 0
        for task_ref in list(self.active_tasks):
            # Sprawdź czy task nie jest już zakończony, ale nadal w aktywnych
            if hasattr(
                task_ref, "_execution_status"
            ) and task_ref._execution_status in ["completed", "failed", "cancelled"]:
                leaked_thread_count += 1

        return {
            "active_threads": active_threads,
            "max_threads": max_threads,
            "load_percentage": round(load_percentage, 2),
            "status": status,
            "active_tasks_in_weakset": len(self.active_tasks),
            "long_running_tasks": long_running_tasks,
            "potential_leaked_threads": leaked_thread_count,
        }

    def _check_thread_health(self):
        """
        Sprawdza stan zdrowia wątków i podejmuje działania naprawcze w razie problemów
        """
        health_status = self.get_thread_health_status()

        # Sprawdź LogQueue, jeśli jest używana
        if self.log_queue:
            log_health = self.log_queue.get_health_status()
            if log_health["health_status"] != "healthy":
                self._log_message(
                    logging.WARNING,
                    f"LogQueue health issues detected: {log_health['health_status']}. "
                    f"Dropped logs: {log_health['dropped_logs']}, "
                    f"Blocked seconds: {log_health['blocked_seconds']}",
                )

        # Sprawdź długotrwałe zadania
        if health_status["long_running_tasks"]:
            tasks_str = ", ".join(
                [
                    f"{t['task_id']}({t['task_name']}, {t['duration']:.1f}s)"
                    for t in health_status["long_running_tasks"][:3]  # Pokaż max 3
                ]
            )
            self._log_message(
                logging.WARNING,
                f"Long running tasks detected: {len(health_status['long_running_tasks'])} tasks, "
                f"including: {tasks_str}",
            )

        # Sprawdź czy mamy potencjalne wycieki wątków
        if health_status["potential_leaked_threads"] > 0:
            self._log_message(
                logging.WARNING,
                f"Potential thread leaks detected: {health_status['potential_leaked_threads']} tasks "
                f"marked as completed but still in active_tasks",
            )
            # Automatyczne czyszczenie potencjalnych wycieków
            if health_status["potential_leaked_threads"] > 5:
                self._cleanup_leaked_threads()

        # Jeśli obciążenie jest wysokie, rozważ działania naprawcze
        if health_status["load_percentage"] > 90:
            self._log_message(
                logging.WARNING,
                f"Thread pool overloaded: {health_status['load_percentage']}% "
                f"({health_status['active_threads']}/{health_status['max_threads']})",
            )

    def _cleanup_leaked_threads(self):
        """
        Czyści potencjalnie wyciekające wątki
        """
        leaked_count = 0
        for task_ref in list(self.active_tasks):
            if hasattr(
                task_ref, "_execution_status"
            ) and task_ref._execution_status in ["completed", "failed", "cancelled"]:
                # Zadanie zakończone, ale nadal w aktywnych - usuń referencję
                task_id = getattr(task_ref, "task_id", "unknown")
                self.active_tasks.discard(task_ref)
                if task_id != "unknown":
                    self.task_id_map.pop(task_id, None)
                leaked_count += 1

        if leaked_count > 0:
            self._log_message(
                logging.INFO, f"Cleaned up {leaked_count} leaked thread references"
            )

    def cleanup_finished_threads(self):
        """
        Cleanup completed threads and free resources.

        This method performs a thorough cleanup:
        1. Removes tasks that are completed but still in active_tasks
        2. Checks for long-running tasks that might be stuck
        3. Cleans up task history for completed tasks
        """
        cleaned_tasks = self._cleanup_leaked_threads()

        # Sprawdź długotrwałe zadania
        now = time.time()
        long_running_count = 0
        for task_id, info in list(self._task_history.items()):
            if info.get("status") == "running":
                if (
                    info.get("start_time")
                    and now - info.get("start_time") > self._long_running_threshold * 2
                ):
                    # Zadanie działa ponad dwukrotnie dłużej niż próg - oznacz jako podejrzane
                    self._log_message(
                        logging.WARNING,
                        f"Potentially stuck task: {task_id} running for {now - info.get('start_time'):.1f}s",
                    )
                    long_running_count += 1

        # Usuń zakończone zadania z historii, które są starsze niż 5 minut
        cleaned_history = 0
        for task_id, info in list(self._task_history.items()):
            if info.get("status") in ["completed", "failed", "cancelled"]:
                if (
                    info.get("completion_time")
                    and now - info.get("completion_time") > 300
                ):  # 5 minut
                    self._task_history.pop(task_id, None)
                    cleaned_history += 1

        if self.enable_logging:
            self._log_message(
                logging.DEBUG,
                f"Thread cleanup: Cleaned {cleaned_tasks} leaked tasks, "
                f"Found {long_running_count} potentially stuck tasks, "
                f"Cleaned {cleaned_history} history entries",
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return detailed thread performance statistics"""
        uptime = time.time() - self._start_time
        with self._lock:
            tasks_completed = self._tasks_completed
            tasks_failed = self._tasks_failed
            tasks_cancelled = self._tasks_cancelled

        tasks_processed = tasks_completed + tasks_failed + tasks_cancelled
        tps = tasks_processed / uptime if uptime > 0 else 0

        # Calculate failure rate
        failure_rate = (
            (tasks_failed / tasks_processed * 100) if tasks_processed > 0 else 0
        )

        # Analyze task history for performance insights
        task_durations = []
        status_counts = {"running": 0, "completed": 0, "failed": 0, "cancelled": 0}

        for task_info in self._task_history.values():
            status = task_info.get("status", "unknown")
            if status in status_counts:
                status_counts[status] += 1

            # Collect durations for completed tasks
            if status == "completed" and task_info.get("duration") is not None:
                task_durations.append(task_info["duration"])

        # Calculate average and max duration if we have any completed tasks
        avg_duration = (
            sum(task_durations) / len(task_durations) if task_durations else 0
        )
        max_duration = max(task_durations) if task_durations else 0

        return {
            "uptime_seconds": round(uptime, 2),
            "tasks_submitted_total": self.task_counter,
            "tasks_completed_successfully": tasks_completed,
            "tasks_failed": tasks_failed,
            "tasks_cancelled": tasks_cancelled,
            "failure_rate_percent": round(failure_rate, 2),
            "tasks_processed_per_second": round(tps, 2),
            "current_active_qrunnables": self.thread_pool.activeThreadCount(),
            "tasks_in_weakset_queue": len(self.active_tasks),
            "active_task_status": status_counts,
            "avg_task_duration": round(avg_duration, 3) if avg_duration else 0,
            "max_task_duration": round(max_duration, 3) if max_duration else 0,
        }

    def _periodic_cleanup(self):
        """
        Okresowe czyszczenie nieaktywnych zadań i monitorowanie zasobów.
        Wykonuje:
        1. Czyszczenie zakończonych zadań
        2. Sprawdzanie długotrwałych zadań
        3. Analizę obciążenia i wydajności
        4. Logowanie statystyk
        """
        # Uruchom czyszczenie zakończonych wątków
        self.cleanup_finished_threads()

        if self.enable_logging:
            # Zbierz statystyki
            active_count = len(self.active_tasks)
            health_status = self.get_thread_health_status()
            perf_metrics = self.get_performance_metrics()

            # Utwórz raport statusu
            status_report = (
                f"Thread status: {health_status['status']} "
                f"({health_status['active_threads']}/{health_status['max_threads']}) "
                f"load: {health_status['load_percentage']}%. "
                f"Tasks: active={active_count}, "
                f"completed={perf_metrics['tasks_completed_successfully']}, "
                f"failed={perf_metrics['tasks_failed']} "
                f"({perf_metrics['failure_rate_percent']}% fail rate). "
                f"TPS={perf_metrics['tasks_processed_per_second']:.2f}"
            )

            # Dodaj informacje o długotrwałych zadaniach, jeśli są
            if health_status["long_running_tasks"]:
                top_tasks = health_status["long_running_tasks"][:2]  # Pokaż max 2
                status_report += (
                    f". Long running: {len(health_status['long_running_tasks'])} tasks"
                )
                for task in top_tasks:
                    status_report += f", {task['task_name']}({task['duration']:.1f}s)"

            # Dodaj informacje o wyciekach, jeśli występują
            if health_status["potential_leaked_threads"] > 0:
                status_report += (
                    f". Potential leaks: {health_status['potential_leaked_threads']}"
                )

            # Loguj raport z odpowiednim poziomem w zależności od statusu
            if health_status["status"] == "Overloaded":
                self._log_message(logging.WARNING, status_report)
            else:
                self._log_message(logging.DEBUG, status_report)

            # Jeśli mamy istotne problemy, zaloguj więcej szczegółów
            if (
                health_status["status"] == "Overloaded"
                or len(health_status["long_running_tasks"]) > 3
                or health_status["potential_leaked_threads"] > 5
            ):
                self._log_message(
                    logging.WARNING,
                    f"Performance issues detected - avg task duration: {perf_metrics['avg_task_duration']:.3f}s, "
                    f"max duration: {perf_metrics['max_task_duration']:.3f}s",
                )

    def wait_for_completion(self, timeout: int = 30) -> bool:
        """
        Czeka na zakończenie wszystkich zadań z monitoringiem postępu

        Args:
            timeout: Maksymalny czas oczekiwania w sekundach

        Returns:
            bool: True jeśli wszystkie zadania się zakończyły, False w przeciwnym wypadku
        """
        if self.enable_logging:
            initial_count = len(self.active_tasks)
            if initial_count > 0:
                self._log_message(
                    logging.INFO,
                    f"Waiting for {initial_count} active tasks to complete (timeout: {timeout}s)",
                )

        # Podziel timeout na krótsze interwały, aby monitorować postęp
        slice_time = 3  # sekundy
        slices = max(1, int(timeout / slice_time))

        for i in range(slices):
            if self.thread_pool.activeThreadCount() == 0:
                if self.enable_logging:
                    self._log_message(logging.INFO, "All tasks completed")
                return True

            # Poczekaj krótki czas
            result = self.thread_pool.waitForDone(slice_time * 1000)
            if result:
                if self.enable_logging:
                    self._log_message(logging.INFO, "All tasks completed")
                return True

            # Zaloguj postęp, jeśli potrzeba
            if self.enable_logging and i % 2 == 0:  # Co 6 sekund
                remaining = len(self.active_tasks)
                completed = (
                    initial_count - remaining
                    if "initial_count" in locals()
                    else "unknown"
                )
                self._log_message(
                    logging.DEBUG,
                    f"Still waiting: {remaining} tasks active, {completed} completed",
                )

        # Timeout upłynął, ale zadania nie zakończyły się
        if self.enable_logging:
            remaining = len(self.active_tasks)
            self._log_message(
                logging.WARNING,
                f"Wait timeout: {remaining} tasks still active after {timeout}s",
            )
        return False

    def cleanup(self):
        """
        Czyści wszystkie zasoby z pogłębioną diagnostyką i obsługą błędów
        """
        if self.enable_logging:
            self._log_message(
                logging.INFO,
                f"Starting ThreadManager cleanup with {len(self.active_tasks)} active tasks",
            )

        # Zatrzymaj timery
        self.cleanup_timer.stop()
        self.health_check_timer.stop()

        # Zbierz informacje o aktywnych zadaniach przed anulowaniem
        active_task_info = []
        for task_ref in self.active_tasks:
            if hasattr(task_ref, "func") and hasattr(task_ref.func, "__name__"):
                task_name = task_ref.func.__name__
            else:
                task_name = "unknown_task"

            task_status = getattr(task_ref, "_execution_status", "unknown")
            task_id = getattr(task_ref, "task_id", "unknown")

            active_task_info.append(
                {"task_id": task_id, "name": task_name, "status": task_status}
            )

        # Zapisz szczegółowy log przed anulowaniem
        if active_task_info and self.enable_logging:
            tasks_str = ", ".join(
                [
                    f"{t['task_id']}({t['name']}, {t['status']})"
                    for t in active_task_info[:5]
                ]
            )  # Pokaż max 5
            if len(active_task_info) > 5:
                tasks_str += f" and {len(active_task_info) - 5} more"

            self._log_message(
                logging.INFO,
                f"Active tasks before cleanup: {len(active_task_info)}. "
                f"Including: {tasks_str}",
            )

        # Anuluj wszystkie aktywne zadania
        cancel_count = 0
        tasks_to_cancel = list(
            self.active_tasks
        )  # Tworzę kopię, żeby uniknąć modyfikacji podczas iteracji
        for task in tasks_to_cancel:
            try:
                if hasattr(task, "cancel"):
                    task.cancel()
                    cancel_count += 1
            except Exception as e:
                if self.enable_logging:
                    self._log_message(
                        logging.WARNING, f"Error cancelling task: {str(e)}"
                    )

        if self.enable_logging and cancel_count > 0:
            self._log_message(logging.INFO, f"Cancelled {cancel_count} active tasks")

        # Poczekaj na zakończenie zadań
        wait_result = self.wait_for_completion(10)
        if not wait_result and self.enable_logging:
            self._log_message(
                logging.WARNING,
                f"Some tasks ({len(self.active_tasks)}) did not complete within timeout during cleanup",
            )

        # Dodatkowe czyszczenie i raportowanie
        self._cleanup_leaked_threads()

        # Wyczyść historię zadań
        task_history_size = len(self._task_history)
        self._task_history.clear()

        # Zatrzymaj log queue
        if self.log_queue:
            if hasattr(self.log_queue, "get_health_status"):
                log_stats = self.log_queue.get_health_status()
                if self.enable_logging:
                    self._log_message(
                        logging.DEBUG,
                        f"LogQueue final stats: processed={log_stats['processed_logs']}, "
                        f"dropped={log_stats['dropped_logs']}, errors={log_stats['errors']}",
                    )
            self.log_queue.stop()

        # Zatrzymaj AsyncLogger, jeśli używany
        if self._async_logger:
            if hasattr(self._async_logger, "stop"):
                self._async_logger.stop()

        # Wyczyść pool
        self.thread_pool.clear()

        # Wyczyść pozostałe struktury danych
        self.active_tasks.clear()
        self.task_id_map.clear()

        # Zbierz metryki performance przed zakończeniem
        final_metrics = self.get_performance_metrics()

        if self.enable_logging:
            logger.info(
                f"ThreadManager cleanup completed. Metrics: "
                f"tasks_total={self.task_counter}, "
                f"completed={final_metrics['tasks_completed_successfully']}, "
                f"failed={final_metrics['tasks_failed']}, "
                f"cancelled={final_metrics['tasks_cancelled']}, "
                f"history_entries={task_history_size}"
            )

    # Metody kompatybilności ze starym API
    def run_in_thread(self, func, *args, **kwargs):
        """
        Kompatybilność ze starym API. Tworzy i uruchamia zadanie w sposób kompatybilny
        z poprzednią wersją API.

        Args:
            func: Funkcja do wykonania
            *args, **kwargs: Argumenty dla funkcji

        Returns:
            obj: Obiekt kompatybilny ze starym API, posiadający sygnały finished i error
        """
        # Używamy naszej ulepszonej implementacji do faktycznego zarządzania zadaniem
        task_id = self.submit_task(func, *args, **kwargs)
        task = self.task_id_map.get(task_id)

        if not task:
            if self.enable_logging:
                self._log_message(
                    logging.ERROR,
                    f"Failed to create compatible worker for {func.__name__}",
                )
            return None

        # Tworzymy obiekt kompatybilny ze starym API
        worker_compat_obj = QObject()
        worker_compat_obj.finished = task.signals.finished
        worker_compat_obj.error = task.signals.error
        worker_compat_obj.progress = task.signals.progress

        # Dodajemy metodę cancel dla kompatybilności
        worker_compat_obj.cancel = lambda: self.cancel_task(task_id)

        # Dodajemy identyfikator task_id do obiektu
        worker_compat_obj.task_id = task_id

        # Dodajemy czas startu i funkcję
        worker_compat_obj.start_time = time.time()
        worker_compat_obj.func_name = func.__name__

        # Dodajemy metodę do usuwania obiektu z listy workers
        def cleanup_worker():
            if worker_compat_obj in self.workers:
                self.workers.remove(worker_compat_obj)

        # Podłączamy sygnał zakończenia do funkcji czyszczącej
        task.signals.finished.connect(cleanup_worker)
        task.signals.error.connect(cleanup_worker)

        # Dodajemy do listy workers dla kompatybilności ze starym kodem
        self.workers.append(worker_compat_obj)

        if self.enable_logging:
            self._log_message(
                logging.DEBUG,
                f"Legacy run_in_thread: {func.__name__} (task_id: {task_id})",
            )

        return worker_compat_obj
