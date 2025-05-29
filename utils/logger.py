import logging
import os
import time
from datetime import datetime
from queue import Queue
from threading import Thread


class AsyncLogger:
    """
    Klasa obsługująca asynchroniczne logowanie w osobnym wątku.
    """

    def __init__(self):
        """
        Inicjalizuje asynchroniczny logger z kolejką i wątkiem przetwarzającym.
        """
        self.queue = Queue()
        self.thread = Thread(target=self._process_logs, daemon=True)
        self.thread.start()
        self.logger = logging.getLogger("AppLogger")

    def _process_logs(self):
        """
        Przetwarza logi z kolejki w pętli.
        Zatrzymuje się gdy otrzyma sygnał zakończenia (None, None).
        """
        while True:
            try:
                level, message = self.queue.get()
                if level is None:
                    break
                self.logger.log(level, message)
                self.queue.task_done()
            except Exception:
                time.sleep(0.1)

    def log(self, level, message):
        """
        Dodaje wpis do kolejki logów.

        Args:
            level: Poziom logu (np. logging.INFO, logging.ERROR)
            message: Wiadomość do zalogowania
        """
        self.queue.put((level, message))

    def stop(self):
        """
        Zatrzymuje wątek przetwarzający logi.
        """
        self.queue.put((None, None))
        self.thread.join()


class AppLogger:
    """
    Główna klasa loggera aplikacji, zarządzająca konfiguracją i handlami logów.
    """

    def __init__(self, config):
        """
        Inicjalizuje logger aplikacji.

        Args:
            config (dict): Konfiguracja loggera zawierająca ustawienia
        """
        self.config = config
        self.async_logger = AsyncLogger()
        self.setup_logger()

    def setup_logger(self):
        """
        Konfiguruje logger na podstawie ustawień.
        Ustawia poziom logowania, handlery i formatowanie.
        """
        # Poziom logowania
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        log_level = level_map.get(self.config.get("log_level", "INFO"), logging.INFO)
        self.async_logger.logger.setLevel(log_level)

        # Usuń istniejące handlery
        for handler in self.async_logger.logger.handlers[:]:
            self.async_logger.logger.removeHandler(handler)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler (jeśli włączony)
        if self.config.get("log_ui_to_console", False):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.async_logger.logger.addHandler(console_handler)

        # File handler (jeśli włączony)
        if self.config.get("log_to_file", False):
            log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            os.makedirs(log_dir, exist_ok=True)

            log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = os.path.join(log_dir, log_filename)

            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.async_logger.logger.addHandler(file_handler)

    def debug(self, message):
        """
        Loguje wiadomość na poziomie DEBUG.

        Args:
            message: Wiadomość do zalogowania
        """
        self.async_logger.log(logging.DEBUG, message)

    def info(self, message):
        """
        Loguje wiadomość na poziomie INFO.

        Args:
            message: Wiadomość do zalogowania
        """
        self.async_logger.log(logging.INFO, message)

    def warning(self, message):
        """
        Loguje wiadomość na poziomie WARNING.

        Args:
            message: Wiadomość do zalogowania
        """
        self.async_logger.log(logging.WARNING, message)

    def error(self, message):
        """
        Loguje wiadomość na poziomie ERROR.

        Args:
            message: Wiadomość do zalogowania
        """
        self.async_logger.log(logging.ERROR, message)

    def cleanup(self):
        """
        Zatrzymuje asynchroniczny logger i czyści zasoby.
        """
        self.async_logger.stop()
