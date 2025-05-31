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
        self.thread = Thread(
            target=self._process_logs, daemon=True, name="AsyncLoggerThread"
        )
        self.logger = logging.getLogger("AppLogger")
        self._console_widget_handler = None
        self._formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.thread.start()

    def _process_logs(self):
        """
        Przetwarza logi z kolejki w pętli.
        Zatrzymuje się gdy otrzyma sygnał zakończenia (None, None).
        """
        while True:
            try:
                level, message_or_record = self.queue.get()
                if level is None:
                    break

                if isinstance(message_or_record, logging.LogRecord):
                    record = message_or_record
                else:
                    record = self.logger.makeRecord(
                        self.logger.name,
                        level,
                        fn="",
                        lno=0,
                        msg=message_or_record,
                        args=(),
                        exc_info=None,
                    )

                self.logger.handle(record)  # Logowanie do standardowych handlerów

                self.logger.log(
                    logging.DEBUG,
                    f"AsyncLogger: Próba przetworzenia logu dla UI. Handler: {self._console_widget_handler}",
                )

                if self._console_widget_handler:
                    try:
                        formatted_message = self._formatter.format(record)
                        self.logger.log(
                            logging.DEBUG,
                            f"AsyncLogger: Wysyłanie sformatowanego logu do UI: {formatted_message[:100]}...",
                        )
                        # Próba wywołania handlera konsoli UI
                        self._console_widget_handler(formatted_message)
                    except Exception as e:
                        self.logger.log(
                            logging.CRITICAL,
                            f"AsyncLogger: Błąd w handlerze konsoli UI: {e}",
                            exc_info=True,
                        )
                        self.logger.log(
                            logging.DEBUG,
                            f"AsyncLogger: Typ handlera: {type(self._console_widget_handler)}, Handler: {self._console_widget_handler}",
                        )
                else:
                    self.logger.log(
                        logging.DEBUG, "AsyncLogger: Brak handlera konsoli UI."
                    )

                self.queue.task_done()
            except Exception as e:
                self.logger.log(
                    logging.CRITICAL,
                    f"AsyncLogger: Krytyczny błąd w pętli przetwarzania logów: {e}",
                    exc_info=True,
                )
                time.sleep(0.1)

    def log(self, level, message):
        """
        Dodaje wpis do kolejki logów.

        Args:
            level: Poziom logu (np. logging.INFO, logging.ERROR)
            message: Wiadomość do zalogowania lub LogRecord
        """
        self.queue.put((level, message))

    def set_console_widget_handler(self, handler_method, formatter=None):
        """
        Ustawia metodę handlera dla widgetu konsoli UI.

        Args:
            handler_method: Metoda (np. append_log widgetu) do wywołania z komunikatem logu.
            formatter: Opcjonalny formatter dla tego handlera.
        """
        self._console_widget_handler = handler_method
        if formatter:
            self._formatter = formatter

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

    def cleanup(self):
        """
        Zatrzymuje logger aplikacji i zwalnia zasoby.
        """
        if self.async_logger:
            self.async_logger.stop()
            # Dodatkowe logowanie na koniec
            logging.getLogger("AppLogger").info("AppLogger terminated correctly.")

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

        # Usuń istniejące handlery, aby uniknąć duplikatów przy rekonfiguracji
        for handler in self.async_logger.logger.handlers[:]:
            self.async_logger.logger.removeHandler(handler)

        # Formatter dla standardowych handlerów (plik, konsola systemowa)
        # Formatter dla UI będzie zarządzany przez AsyncLogger.set_console_widget_handler
        standard_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.async_logger._formatter = (
            standard_formatter  # Ustaw domyślny formatter w AsyncLogger
        )

        # Console handler (dla konsoli systemowej, jeśli włączony)
        if self.config.get(
            "log_ui_to_console", False
        ):  # Ta opcja może być myląca, może oznaczać logowanie do konsoli systemowej
            # Należy rozważyć zmianę nazwy tej opcji lub jej przeznaczenia
            # Na razie zakładamy, że to logowanie do konsoli systemowej, a nie UI
            system_console_handler = logging.StreamHandler()  # Domyślnie sys.stderr
            system_console_handler.setFormatter(standard_formatter)
            self.async_logger.logger.addHandler(system_console_handler)

        # File handler (jeśli włączony)
        if self.config.get("log_to_file", False):
            log_dir = self.config.get(
                "log_dir"
            )  # Pobierz z konfiguracji, jeśli dostępne
            if not log_dir:
                log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            os.makedirs(log_dir, exist_ok=True)

            log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = os.path.join(log_dir, log_filename)

            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(standard_formatter)
            self.async_logger.logger.addHandler(file_handler)

    def set_console_widget_handler(self, handler_method, formatter=None):
        """
        Przekazuje metodę handlera do AsyncLogger.

        Args:
            handler_method: Metoda (np. append_log widgetu) do wywołania z komunikatem logu.
            formatter: Opcjonalny formatter dla tego handlera.
        """
        self.async_logger.set_console_widget_handler(handler_method, formatter)

    def debug(self, message):
        self.async_logger.log(logging.DEBUG, message)

    def info(self, message):
        self.async_logger.log(logging.INFO, message)

    def warning(self, message):
        self.async_logger.log(logging.WARNING, message)

    def error(self, message):
        self.async_logger.log(logging.ERROR, message)

    def cleanup(self):
        """
        Zatrzymuje asynchroniczny logger i czyści zasoby.
        """
        self.async_logger.stop()
