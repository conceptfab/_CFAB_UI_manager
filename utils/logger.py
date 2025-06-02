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
        # Osobny logger dla wewnętrznych komunikatów diagnostycznych
        self.internal_logger = logging.getLogger("AsyncLoggerInternal")
        self.internal_logger.setLevel(logging.ERROR)  # Domyślnie tylko błędy
        self.internal_logger.propagate = (
            False  # Nie propagujemy logów do nadrzędnych loggerów
        )

        # Flaga kontrolująca poziom szczegółowości logów wewnętrznych
        self._debug_mode = False

        # Dodaj handler dla wewnętrznego loggera, jeśli jeszcze nie ma
        if not self.internal_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[ASYNC_LOGGER] %(message)s"))
            self.internal_logger.addHandler(handler)

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

                # Utworzenie rekordu logu
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

                # Logowanie do standardowych handlerów (plik, konsola systemowa)
                # zarządzanych przez główny logger
                self.logger.handle(record)

                # Wewnętrzne logowanie diagnostyczne tylko w trybie debugowania
                if self._debug_mode:
                    self.internal_logger.debug(
                        f"Przetworzono log: {record.levelname}. UI handler: {self._console_widget_handler is not None}"
                    )

                # Obsługa konsoli UI (jeśli skonfigurowana)
                if self._console_widget_handler:
                    try:
                        formatted_message = self._formatter.format(record)
                        # Loguj szczegóły wysyłania tylko w trybie debugowania
                        if self._debug_mode:
                            self.internal_logger.debug(
                                f"Wysyłanie do UI: {formatted_message[:100]}..."
                            )
                        # Wywołanie handlera konsoli UI
                        self._console_widget_handler(formatted_message)
                    except Exception as e:
                        # Krytyczne błędy zawsze logujemy
                        self.internal_logger.critical(
                            f"Błąd w handlerze konsoli UI: {e}", exc_info=True
                        )
                        if self._debug_mode:
                            self.internal_logger.debug(
                                f"Typ handlera: {type(self._console_widget_handler)}"
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

    def set_debug_mode(self, enabled=False):
        """
        Włącza lub wyłącza tryb debugowania, który pokazuje szczegółowe logi wewnętrzne.

        Args:
            enabled: True włącza tryb debug, False wyłącza.
        """
        self._debug_mode = enabled
        # Dostosuj poziom logowania wewnętrznego loggera
        if enabled:
            self.internal_logger.setLevel(logging.DEBUG)
        else:
            self.internal_logger.setLevel(logging.ERROR)  # Tylko błędy krytyczne

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

        # Sprawdź, czy tryb debugowania jest włączony w konfiguracji
        if self.config.get("logger_debug_mode", False):
            self.set_debug_mode(True)

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
            "log_to_system_console", self.config.get("log_ui_to_console", False)
        ):  # Używamy nowej nazwy, ale zachowujemy kompatybilność ze starą
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

    def set_debug_mode(self, enabled=False):
        """
        Włącza lub wyłącza tryb debugowania, który pokazuje szczegółowe logi wewnętrzne.

        Args:
            enabled: True włącza tryb debug, False wyłącza.
        """
        self.async_logger.set_debug_mode(enabled)
        if enabled:
            self.info(
                "Logger debug mode: ENABLED - pokazywanie szczegółowych logów wewnętrznych"
            )
        else:
            self.info(
                "Logger debug mode: DISABLED - pokazywanie tylko błędów krytycznych"
            )

    def debug(self, message):
        self.async_logger.log(logging.DEBUG, message)

    def info(self, message):
        self.async_logger.log(logging.INFO, message)

    def warning(self, message):
        self.async_logger.log(logging.WARNING, message)

    def error(self, message):
        self.async_logger.log(logging.ERROR, message)

    # Usunięto zduplikowaną metodę cleanup, ponieważ jest już zdefiniowana wyżej
