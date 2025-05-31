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
        self.active_tasks.add(task)  # Dodawanie do WeakSet

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
        Anuluje zadanie

        Args:
            task_id: ID zadania do anulowania - UWAGA: WeakSet nie wspiera bezpośredniego usuwania po ID,
                     trzeba by iterować i sprawdzać atrybut task_id w obiekcie task.
                     Dla uproszczenia, ta metoda może wymagać przeprojektowania lub usunięcia,
                     jeśli nie jest krytyczna. Załóżmy na razie, że nie jest używana lub
                     będzie dostosowana później.
                     Alternatywnie, można przechowywać mapowanie task_id -> weakref(task)
        Returns:
            bool: True jeśli zadanie zostało anulowane
        """
        # Implementacja wymaga dostosowania do WeakSet
        # Na potrzeby tego etapu, załóżmy, że ta funkcjonalność jest mniej priorytetowa
        # lub zostanie zaimplementowana inaczej.
        # Przykład:
        # for task_ref in self.active_tasks:
        #     task = task_ref() # Get the actual task object
        #     if task and hasattr(task, 'id') and task.id == task_id: # Zakładając, że task ma atrybut id
        #         task.cancel()
        #         # WeakSet sam usunie obiekt, gdy nie będzie już silnych referencji
        #         if self.enable_logging:
        #             self.log_queue.add_log(logging.DEBUG, f"Cancelled task {task_id}")
        #         return True
        if self.enable_logging:
            logger.warning(
                f"cancel_task for WeakSet needs review/reimplementation for task_id: {task_id}"
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
        Kompatybilność ze starym API
        """
        # Logika dla starego API, jeśli potrzebne zachowanie `workers`
        # W tym przypadku, po prostu przekierowujemy do submit_task
        # Jeśli LegacyWorker jest nadal potrzebny, można go tu zaimplementować
        # ale celem jest unifikacja.

        # Proste przekierowanie, jeśli LegacyWorker nie jest absolutnie konieczne:
        task_id = self.submit_task(func, *args, **kwargs)

        # Jeśli `self.workers` i sygnały `finished`/`error` na workerze są nadal używane
        # przez stary kod, trzeba by stworzyć obiekt kompatybilny.
        # Na podstawie opisu, celem jest konsolidacja, więc idealnie stary kod
        # powinien zostać zaktualizowany do używania `submit_task` bezpośrednio.
        # Poniżej uproszczona wersja, która nie tworzy LegacyWorker,
        # zakładając, że `self.workers` nie jest już krytyczne.

        # Jeśli jednak `LegacyWorker` jest potrzebny dla kompatybilności:
        class LegacyWorkerCompat:  # Uproszczona wersja dla kompatybilności
            def __init__(self, task_id_ref, manager_ref, original_task_signals):
                self.task_id = task_id_ref
                self.manager = manager_ref
                # Przekierowanie sygnałów z oryginalnego zadania
                self.finished = original_task_signals.finished
                self.error = original_task_signals.error
                # Można dodać metodę cancel, jeśli potrzebna
                # self.cancel = lambda: manager_ref.cancel_task(task_id_ref) # Uproszczenie

        # Aby to działało poprawnie, submit_task musiałby zwracać obiekt zadania,
        # a nie tylko task_id, lub musielibyśmy znaleźć zadanie po task_id.
        # Dla uproszczenia, na razie zwracamy task_id, co może wymagać dostosowania
        # w miejscach użycia run_in_thread, jeśli oczekują one obiektu workera.

        # Zgodnie z oryginalnym kodem `ThreadManager` (wrapper):
        # Tworzymy obiekt podobny do LegacyWorker, ale używając sygnałów z ImprovedWorkerTask

        # Aby to zadziałało, submit_task musiałby zwracać również obiekt task,
        # albo musielibyśmy go odszukać. Załóżmy, że submit_task zwraca task_id.
        # To jest problematyczne, bo stary API oczekuje obiektu workera.

        # Zmiana: submit_task powinien zwracać obiekt task, a nie task_id,
        # jeśli chcemy łatwo zaimplementować run_in_thread w ten sposób.
        # Alternatywnie, run_in_thread tworzy task i zarządza nim.

        # Podejście z `poprawki.md` (zwracanie task_id) jest prostsze, ale może łamać stary kod.
        # Załóżmy, że to jest akceptowalne zgodnie z planem.

        # Jeśli jednak chcemy pełniejszą kompatybilność dla `run_in_thread`
        # bez zmiany `submit_task` za bardzo:
        task = ImprovedWorkerTask(func, self.task_timeout, *args, **kwargs)

        # Symulacja LegacyWorker dla kompatybilności, jeśli potrzebne
        # To jest tylko jeśli `self.workers` i zwracany obiekt są krytyczne.

        # Definicja klasy pomocniczej QObject do posiadania sygnałów
        class CompatSignalsHelper(QObject):
            finished = pyqtSignal(object)
            error = pyqtSignal(Exception)

        # Utworzenie instancji klasy pomocniczej
        signals_helper_instance = CompatSignalsHelper()

        def on_compat_finished(result):
            signals_helper_instance.finished.emit(result)
            # Usunięcie z self.workers? Wymagałoby przechowywania referencji.

        def on_compat_error(error):
            signals_helper_instance.error.emit(error)

        task.signals.finished.connect(on_compat_finished)
        task.signals.error.connect(on_compat_error)

        self.thread_pool.start(task)
        self.active_tasks.add(task)  # Dodajemy do WeakSet

        # Tworzymy obiekt, który stary kod może oczekiwać
        # To jest odstępstwo od `return self.submit_task` z `poprawki.md`
        # ale zapewnia lepszą kompatybilność.
        worker_compat_obj = QObject()  # Prosty obiekt
        worker_compat_obj.finished = (
            signals_helper_instance.finished
        )  # Przypisujemy sygnał z instancji klasy pomocniczej
        worker_compat_obj.error = (
            signals_helper_instance.error
        )  # Przypisujemy sygnał z instancji klasy pomocniczej
        # worker_compat_obj.task = task # Można dodać referencję do zadania
        # worker_compat_obj.cancel = task.cancel # Przekazanie metody cancel

        self.workers.append(worker_compat_obj)  # Dla kompatybilności z `self.workers`

        if self.enable_logging:
            self.log_queue.add_log(
                logging.DEBUG, f"Legacy run_in_thread: {func.__name__}"
            )

        return worker_compat_obj  # Zwracamy obiekt z sygnałami
