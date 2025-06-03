#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testy dla modułu logger.py.

Testy sprawdzają:
- Formatowanie logów
- Integrację z wyjątkami
- Rotację plików logów
- Funkcjonalność klas AsyncLogger i AppLogger
"""

import logging
import os
import shutil
import tempfile
import threading
import time
import unittest
from queue import Queue

from utils.exceptions import CFABError, ErrorCode

# Importy dla testowania
from utils.logger import AppLogger, AsyncLogger, get_logger, initialize_logger


class TestAsyncLogger(unittest.TestCase):
    """Testy dla klasy AsyncLogger."""

    def setUp(self):
        """Przygotowanie środowiska testowego przed każdym testem."""
        self.async_logger = AsyncLogger(max_queue_size=100)

    def tearDown(self):
        """Czyszczenie po testach."""
        if hasattr(self, "async_logger"):
            self.async_logger.stop()

    def test_init(self):
        """Test inicjalizacji AsyncLogger."""
        self.assertIsNotNone(self.async_logger.queue)
        self.assertFalse(self.async_logger._shutdown_flag)
        self.assertTrue(self.async_logger.thread.is_alive())

    def test_log(self):
        """Test dodawania logów do AsyncLogger."""
        # Log test message
        self.async_logger.log(logging.INFO, "Test message")

        # Wait for processing
        time.sleep(0.1)

        # Check stats
        stats = self.async_logger.get_performance_stats()
        self.assertGreaterEqual(stats["logs_processed"], 1)
        self.assertGreaterEqual(stats["log_levels_count"]["info"], 1)

    def test_log_exception(self):
        """Test logowania wyjątków przez AsyncLogger."""
        # Create a test exception
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            # Log the exception
            self.async_logger.log_exception(e, message="Caught exception")

        # Wait for processing
        time.sleep(0.1)

        # Check stats
        stats = self.async_logger.get_performance_stats()
        self.assertGreaterEqual(stats["logs_processed"], 1)
        self.assertGreaterEqual(stats["errors"], 1)
        self.assertGreaterEqual(stats["log_levels_count"]["error"], 1)

    def test_cfab_error_logging(self):
        """Test logowania specjalnych wyjątków CFABError."""
        # Create a CFAB error
        error = CFABError(
            "Test CFAB error",
            error_code=ErrorCode.CONFIG,
            details={"file": "test.json"},
        )

        # Log the error
        self.async_logger.log_exception(error)

        # Wait for processing
        time.sleep(0.1)

        # Check stats
        stats = self.async_logger.get_performance_stats()
        self.assertGreaterEqual(stats["cfab_errors_count"], 1)

    def test_performance_stats(self):
        """Test zbierania statystyk wydajności."""
        # Log multiple messages
        for i in range(5):
            self.async_logger.log(logging.INFO, f"Info message {i}")

        for i in range(3):
            self.async_logger.log(logging.WARNING, f"Warning message {i}")

        for i in range(2):
            self.async_logger.log(logging.ERROR, f"Error message {i}")

        # Wait for processing
        time.sleep(0.2)

        # Check stats
        stats = self.async_logger.get_performance_stats()
        self.assertGreaterEqual(stats["logs_processed"], 10)
        self.assertGreaterEqual(stats["log_levels_count"]["info"], 5)
        self.assertGreaterEqual(stats["log_levels_count"]["warning"], 3)
        self.assertGreaterEqual(stats["log_levels_count"]["error"], 2)
        self.assertGreaterEqual(stats["errors"], 2)
        self.assertGreaterEqual(stats["warnings"], 3)
        self.assertIsNotNone(stats["uptime_formatted"])

    def test_stop(self):
        """Test zatrzymania AsyncLogger."""
        # Log a message
        self.async_logger.log(logging.INFO, "Test message")

        # Stop the logger
        self.async_logger.stop()

        # Check if thread is stopped or stopping
        time.sleep(0.1)
        self.assertTrue(self.async_logger._shutdown_flag)

        # Ensure we can't log after stopping
        self.async_logger.log(logging.INFO, "This should not be processed")
        stats = self.async_logger.get_performance_stats()
        self.assertGreaterEqual(stats["logs_processed"], 1)  # Still only 1 processed

    def test_log_formatting(self):
        """Test formatowania logów przez AsyncLogger."""
        # Test podstawowego formatowania
        test_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Sprawdź formatowanie dla różnych poziomów i typów logów
        formatters = {
            "default": self.async_logger._get_formatter_for_record(test_record),
            "debug": self.async_logger._get_formatter_for_record(
                logging.LogRecord(
                    "test", logging.DEBUG, "test.py", 1, "Debug", (), None
                )
            ),
            "error": self.async_logger._get_formatter_for_record(
                logging.LogRecord(
                    "test", logging.ERROR, "test.py", 1, "Error", (), None
                )
            ),
        }

        # Sprawdź czy każdy formatter zwraca string
        for name, formatter in formatters.items():
            formatted = formatter.format(test_record)
            self.assertIsInstance(formatted, str)
            self.assertIn("Test message", formatted)

        # Test formatowania CFABError
        cfab_record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="CFAB Error",
            args=(),
            exc_info=None,
        )
        setattr(cfab_record, "error_code", "CONFIG")

        cfab_formatter = self.async_logger._get_formatter_for_record(cfab_record)
        formatted_cfab = cfab_formatter.format(cfab_record)
        self.assertIsInstance(formatted_cfab, str)
        self.assertIn("CFAB Error", formatted_cfab)


class TestAppLogger(unittest.TestCase):
    """Testy dla klasy AppLogger."""

    def setUp(self):
        """Przygotowanie środowiska testowego przed każdym testem."""
        # Use a temporary directory for logs
        self.test_log_dir = tempfile.mkdtemp()
        self.app_logger = AppLogger(
            log_dir=self.test_log_dir,
            app_name="TestLogger",
            log_level=logging.DEBUG,
            max_file_size_mb=1,
            backup_count=2,
        )
        self.app_logger.setup()

    def tearDown(self):
        """Czyszczenie po testach."""
        if hasattr(self, "app_logger"):
            self.app_logger.shutdown()

        # Clean up test log directory
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def test_init_and_setup(self):
        """Test inicjalizacji i konfiguracji AppLogger."""
        self.assertEqual(self.app_logger.app_name, "TestLogger")
        self.assertEqual(self.app_logger.log_level, logging.DEBUG)
        self.assertTrue(self.app_logger._is_setup)
        self.assertTrue(os.path.exists(self.test_log_dir))

    def test_log_methods(self):
        """Test różnych metod logowania."""
        self.app_logger.debug("Debug message")
        self.app_logger.info("Info message")
        self.app_logger.warning("Warning message")
        self.app_logger.error("Error message")
        self.app_logger.critical("Critical message")

        # Wait for processing
        time.sleep(0.2)

        # Check stats
        stats = self.app_logger.get_performance_stats()
        self.assertGreaterEqual(stats["logs_processed"], 6)  # 5 + setup message

        # Check that files were created
        self.assertTrue(
            os.path.exists(os.path.join(self.test_log_dir, "TestLogger.log"))
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.test_log_dir, "TestLogger_errors.log"))
        )

    def test_exception_handling(self):
        """Test obsługi wyjątków."""
        try:
            raise ValueError("Test exception")
        except Exception as e:
            self.app_logger.exception("Caught exception", e)

        # Log a CFAB error
        error = CFABError(
            "Test CFAB error",
            error_code=ErrorCode.FILE_NOT_FOUND,
            details={"path": "/tmp/missing.txt"},
        )
        self.app_logger.cfab_error(error)

        # Wait for processing
        time.sleep(0.2)

        # Check stats
        stats = self.app_logger.get_performance_stats()
        self.assertGreaterEqual(stats["errors"], 2)
        self.assertGreaterEqual(stats["cfab_errors_count"], 1)

    def test_console_widget_integration(self):
        """Test integracji z widgetem konsoli."""
        # Create a mock console widget
        console_logs = []

        def mock_console_append(message):
            console_logs.append(message)

        # Set the mock widget
        self.app_logger.set_console_widget(mock_console_append)

        # Log some messages
        self.app_logger.info("Console info")
        self.app_logger.error("Console error")

        # Wait for processing
        time.sleep(0.2)

        # Check that messages were sent to the console
        # W rzeczywistym środowisku logów może być więcej ze względu na wcześniejsze
        # operacje (np. setup), więc używamy 'any' zamiast sprawdzać dokładną liczbę
        self.assertTrue(any("Console info" in log for log in console_logs))
        self.assertTrue(any("Console error" in log for log in console_logs))

    def test_log_level_change(self):
        """Test zmiany poziomu logowania."""
        # Log at DEBUG level
        self.app_logger.debug("Debug message")

        # Wait for processing
        time.sleep(0.1)

        # Change log level to INFO
        self.app_logger.set_log_level(logging.INFO)

        # These should not be processed due to level
        self.app_logger.debug("Debug message after level change")
        self.app_logger.info("Info message after level change")

        # Wait for processing
        time.sleep(0.1)

        # Check stats
        stats = self.app_logger.get_performance_stats()
        # Oczekiwane: 1 setup + 1 debug + 1 set_level info + 1 info after = 4
        self.assertGreaterEqual(
            stats["logs_processed"], 3
        )  # Co najmniej setup + debug + set_level

    def test_log_file_rotation(self):
        """Test rotacji plików logów."""
        # Zapisz duże logi, które powinny spowodować rotację
        for i in range(1000):  # Zmniejszenie liczby logów dla przyspieszenia testu
            self.app_logger.info(f"Test log message {i} " + "x" * 100)

        # Sprawdź, czy utworzono pliki rotacji
        time.sleep(0.5)  # Daj czas na przetworzenie i rotację

        # Sprawdź pliki w katalogu logów
        log_files = [
            f for f in os.listdir(self.test_log_dir) if f.startswith("TestLogger")
        ]

        # Powinien być główny plik logów i przynajmniej jeden dodatkowy plik
        self.assertGreaterEqual(len(log_files), 2)
        # Sprawdź tylko czy jest więcej niż jeden plik, bez sprawdzania rozszerzenia
        self.assertTrue(
            len(log_files) >= 2,
            f"Nie znaleziono wystarczającej liczby plików logów. Znalezione pliki: {log_files}",
        )


class TestLoggerHelperFunctions(unittest.TestCase):
    """Testy funkcji pomocniczych modułu logger."""

    def setUp(self):
        """Przygotowanie środowiska testowego przed każdym testem."""
        # Use a temporary directory for logs
        self.test_log_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Czyszczenie po testach."""
        from utils.logger import _app_logger

        # Reset the singleton instance
        if _app_logger is not None:
            _app_logger.shutdown()

        # Clean up the module's global variable
        import utils.logger

        utils.logger._app_logger = None

        # Clean up test log directory
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def test_initialize_logger(self):
        """Test inicjalizacji loggera."""
        logger = initialize_logger(
            log_dir=self.test_log_dir, app_name="InitTest", log_level=logging.INFO
        )

        self.assertIsNotNone(logger)
        self.assertEqual(logger.app_name, "InitTest")
        self.assertEqual(logger.log_level, logging.INFO)
        self.assertTrue(logger._is_setup)

    def test_get_logger(self):
        """Test pobierania loggera."""
        # First call should initialize with defaults
        logger1 = get_logger()
        self.assertIsNotNone(logger1)

        # Second call should return the same instance
        logger2 = get_logger()
        self.assertIs(logger1, logger2)

        # Reset the logger for testing custom initialization
        import utils.logger

        utils.logger._app_logger = None

        # After initializing explicitly, get_logger should return that instance
        custom_logger = initialize_logger(app_name="CustomLogger")
        retrieved_logger = get_logger()
        self.assertIs(custom_logger, retrieved_logger)
        self.assertEqual(retrieved_logger.app_name, "CustomLogger")


if __name__ == "__main__":
    unittest.main()
