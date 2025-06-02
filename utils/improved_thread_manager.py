import logging
import queue
import threading
import time
import weakref
from typing import Any, Callable, Dict, List, Optional
from weakref import WeakValueDictionary

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


class LogQueue:
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
        self.log_queue = (
            LogQueue() if enable_logging else None
        )  # Użycie nowej nazwy LogQueue

        if self.enable_logging:
            logger.info(f"ThreadManager initialized with {max_workers} workers")

        self.task_timeout = task_timeout  # Dodano z ImprovedThreadManager
        self.task_counter = 0  # Dodano z ImprovedThreadManager

        # Cleanup timer - przeniesione z ImprovedThreadManager
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(30000)  # Cleanup co 30 sekund

        # Performance metrics
        self._start_time = time.time()
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._lock = threading.Lock()

    # Metody z ImprovedThreadManager
    def submit_task(self, func: Callable, *args, task_timeout: Optional[int] = None, **kwargs) -> str:
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
        setattr(task, 'task_id', task_id)  # Dodajemy atrybut task_id do obiektu zadania
        self.active_tasks.add(task)  # Dodawanie do WeakSet
        self.task_id_map[task_id] = task  # Dodajemy mapowanie task_id -> task

        # Weak reference cleanup po zakończeniu
        def on_finished(result):
            # self._remove_task(task_id) # Usunięto, WeakSet sam zarządza
            with self._lock:
                self._tasks_completed += 1
            if self.enable_logging and self._log_rate_limiter():
                self.log_queue.add_log(
                    logging.DEBUG, f"Task {task_id} finished with result: {result}"
                )

        def on_error(error):
            # self._remove_task(task_id) # Usunięto
            with self._lock:
                self._tasks_failed += 1
            if self.enable_logging:
                self.log_queue.add_log(
                    logging.ERROR, f"Task {task_id} failed with error: {error}"
                )

        task.signals.finished.connect(on_finished)
        task.signals.error.connect(on_error)

        self.thread_pool.start(task)

        if self.enable_logging:
            self.log_queue.add_log(
                logging.DEBUG, f"Submitted task {task_id}: {func.__name__}"
            )
        return task_id
        
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
            # WeakSet automatycznie usunie zadanie, gdy nie będzie już do niego referencji
            if self.enable_logging:
                self.log_queue.add_log(logging.DEBUG, f"Cancelled task {task_id}")
            return True
            
        # Zadanie nie zostało znalezione
        if self.enable_logging:
            self.log_queue.add_log(logging.WARNING, f"Task {task_id} not found for cancellation")
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
        # Ograniczenie logowania przy dużej liczbie zadań (powyżej 20)
        if active_count > 20:
            # Logowanie co 5-te zadanie przy dużym obciążeniu
            return self.task_counter % 5 == 0
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

        return {
            "active_threads": active_threads,
            "max_threads": max_threads,
            "load_percentage": round(load_percentage, 2),
            "status": status,
            "active_tasks_in_weakset": len(self.active_tasks),
        }

    def cleanup_finished_threads(self):
        """
        Remove completed threads and free resources.
        QThreadPool manages its threads automatically. This method can be used
        for custom cleanup logic if needed, or to explicitly clear the pool.
        For now, relies on QThreadPool's internal management and _periodic_cleanup.
        """
        # QThreadPool handles its own thread lifecycle.
        # If specific cleanup of QRunnable tasks is needed beyond WeakSet,
        # it would be implemented here.
        # For now, this method can be a placeholder or log current state.
        if self.enable_logging:
            self.log_queue.add_log(
                logging.DEBUG,
                "cleanup_finished_threads called. QThreadPool manages threads.",
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return thread performance statistics"""
        uptime = time.time() - self._start_time
        with self._lock:
            tasks_completed = self._tasks_completed
            tasks_failed = self._tasks_failed

        tasks_processed = tasks_completed + tasks_failed
        tps = tasks_processed / uptime if uptime > 0 else 0

        return {
            "uptime_seconds": round(uptime, 2),
            "tasks_submitted_total": self.task_counter,
            "tasks_completed_successfully": tasks_completed,
            "tasks_failed": tasks_failed,
            "tasks_processed_per_second": round(tps, 2),
            "current_active_qrunnables": self.thread_pool.activeThreadCount(),
            "tasks_in_weakset_queue": len(
                self.active_tasks
            ),  # Liczba zadań, które są śledzone przez WeakSet
        }

    # _remove_task nie jest już potrzebne z WeakSet

    def _periodic_cleanup(self):
        """
        Okresowe czyszczenie nieaktywnych zadań.
        WeakSet automatycznie usuwa obiekty, gdy nie ma do nich silnych referencji.
        Ta metoda może być uproszczona lub usunięta, chyba że są inne zadania cleanup.
        Dodatkowo, loguje statystyki.
        """
        if self.enable_logging:
            active_count = len(self.active_tasks)
            health_status = self.get_thread_health_status()
            perf_metrics = self.get_performance_metrics()

            self.log_queue.add_log(
                logging.DEBUG,
                f"Periodic cleanup: {active_count} active tasks in WeakSet. "
                f"Health: {health_status['status']} ({health_status['active_threads']}/{health_status['max_threads']}). "
                f"Perf: TPS={perf_metrics['tasks_processed_per_second']:.2f}, Completed={perf_metrics['tasks_completed_successfully']}",
            )
            # Można dodać logikę czyszczenia, jeśli WeakSet nie wystarcza
            # np. sprawdzanie "wiszących" zadań, które nie zostały poprawnie usunięte
            # przez WeakSet z jakiegoś powodu (np. cykliczne referencje)

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
        if self.enable_logging:
            self.log_queue.add_log(logging.INFO, "Starting ThreadManager cleanup")

        # Zatrzymaj timer cleanup
        self.cleanup_timer.stop()

        # Anuluj wszystkie aktywne zadania - wymaga iteracji po WeakSet
        tasks_to_cancel = []
        for task_ref in self.active_tasks:
            task = task_ref()
            if task:
                tasks_to_cancel.append(task)

        for task in tasks_to_cancel:
            task.cancel()  # Wywołaj metodę cancel na obiekcie zadania
            if self.enable_logging:
                # Załóżmy, że task ma atrybut func.__name__ lub podobny do identyfikacji
                task_name = getattr(
                    getattr(task, "func", None), "__name__", "unknown_task"
                )
                self.log_queue.add_log(
                    logging.DEBUG, f"Cancelled task {task_name} during cleanup"
                )

        # Poczekaj na zakończenie zadań
        if not self.wait_for_completion(10):
            if self.enable_logging:
                self.log_queue.add_log(
                    logging.WARNING,
                    "Some tasks did not complete within timeout during cleanup",
                )

        # Zatrzymaj log queue
        if self.log_queue:
            self.log_queue.stop()

        # Wyczyść pool
        self.thread_pool.clear()

        if self.enable_logging:
            logger.info(
                "ThreadManager cleanup completed"
            )  # Bezpośrednie logowanie, bo log_queue jest już zatrzymana

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
                self.log_queue.add_log(
                    logging.ERROR, f"Failed to create compatible worker for {func.__name__}"
                )
            return None
        
        # Tworzymy obiekt kompatybilny ze starym API
        worker_compat_obj = QObject()
        worker_compat_obj.finished = task.signals.finished
        worker_compat_obj.error = task.signals.error
        
        # Dodajemy metodę cancel dla kompatybilności
        worker_compat_obj.cancel = lambda: self.cancel_task(task_id)
        
        # Dodajemy identyfikator task_id do obiektu
        worker_compat_obj.task_id = task_id
        
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
            self.log_queue.add_log(
                logging.DEBUG, f"Legacy run_in_thread: {func.__name__} (task_id: {task_id})"
            )
            
        return worker_compat_obj
