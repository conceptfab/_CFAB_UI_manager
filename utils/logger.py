import logging
import os
import queue
import re
import sys
import time
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from queue import Empty, Full, Queue
from threading import Lock, Thread
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .exceptions import CFABError, ErrorCode


class AsyncLogger:
    """
    Klasa obsługująca asynchroniczne logowanie w osobnym wątku.

    Zapewnia buforowanie logów w kolejce i przetwarzanie ich w osobnym wątku,
    co poprawia wydajność aplikacji głównej przez uniknięcie blokowania na operacjach I/O.

    Przykład użycia:
        logger = AsyncLogger()
        logger.log(logging.INFO, "Uruchomienie aplikacji")
        logger.set_console_widget_handler(console_widget.append_log)
        try:
            # kod, który może rzucać wyjątki
        except Exception as e:
            logger.log(logging.ERROR, f"Błąd: {e}", exc_info=True)
    """

    def __init__(
        self,
        max_queue_size: int = 1000,
        process_interval: float = 0.01,
        logger_name: str = "AppLogger",
    ):
        """
        Inicjalizuje asynchroniczny logger z kolejką i wątkiem przetwarzającym.

        Args:
            max_queue_size: Maksymalny rozmiar kolejki logów
            process_interval: Interwał (w sekundach) oczekiwania przy pustej kolejce
            logger_name: Nazwa loggera do użycia
        """
        self.queue = Queue(maxsize=max_queue_size)
        self._shutdown_flag = False
        self._lock = Lock()
        self._process_interval = process_interval
        self._start_time = time.time()

        # Rozszerzone statystyki wydajności
        self._stats = {
            "logs_processed": 0,
            "logs_dropped": 0,
            "errors": 0,
            "warnings": 0,
            "processing_time_ms": 0,
            "max_processing_time_ms": 0,
            "average_processing_time_ms": 0,
            "queue_max_size": 0,
            "log_levels_count": {
                "debug": 0,
                "info": 0,
                "warning": 0,
                "error": 0,
                "critical": 0,
                "other": 0,
            },
            "cfab_errors_count": 0,
            "last_error_time": None,
            "log_throughput": 0,  # logs per second
        }

        # Główny logger aplikacji
        self.logger = logging.getLogger(logger_name)

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

        # Handler dla widgetu konsoli UI
        self._console_widget_handler = None

        # Formatterzy dla różnych typów logów
        self._formatters = {
            "default": logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            "error": logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s"
            ),
            "debug": logging.Formatter(
                "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s",
                "%Y-%m-%d %H:%M:%S",
            ),
            "ui": logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
            "cfab_error": logging.Formatter(
                "%(asctime)s - %(levelname)s - [%(error_code)s] - %(message)s"
            ),
        }

        # Uruchom wątek przetwarzający
        self.thread = Thread(
            target=self._process_logs, daemon=True, name="AsyncLoggerThread"
        )
        self.thread.start()

        if self._debug_mode:
            self.internal_logger.debug("AsyncLogger initialized")

    def _process_logs(self):
        """
        Przetwarza logi z kolejki w pętli.
        Zatrzymuje się gdy otrzyma sygnał zakończenia (None, None).
        Zawiera usprawnioną obsługę błędów i monitorowanie wydajności.
        """
        while not self._shutdown_flag:
            try:
                try:
                    # Używamy timeout, żeby regularnie sprawdzać flagę shutdown
                    level, message_or_record, exc_info, extra = self.queue.get(
                        timeout=self._process_interval
                    )

                    # Mierz czas przetwarzania dla statystyk
                    start_process_time = time.time()

                    # Aktualizuj statystyki rozmiaru kolejki
                    with self._lock:
                        current_size = self.queue.qsize()
                        if current_size > self._stats["queue_max_size"]:
                            self._stats["queue_max_size"] = current_size

                    if level is None:  # Sygnał zatrzymania
                        break

                    # Utworzenie rekordu logu
                    if isinstance(message_or_record, logging.LogRecord):
                        record = message_or_record
                    else:
                        # Dodatkowe atrybuty dla rekordu logu
                        extra_args = extra or {}
                        kwargs = {
                            "exc_info": exc_info,
                            "extra": extra_args,
                        }

                        record = self.logger.makeRecord(
                            self.logger.name,
                            level,
                            fn="",
                            lno=0,
                            msg=message_or_record,
                            args=(),
                            **kwargs,
                        )

                    # Aktualizacja liczników dla poszczególnych poziomów logów
                    with self._lock:
                        if level == logging.DEBUG:
                            self._stats["log_levels_count"]["debug"] += 1
                        elif level == logging.INFO:
                            self._stats["log_levels_count"]["info"] += 1
                        elif level == logging.WARNING:
                            self._stats["log_levels_count"]["warning"] += 1
                        elif level == logging.ERROR:
                            self._stats["log_levels_count"]["error"] += 1
                        elif level == logging.CRITICAL:
                            self._stats["log_levels_count"]["critical"] += 1
                        else:
                            self._stats["log_levels_count"]["other"] += 1

                    # Sprawdź, czy to jest log błędu CFABError
                    if extra and isinstance(extra, dict) and "error_code" in extra:
                        with self._lock:
                            self._stats["cfab_errors_count"] += 1

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
                            # Wybierz odpowiedni formatter w zależności od poziomu i typu logu
                            formatter = self._get_formatter_for_record(record)
                            formatted_message = formatter.format(record)

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
                            with self._lock:
                                self._stats["errors"] += 1

                            if self._debug_mode:
                                self.internal_logger.debug(
                                    f"Typ handlera: {type(self._console_widget_handler)}"
                                )

                    # Aktualizuj statystyki
                    process_time_ms = (time.time() - start_process_time) * 1000
                    with self._lock:
                        self._stats["logs_processed"] += 1
                        self._stats["processing_time_ms"] += process_time_ms
                        if process_time_ms > self._stats["max_processing_time_ms"]:
                            self._stats["max_processing_time_ms"] = process_time_ms

                        # Aktualizuj czas ostatniego błędu jeśli to jest błąd
                        if level >= logging.ERROR:
                            self._stats["errors"] += 1
                            self._stats["last_error_time"] = time.time()
                        elif level == logging.WARNING:
                            self._stats["warnings"] += 1

                        # Aktualizuj przepustowość logów (logs per second)
                        uptime = time.time() - self._start_time
                        if uptime > 0:
                            self._stats["log_throughput"] = (
                                self._stats["logs_processed"] / uptime
                            )

                    self.queue.task_done()

                except Empty:
                    # Pusta kolejka, nie robimy nic
                    continue

            except Exception as e:
                with self._lock:
                    self._stats["errors"] += 1

                # Użyj bezpośrednio logging, aby uniknąć pętli w przypadku błędu
                sys.stderr.write(
                    f"AsyncLogger: Krytyczny błąd w pętli przetwarzania logów: {e}\n"
                )
                traceback.print_exc(file=sys.stderr)

                # Spróbuj też zalogować poprzez standardowy logger
                try:
                    self.logger.critical(
                        f"AsyncLogger: Krytyczny błąd w pętli przetwarzania logów: {e}",
                        exc_info=True,
                    )
                except:
                    pass  # Ignoruj błędy loggera w tym miejscu

                time.sleep(0.1)  # Daj czas na stabilizację

        # Zamykanie wątku - wyświetl statystyki
        if self._debug_mode:
            avg_time = 0
            if self._stats["logs_processed"] > 0:
                avg_time = (
                    self._stats["processing_time_ms"] / self._stats["logs_processed"]
                )

            self.internal_logger.debug(
                f"AsyncLogger stopped. Stats: processed={self._stats['logs_processed']}, "
                f"dropped={self._stats['logs_dropped']}, errors={self._stats['errors']}, "
                f"avg_time={avg_time:.2f}ms, max_time={self._stats['max_processing_time_ms']:.2f}ms"
            )

    def log(self, level, message, exc_info=None, extra=None):
        """
        Dodaje wpis do kolejki logów z obsługą przepełnienia.

        Args:
            level: Poziom logu (np. logging.INFO, logging.ERROR)
            message: Wiadomość do zalogowania lub LogRecord
            exc_info: Opcjonalna informacja o wyjątku (True, tuple(typ, wartość, traceback) lub Exception)
            extra: Opcjonalny słownik z dodatkowymi danymi dla rekordu logu
        """
        if self._shutdown_flag:
            return

        try:
            self.queue.put_nowait((level, message, exc_info, extra))
        except Full:
            # Kolejka pełna, inkrementuj licznik porzuconych logów
            with self._lock:
                self._stats["logs_dropped"] += 1

            # Co 100 porzuconych logów próbuj zalogować ten problem
            if self._stats["logs_dropped"] % 100 == 1:
                try:
                    sys.stderr.write(
                        f"AsyncLogger: Kolejka logów przepełniona, porzucono {self._stats['logs_dropped']} logów\n"
                    )
                except:
                    pass

    def log_exception(
        self,
        exception,
        level=logging.ERROR,
        message=None,
        include_traceback=True,
        add_context=None,
    ):
        """
        Loguje wyjątek z pełnymi informacjami diagnostycznymi.
        Specjalna obsługa dla wyjątków CFABError - uwzględnia kod błędu.

        Args:
            exception: Wyjątek do zalogowania
            level: Poziom logu (domyślnie ERROR)
            message: Opcjonalna dodatkowa wiadomość
            include_traceback: Czy dołączyć traceback do logu (domyślnie True)
            add_context: Dodatkowy słownik z kontekstem zdarzenia
        """
        if message is None:
            message = str(exception)

        if isinstance(exception, CFABError):
            # Specjalna obsługa dla wyjątków z naszego frameworku
            error_code = (
                exception.error_code.value if exception.error_code else "UNKNOWN"
            )
            error_details = exception.details if hasattr(exception, "details") else {}

            # Dodaj dodatkowy kontekst do error_details, jeśli podano
            if add_context and isinstance(add_context, dict):
                if isinstance(error_details, dict):
                    error_details.update(add_context)
                else:
                    error_details = add_context

            extra = {
                "error_code": error_code,
                "error_details": error_details,
                "exception_type": type(exception).__name__,
            }

            # Jeśli jest oryginalny wyjątek, dodaj jego informacje
            if (
                hasattr(exception, "original_exception")
                and exception.original_exception
            ):
                orig_ex = exception.original_exception
                extra["original_exception"] = {
                    "type": type(orig_ex).__name__,
                    "message": str(orig_ex),
                }

            # Format: [KOD_BŁĘDU] Wiadomość (szczegóły)
            enhanced_message = f"[{error_code}] {message}"
            if error_details:
                enhanced_message += f" (details: {error_details})"

            # Aktualizuj licznik błędów typu CFABError
            with self._lock:
                self._stats["cfab_errors_count"] += 1
                self._stats["last_error_time"] = time.time()

            # Użyj exc_info tylko jeśli include_traceback jest True
            exc_info_param = exception if include_traceback else None
            self.log(level, enhanced_message, exc_info=exc_info_param, extra=extra)
        else:
            # Standardowa obsługa innych wyjątków
            extra = {"exception_type": type(exception).__name__}

            # Dodaj dodatkowy kontekst, jeśli podano
            if add_context and isinstance(add_context, dict):
                extra.update(add_context)

            # Użyj exc_info tylko jeśli include_traceback jest True
            exc_info_param = exception if include_traceback else None
            self.log(level, message, exc_info=exc_info_param, extra=extra)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Zwraca rozszerzone statystyki wydajności loggera.

        Returns:
            Dict zawierający szczegółowe statystyki wydajności
        """
        with self._lock:
            stats_copy = self._stats.copy()

        # Oblicz pochodne statystyki
        uptime = time.time() - self._start_time
        stats_copy["uptime_seconds"] = uptime
        stats_copy["uptime_formatted"] = self._format_time_duration(uptime)

        if stats_copy["logs_processed"] > 0:
            stats_copy["avg_processing_time_ms"] = (
                stats_copy["processing_time_ms"] / stats_copy["logs_processed"]
            )
        else:
            stats_copy["avg_processing_time_ms"] = 0

        if uptime > 0:
            stats_copy["logs_per_second"] = stats_copy["logs_processed"] / uptime

            # Dodaj statystyki per poziom logowania per sekundę
            for level, count in stats_copy["log_levels_count"].items():
                stats_copy[f"{level}_per_second"] = count / uptime
        else:
            stats_copy["logs_per_second"] = 0
            for level in stats_copy["log_levels_count"].keys():
                stats_copy[f"{level}_per_second"] = 0

        # Dodaj aktualny rozmiar kolejki
        try:
            stats_copy["current_queue_size"] = self.queue.qsize()
            stats_copy["queue_usage_percent"] = (
                (self.queue.qsize() / self.queue.maxsize) * 100
                if self.queue.maxsize > 0
                else 0
            )
        except Exception:
            # Zabezpieczenie na wypadek problemów z kolejką
            stats_copy["current_queue_size"] = "N/A"
            stats_copy["queue_usage_percent"] = "N/A"

        # Dodaj czas od ostatniego błędu
        if stats_copy["last_error_time"] is not None:
            time_since_last_error = time.time() - stats_copy["last_error_time"]
            stats_copy["time_since_last_error_seconds"] = time_since_last_error
            stats_copy["time_since_last_error_formatted"] = self._format_time_duration(
                time_since_last_error
            )
        else:
            stats_copy["time_since_last_error_seconds"] = None
            stats_copy["time_since_last_error_formatted"] = "N/A"

        # Dodaj współczynnik błędów
        if stats_copy["logs_processed"] > 0:
            stats_copy["error_rate"] = (
                stats_copy["errors"] / stats_copy["logs_processed"]
            )
            stats_copy["warning_rate"] = (
                stats_copy["warnings"] / stats_copy["logs_processed"]
            )
        else:
            stats_copy["error_rate"] = 0
            stats_copy["warning_rate"] = 0

        # Status zdrowia logera
        stats_copy["health_status"] = self._calculate_health_status(stats_copy)

        return stats_copy

    def _format_time_duration(self, seconds: float) -> str:
        """
        Formatuje czas trwania z sekund do czytelnego formatu.

        Args:
            seconds: Czas w sekundach

        Returns:
            String w formacie "X dni, Y godzin, Z minut, W sekund"
        """
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        result = []
        if days > 0:
            result.append(f"{int(days)} {'dni' if days > 1 else 'dzień'}")
        if hours > 0 or days > 0:
            result.append(f"{int(hours)} {'godzin' if hours != 1 else 'godzina'}")
        if minutes > 0 or hours > 0 or days > 0:
            result.append(f"{int(minutes)} {'minut' if minutes != 1 else 'minuta'}")
        result.append(f"{int(seconds)} {'sekund' if seconds != 1 else 'sekunda'}")

        return ", ".join(result)

    def _calculate_health_status(self, stats: Dict[str, Any]) -> str:
        """
        Oblicza status zdrowia loggera na podstawie statystyk.

        Args:
            stats: Słownik ze statystykami

        Returns:
            Status zdrowia: "healthy", "warning" lub "critical"
        """
        # Kryteria zdrowia
        if stats["error_rate"] > 0.1 or stats["queue_usage_percent"] > 90:
            return "critical"
        elif (
            stats["error_rate"] > 0.01
            or stats["warning_rate"] > 0.1
            or stats["queue_usage_percent"] > 70
        ):
            return "warning"
        else:
            return "healthy"

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
            self.internal_logger.debug("Debug mode enabled")
        else:
            # Najpierw zapisz komunikat, potem zmień poziom
            self.internal_logger.debug("Debug mode disabled")
            self.internal_logger.setLevel(logging.ERROR)  # Tylko błędy krytyczne

    def set_formatter(self, formatter_type: str, formatter: logging.Formatter):
        """
        Ustawia formatter dla określonego typu logów.

        Args:
            formatter_type: Typ formattera ('default', 'error', 'ui')
            formatter: Obiekt formattera
        """
        self._formatters[formatter_type] = formatter

    def set_console_widget_handler(
        self, handler_method: Callable, formatter: Optional[logging.Formatter] = None
    ):
        """
        Ustawia metodę handlera dla widgetu konsoli UI.

        Args:
            handler_method: Metoda (np. append_log widgetu) do wywołania z komunikatem logu.
            formatter: Opcjonalny formatter dla tego handlera.
        """
        self._console_widget_handler = handler_method
        if formatter:
            self._formatters["ui"] = formatter

    def stop(self):
        """
        Zatrzymuje wątek przetwarzający logi, zapisuje statystyki.
        """
        if self._shutdown_flag:
            return  # Już zatrzymany

        self._shutdown_flag = True
        try:
            self.queue.put((None, None, None, None))
        except:
            pass  # Ignoruj błędy podczas zamykania

        # Poczekaj na zakończenie wątku z timeout
        if self.thread.is_alive():
            self.thread.join(timeout=2.0)
            if self.thread.is_alive() and self._debug_mode:
                self.internal_logger.warning(
                    "AsyncLogger thread did not stop gracefully within timeout"
                )

        # Log końcowy z podsumowaniem (używamy bezpośrednio logging)
        final_stats = self.get_performance_stats()
        logging.getLogger("AppLogger").info(
            f"AsyncLogger stopped. Processed {final_stats['logs_processed']} logs, "
            f"dropped {final_stats['logs_dropped']}, "
            f"avg time {final_stats['avg_processing_time_ms']:.2f}ms"
        )

    def _get_formatter_for_record(self, record: logging.LogRecord) -> logging.Formatter:
        """
        Wybiera odpowiedni formatter na podstawie poziomu i typu logu.

        Args:
            record: Rekord logu do sformatowania

        Returns:
            Odpowiedni formatter dla danego rekordu
        """
        # Sprawdź czy to log z CFABError
        if hasattr(record, "error_code"):
            return self._formatters.get("cfab_error", self._formatters["default"])

        # Wybierz na podstawie poziomu
        if record.levelno >= logging.CRITICAL:
            return self._formatters.get("error", self._formatters["default"])
        elif record.levelno >= logging.ERROR:
            return self._formatters.get("error", self._formatters["default"])
        elif record.levelno >= logging.WARNING:
            return self._formatters.get("error", self._formatters["default"])
        elif record.levelno >= logging.DEBUG:
            return self._formatters.get("debug", self._formatters["default"])
        else:
            # Dla UI możemy użyć specjalnego formattera
            if self._console_widget_handler is not None:
                return self._formatters.get("ui", self._formatters["default"])
            return self._formatters.get("default", self._formatters["default"])


class AppLogger:
    """
    Główna klasa logująca dla aplikacji CFAB.

    Zarządza logowaniem asynchronicznym, konfiguracją formatterów,
    rotacją plików logów oraz integracją z konsolą UI.

    Przykład użycia:
        app_logger = AppLogger(log_dir="logs", app_name="CFAB")
        app_logger.setup()

        # Podstawowe logowanie
        app_logger.info("Aplikacja uruchomiona")
        app_logger.warning("Ostrzeżenie")

        # Logowanie wyjątków
        try:
            # kod, który może generować wyjątki
        except Exception as e:
            app_logger.exception("Wystąpił błąd", e)

        # Integracja z UI
        app_logger.set_console_widget(console_widget.append_log)

        # Zamknięcie
        app_logger.shutdown()
    """

    def __init__(
        self,
        log_dir: str = "logs",
        app_name: str = "AppLogger",
        log_level: int = logging.INFO,
        max_queue_size: int = 1000,
        enable_console: bool = True,
        enable_file_logging: bool = True,
        max_file_size_mb: int = 10,
        backup_count: int = 5,
        enable_daily_rotation: bool = True,
    ):
        """
        Inicjalizuje główny logger aplikacji.

        Args:
            log_dir: Katalog do przechowywania logów
            app_name: Nazwa aplikacji/logger
            log_level: Poziom logowania (np. logging.INFO)
            max_queue_size: Maksymalny rozmiar kolejki dla asynchronicznego logowania
            enable_console: Czy włączyć logowanie do konsoli
            enable_file_logging: Czy włączyć logowanie do pliku
            max_file_size_mb: Maksymalny rozmiar pliku logu w MB przed rotacją
            backup_count: Liczba kopii zapasowych plików logów
            enable_daily_rotation: Czy włączyć dzienną rotację plików
        """
        self.log_dir = os.path.abspath(log_dir)
        self.app_name = app_name
        self.log_level = log_level
        self.max_queue_size = max_queue_size
        self.enable_console = enable_console
        self.enable_file_logging = enable_file_logging
        self.max_file_size_mb = max_file_size_mb
        self.backup_count = backup_count
        self.enable_daily_rotation = enable_daily_rotation

        # Utwórz katalog logów, jeśli nie istnieje
        os.makedirs(self.log_dir, exist_ok=True)

        # Główny logger aplikacji
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False  # Nie propaguj do root loggera

        # Asynchroniczny logger do buforowania i przetwarzania logów
        self.async_logger = AsyncLogger(
            max_queue_size=max_queue_size, logger_name=self.app_name
        )

        # Ścieżki plików logów
        self.log_file_path = os.path.join(self.log_dir, f"{self.app_name}.log")
        self.error_log_file_path = os.path.join(
            self.log_dir, f"{self.app_name}_errors.log"
        )

        # Lista handlerów
        self.handlers = []

        # Flag indicating whether the logger has been set up
        self._is_setup = False

    def setup(self):
        """
        Konfiguruje i inicjalizuje logger.
        Ustawia handlery dla konsoli i plików.
        """
        if self._is_setup:
            return

        # Usuń istniejące handlery
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)

        # Dodaj handler konsoli
        if self.enable_console:
            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(console_handler)
            self.handlers.append(console_handler)

        # Dodaj handlery plików
        if self.enable_file_logging:
            # Główny plik logów z rotacją
            if self.enable_daily_rotation:
                # Dzienna rotacja
                file_handler = TimedRotatingFileHandler(
                    filename=self.log_file_path,
                    when="midnight",
                    interval=1,
                    backupCount=self.backup_count,
                )
            else:
                # Rotacja na podstawie rozmiaru
                file_handler = RotatingFileHandler(
                    filename=self.log_file_path,
                    maxBytes=self.max_file_size_mb * 1024 * 1024,
                    backupCount=self.backup_count,
                )

            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s"
                )
            )
            self.logger.addHandler(file_handler)
            self.handlers.append(file_handler)

            # Osobny plik tylko dla błędów (ERROR i CRITICAL)
            error_file_handler = RotatingFileHandler(
                filename=self.error_log_file_path,
                maxBytes=self.max_file_size_mb * 1024 * 1024,
                backupCount=self.backup_count,
            )
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s"
                )
            )
            self.logger.addHandler(error_file_handler)
            self.handlers.append(error_file_handler)

        self._is_setup = True
        # Komunikat zainicjowania przeniesiony na poziom DEBUG dla zmniejszenia verbosity
        self.debug(
            f"Logger '{self.app_name}' zainicjowany. Poziom logowania: {logging.getLevelName(self.log_level)}"
        )

    def set_console_widget(self, widget_handler: Callable[[str], None]):
        """
        Ustawia handler konsoli UI dla logów.

        Args:
            widget_handler: Funkcja do wyświetlania logów w UI
        """
        self.async_logger.set_console_widget_handler(widget_handler)
        self.info("Handler konsoli UI ustawiony")

    # Alias dla kompatybilności z kodem oczekującym set_console_widget_handler
    def set_console_widget_handler(self, widget_handler: Callable[[str], None]):
        """
        Alias dla set_console_widget dla zachowania kompatybilności.

        Args:
            widget_handler: Funkcja do wyświetlania logów w UI
        """
        return self.set_console_widget(widget_handler)

    def set_log_level(self, level: int):
        """
        Ustawia poziom logowania.

        Args:
            level: Poziom logowania (np. logging.INFO, logging.DEBUG)
        """
        self.log_level = level
        self.logger.setLevel(level)

        # Zaktualizuj poziom dla istniejących handlerów
        for handler in self.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setLevel(level)
            elif isinstance(handler, logging.FileHandler) and not isinstance(
                handler, logging.handlers.RotatingFileHandler
            ):
                handler.setLevel(level)

        # Ustaw także poziom dla modułu-rodzica (aplikacji)
        logging.getLogger().setLevel(level)

        # Ustaw poziom logowania dla wszystkich istniejących loggerów
        for logger_name in logging.root.manager.loggerDict:
            logger_obj = logging.getLogger(logger_name)
            # Nie zmieniaj poziomu dla loggerów, które mają włączoną propagację
            # i nie mają własnych handlerów - będą korzystać z konfiguracji rodzica
            if not (logger_obj.propagate and not logger_obj.handlers):
                logger_obj.setLevel(level)

        self.info(f"Poziom logowania zmieniony na: {logging.getLevelName(level)}")

    def debug(self, msg: str, *args, **kwargs):
        """Loguje komunikat na poziomie DEBUG."""
        self.async_logger.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Loguje komunikat na poziomie INFO."""
        self.async_logger.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Loguje komunikat na poziomie WARNING."""
        self.async_logger.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Loguje komunikat na poziomie ERROR."""
        self.async_logger.log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Loguje komunikat na poziomie CRITICAL."""
        self.async_logger.log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, exception: Exception = None, *args, **kwargs):
        """
        Loguje wyjątek z odpowiednim formatowaniem.

        Args:
            msg: Wiadomość do zalogowania
            exception: Wyjątek do zalogowania (jeśli None, użyje sys.exc_info())
        """
        if exception is None:
            exception = sys.exc_info()[1]

        if exception:
            self.async_logger.log_exception(
                exception, logging.ERROR, msg, *args, **kwargs
            )
        else:
            self.error(msg, *args, **kwargs)

    def cfab_error(self, cfab_error: CFABError, msg: str = None):
        """
        Specjalna metoda do logowania wyjątków CFABError.

        Args:
            cfab_error: Wyjątek CFABError do zalogowania
            msg: Opcjonalna dodatkowa wiadomość
        """
        if msg is None:
            msg = str(cfab_error)

        self.async_logger.log_exception(cfab_error, logging.ERROR, msg)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Zwraca statystyki wydajności loggera.

        Returns:
            Dict zawierający statystyki wydajności
        """
        return self.async_logger.get_performance_stats()

    def flush(self):
        """
        Wymusza przetworzenie wszystkich zakolejkowanych logów.
        """
        # Czekaj na przetworzenie wszystkich logów
        self.async_logger.queue.join()

    def shutdown(self):
        """
        Zatrzymuje logger, loguje statystyki i zamyka wszystkie handlery.
        """
        # Log final stats
        stats = self.get_performance_stats()
        self.info(
            f"Zamykanie loggera. Przetworzono {stats['logs_processed']} logów, "
            f"odrzucono {stats['logs_dropped']}, błędów: {stats['errors']}"
        )

        # Stop async logger
        self.async_logger.stop()

        # Close all handlers
        for handler in self.handlers:
            try:
                handler.close()
            except:
                pass

        # Remove all handlers
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)

        self.handlers = []
        self._is_setup = False


# Singleton instancja AppLogger
_app_logger = None


def initialize_logger(
    log_dir: str = "logs",
    app_name: str = "CFAB",
    log_level: int = logging.INFO,
    enable_console: bool = True,
    enable_file_logging: bool = True,
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    enable_daily_rotation: bool = True,
) -> AppLogger:
    """
    Inicjalizuje i konfiguruje główny logger aplikacji.

    Args:
        log_dir: Katalog logów
        app_name: Nazwa aplikacji/logger
        log_level: Poziom logowania
        enable_console: Czy włączyć logowanie do konsoli
        enable_file_logging: Czy włączyć logowanie do pliku
        max_file_size_mb: Maksymalny rozmiar pliku logu w MB
        backup_count: Liczba kopii zapasowych logów
        enable_daily_rotation: Czy włączyć dzienną rotację plików

    Returns:
        Skonfigurowana instancja AppLogger
    """
    global _app_logger

    if _app_logger is None:
        # Najpierw ustaw globalną konfigurację logowania
        logging.basicConfig(level=log_level, force=True)

        # Ustaw poziom dla root loggera
        logging.getLogger().setLevel(log_level)

        # Ustaw poziom dla wszystkich istniejących loggerów
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(log_level)

        _app_logger = AppLogger(
            log_dir=log_dir,
            app_name=app_name,
            log_level=log_level,
            enable_console=enable_console,
            enable_file_logging=enable_file_logging,
            max_file_size_mb=max_file_size_mb,
            backup_count=backup_count,
            enable_daily_rotation=enable_daily_rotation,
        )
        _app_logger.setup()

    return _app_logger


def get_logger() -> AppLogger:
    """
    Zwraca główny logger aplikacji. Jeśli nie został jeszcze zainicjowany,
    inicjuje go z domyślnymi parametrami.

    Returns:
        Instancja AppLogger
    """
    global _app_logger

    if _app_logger is None:
        return initialize_logger()

    return _app_logger
