import queue
import threading
import time

from PyQt6.QtCore import QObject, QThread, pyqtSignal


class WorkerThread(QThread):
    """
    Klasa reprezentująca wątek roboczy do wykonywania zadań w tle.

    Atrybuty:
        finished (pyqtSignal): Sygnał emitowany po zakończeniu zadania
        error (pyqtSignal): Sygnał emitowany w przypadku błędu
    """

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, func, *args, **kwargs):
        """
        Inicjalizuje wątek roboczy.

        Args:
            func: Funkcja do wykonania w wątku
            *args: Argumenty pozycyjne dla funkcji
            **kwargs: Argumenty nazwane dla funkcji
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Wykonuje funkcję w wątku i emituje odpowiednie sygnały.
        """
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)


class LogQueue:
    """
    Klasa zarządzająca kolejką logów w osobnym wątku.
    """

    def __init__(self):
        """
        Inicjalizuje kolejkę logów i wątek przetwarzający.
        """
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._process_logs, daemon=True)
        self.thread.start()

    def _process_logs(self):
        """
        Przetwarza logi z kolejki w pętli.
        """
        while True:
            try:
                log_entry = self.queue.get()
                if log_entry is None:
                    break
                # Tutaj implementacja zapisu logu
                self.queue.task_done()
            except Exception:
                time.sleep(0.1)

    def add_log(self, level, message):
        """
        Dodaje wpis do kolejki logów.

        Args:
            level: Poziom logu
            message: Wiadomość do zalogowania
        """
        self.queue.put((level, message))

    def stop(self):
        """
        Zatrzymuje wątek przetwarzający logi.
        """
        self.queue.put(None)
        self.thread.join()


class ThreadManager(QObject):
    """
    Klasa zarządzająca wątkami w aplikacji.
    """

    def __init__(self):
        """
        Inicjalizuje menedżera wątków.
        """
        super().__init__()
        self.workers = []
        self.log_queue = LogQueue()

    def run_in_thread(self, func, *args, **kwargs):
        """
        Uruchamia funkcję w osobnym wątku.

        Args:
            func: Funkcja do wykonania
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane

        Returns:
            WorkerThread: Utworzony wątek roboczy
        """
        worker = WorkerThread(func, *args, **kwargs)
        self.workers.append(worker)
        worker.finished.connect(lambda result: self.workers.remove(worker))
        worker.error.connect(lambda error: self.workers.remove(worker))
        worker.start()
        return worker

    def cleanup(self):
        """
        Czyści wszystkie wątki i zasoby.
        """
        self.log_queue.stop()
        for worker in self.workers:
            worker.quit()
            worker.wait()
