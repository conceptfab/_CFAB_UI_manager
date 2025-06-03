"""
Tests for the exceptions module.
"""

import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from utils.exceptions import (
    APIError,
    CacheError,
    CFABError,
    ConfigurationError,
    DatabaseError,
    ErrorCode,
    FileOperationError,
    HardwareProfilingError,
    NetworkError,
    PerformanceError,
    ResourceError,
    SecurityError,
    ThreadManagementError,
    TranslationError,
    UIError,
    ValidationError,
    handle_error_gracefully,
    log_error_with_context,
    safe_operation,
    try_except_with_context,
)


class TestErrorCode(unittest.TestCase):
    """Test the ErrorCode Enum"""

    def test_error_code_values(self):
        """Should have specific string values for error codes."""
        self.assertEqual(ErrorCode.UNKNOWN.value, "CFAB_UNKNOWN")
        self.assertEqual(ErrorCode.CONFIG.value, "CFAB_CONFIG")
        self.assertEqual(ErrorCode.HARDWARE.value, "CFAB_HARDWARE")
        # Add more assertions for other error codes as needed


class TestCFABError(unittest.TestCase):
    """Test the base CFABError class"""

    @patch("utils.exceptions.logger")
    def test_cfab_error_creation_defaults(self, mock_logger):
        """Should create CFABError with default values and log it."""
        error = CFABError("Test message")
        self.assertEqual(error.message, "Test message")
        self.assertEqual(error.error_code, ErrorCode.UNKNOWN)
        self.assertEqual(error.details, {})
        self.assertIsNone(error.original_exception)
        mock_logger.error.assert_called_once_with(
            "[CFAB_UNKNOWN] Test message", extra={"details": {}}
        )

    @patch("utils.exceptions.logger")
    def test_cfab_error_creation_with_all_params(self, mock_logger):
        """Should create CFABError with all parameters and log it."""
        original_exc = ValueError("Original error")
        details = {"key": "value"}
        error = CFABError(
            "Test message with params",
            ErrorCode.CONFIG,
            details=details,
            original_exception=original_exc,
        )
        self.assertEqual(error.message, "Test message with params")
        self.assertEqual(error.error_code, ErrorCode.CONFIG)
        expected_details = {
            "key": "value",
            "original_exception_type": "ValueError",
            "original_exception_message": "Original error",
        }
        self.assertEqual(error.details, expected_details)
        self.assertIs(error.original_exception, original_exc)
        mock_logger.error.assert_called_once_with(
            "[CFAB_CONFIG] Test message with params",
            extra={"details": expected_details},
        )


class TestSpecificErrorClasses(unittest.TestCase):
    """Test specific error classes derived from CFABError."""

    @patch("utils.exceptions.logger")
    def test_configuration_error(self, mock_logger):
        """Should create ConfigurationError with specific details."""
        error = ConfigurationError("Config failed", config_path="/path/to/config")
        self.assertEqual(error.message, "Config failed")
        self.assertEqual(error.error_code, ErrorCode.CONFIG)
        self.assertEqual(error.config_path, "/path/to/config")
        self.assertIn("config_path", error.details)
        self.assertEqual(error.details["config_path"], "/path/to/config")
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_hardware_profiling_error(self, mock_logger):
        """Should create HardwareProfilingError with specific details."""
        error = HardwareProfilingError("GPU error", hardware_type="GPU")
        self.assertEqual(error.message, "GPU error")
        self.assertEqual(error.error_code, ErrorCode.HARDWARE)
        self.assertEqual(error.hardware_type, "GPU")
        self.assertIn("hardware_type", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_thread_management_error(self, mock_logger):
        """Should create ThreadManagementError with specific details."""
        error = ThreadManagementError("Thread died", thread_id="123")
        self.assertEqual(error.error_code, ErrorCode.THREAD)
        self.assertEqual(error.thread_id, "123")
        self.assertIn("thread_id", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_translation_error(self, mock_logger):
        """Should create TranslationError with specific details."""
        error = TranslationError("Missing key", language="en", key="greeting")
        self.assertEqual(error.error_code, ErrorCode.TRANSLATION)
        self.assertEqual(error.language, "en")
        self.assertEqual(error.key, "greeting")
        self.assertIn("language", error.details)
        self.assertIn("key", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_file_operation_error(self, mock_logger):
        """Should create FileOperationError with specific details."""
        error = FileOperationError(
            "Cannot write", file_path="/tmp/test.txt", operation="write"
        )
        self.assertEqual(error.error_code, ErrorCode.FILE)
        self.assertEqual(error.file_path, "/tmp/test.txt")
        self.assertEqual(error.operation, "write")
        self.assertIn("file_path", error.details)
        self.assertIn("operation", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_ui_error(self, mock_logger):
        """Should create UIError with specific details."""
        error = UIError("Button failed", widget_name="MyButton")
        self.assertEqual(error.error_code, ErrorCode.UI)
        self.assertEqual(error.widget_name, "MyButton")
        self.assertIn("widget_name", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_performance_error(self, mock_logger):
        """Should create PerformanceError with specific details."""
        error = PerformanceError("Too slow", operation="render")
        self.assertEqual(error.error_code, ErrorCode.PERFORMANCE)
        self.assertEqual(error.operation, "render")
        self.assertIn("operation", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_validation_error(self, mock_logger):
        """Should create ValidationError with specific details."""
        error = ValidationError("Invalid email", field="email", value="test@")
        self.assertEqual(error.error_code, ErrorCode.VALIDATION)
        self.assertEqual(error.field, "email")
        self.assertEqual(error.value, "test@")
        self.assertIn("field", error.details)
        self.assertIn("value", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_cache_error(self, mock_logger):
        """Should create CacheError with specific details."""
        error = CacheError("Cache miss", cache_key="mykey123")
        self.assertEqual(error.error_code, ErrorCode.CACHE)
        self.assertEqual(error.cache_key, "mykey123")
        self.assertIn("cache_key", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_network_error(self, mock_logger):
        """Should create NetworkError with specific details."""
        error = NetworkError("Connection failed", url="https://example.com")
        self.assertEqual(error.error_code, ErrorCode.NETWORK_CONNECTION_ERROR)
        self.assertEqual(error.url, "https://example.com")
        self.assertIn("url", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_api_error(self, mock_logger):
        """Should create APIError with specific details."""
        error = APIError("API failed", endpoint="/api/test")
        self.assertEqual(error.error_code, ErrorCode.API_ERROR)
        self.assertEqual(error.endpoint, "/api/test")
        self.assertIn("endpoint", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_resource_error(self, mock_logger):
        """Should create ResourceError with specific details."""
        error = ResourceError("Resource unavailable", resource_type="memory")
        self.assertEqual(error.error_code, ErrorCode.RESOURCE_UNAVAILABLE)
        self.assertEqual(error.resource_type, "memory")
        self.assertIn("resource_type", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_security_error(self, mock_logger):
        """Should create SecurityError with specific details."""
        error = SecurityError("Security breach", security_context="login")
        self.assertEqual(error.error_code, ErrorCode.SECURITY_ERROR)
        self.assertEqual(error.security_context, "login")
        self.assertIn("security_context", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_database_error(self, mock_logger):
        """Should create DatabaseError with specific details."""
        error = DatabaseError("Database error", table="users")
        self.assertEqual(error.error_code, ErrorCode.DATABASE_ERROR)
        self.assertEqual(error.table, "users")
        self.assertIn("table", error.details)
        mock_logger.error.assert_called_once()


class TestNewErrorClasses(unittest.TestCase):
    """Test nowych klas wyjątków domenowych."""

    @patch("utils.exceptions.logger")
    def test_network_error(self, mock_logger):
        """Should create NetworkError with specific details."""
        error = NetworkError(
            "Connection failed", url="https://example.com", status_code=404
        )
        self.assertEqual(error.error_code, ErrorCode.NETWORK_CONNECTION_ERROR)
        self.assertEqual(error.url, "https://example.com")
        self.assertEqual(error.status_code, 404)
        self.assertIn("url", error.details)
        self.assertIn("status_code", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_api_error(self, mock_logger):
        """Should create APIError with specific details."""
        error = APIError(
            "API request failed", endpoint="/api/users", method="GET", response_code=500
        )
        self.assertEqual(error.error_code, ErrorCode.API_ERROR)
        self.assertEqual(error.endpoint, "/api/users")
        self.assertEqual(error.method, "GET")
        self.assertEqual(error.response_code, 500)
        self.assertIn("endpoint", error.details)
        self.assertIn("method", error.details)
        self.assertIn("response_code", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_resource_error(self, mock_logger):
        """Should create ResourceError with specific details."""
        error = ResourceError(
            "Resource unavailable", resource_type="memory", resource_id="heap"
        )
        self.assertEqual(error.error_code, ErrorCode.RESOURCE_UNAVAILABLE)
        self.assertEqual(error.resource_type, "memory")
        self.assertEqual(error.resource_id, "heap")
        self.assertIn("resource_type", error.details)
        self.assertIn("resource_id", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_security_error(self, mock_logger):
        """Should create SecurityError with specific details."""
        error = SecurityError(
            "Permission denied", security_context="file_access", user_id="user123"
        )
        self.assertEqual(error.error_code, ErrorCode.SECURITY_ERROR)
        self.assertEqual(error.security_context, "file_access")
        self.assertEqual(error.user_id, "user123")
        self.assertIn("security_context", error.details)
        self.assertIn("user_id", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_database_error(self, mock_logger):
        """Should create DatabaseError with specific details."""
        error = DatabaseError("SQL error", query="SELECT * FROM users", table="users")
        self.assertEqual(error.error_code, ErrorCode.DATABASE_ERROR)
        self.assertEqual(error.query, "SELECT * FROM users")
        self.assertEqual(error.table, "users")
        self.assertIn("query", error.details)
        self.assertIn("table", error.details)
        mock_logger.error.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_specific_error_codes(self, mock_logger):
        """Should use specific error codes when provided."""
        error = NetworkError(
            "Connection timed out",
            url="https://example.com",
            error_code=ErrorCode.NETWORK_TIMEOUT,
        )
        self.assertEqual(error.error_code, ErrorCode.NETWORK_TIMEOUT)
        mock_logger.error.assert_called_once_with(
            f"[{ErrorCode.NETWORK_TIMEOUT.value}] Connection timed out",
            extra={"details": {"url": "https://example.com"}},
        )


class TestHandleErrorGracefully(unittest.TestCase):
    """Test the handle_error_gracefully decorator."""

    @patch("utils.exceptions.logger")
    def test_decorator_handles_cfab_error(self, mock_logger):
        """Should re-raise CFABError without modification (already logged)."""

        @handle_error_gracefully
        def func_raises_cfab():
            raise ConfigurationError("Test CFAB error")

        with self.assertRaises(ConfigurationError):
            func_raises_cfab()
        # CFABError logs itself on creation, so logger.exception shouldn't be called by decorator
        mock_logger.exception.assert_not_called()

    @patch("utils.exceptions.logger")
    def test_decorator_wraps_standard_error(self, mock_logger):
        """Should wrap standard exceptions in CFABError and log them."""

        @handle_error_gracefully
        def func_raises_standard_error():
            raise ValueError("Standard error")

        with self.assertRaises(CFABError) as cm:
            func_raises_standard_error()

        self.assertEqual(cm.exception.error_code, ErrorCode.UNEXPECTED)
        self.assertIn("Standard error", cm.exception.message)
        self.assertIn("func_raises_standard_error", cm.exception.message)
        self.assertIsInstance(cm.exception.original_exception, ValueError)
        mock_logger.exception.assert_called_once()
        # Check that the CFABError (wrapper) also logged itself
        # This will be the second log call for this scenario
        self.assertEqual(
            mock_logger.error.call_count, 1
        )  # Original log by CFABError constructor

    def test_decorator_returns_value(self):
        """Should return the function's result if no exception occurs."""

        @handle_error_gracefully
        def func_returns_value():
            return "Success"

        self.assertEqual(func_returns_value(), "Success")


class TestLogErrorWithContext(unittest.TestCase):
    """Test the log_error_with_context function."""

    @patch("utils.exceptions.logger")
    def test_logs_cfab_error_with_context(self, mock_logger):
        """Should log CFABError with additional context."""
        error = ConfigurationError("CFAB Context Test", config_path="/cfg")
        context = {"user_id": 123, "session_id": "abc"}

        # Clear mock calls from error creation
        mock_logger.reset_mock()

        log_error_with_context(error, context)

        expected_details = {
            "config_path": "/cfg",
            "additional_context": context,
        }
        mock_logger.error.assert_called_once_with(
            "[CFAB_CONFIG] CFAB Context Test (Contextual Log)",
            extra={"details": expected_details},
        )

    @patch("utils.exceptions.logger")
    def test_logs_standard_error_with_context(self, mock_logger):
        """Should log standard error with context and exc_info=True."""
        error = ValueError("Standard Context Test")
        context = {"request_id": "xyz"}

        log_error_with_context(error, context)

        mock_logger.error.assert_called_once_with(
            "Unhandled error: Standard Context Test (Contextual Log)",
            extra={
                "context": context,
                "original_exception_type": "ValueError",
            },
            exc_info=True,
        )


class TestNewHelperFunctions(unittest.TestCase):
    """Test nowych funkcji pomocniczych do obsługi wyjątków."""

    @patch("utils.exceptions.logger")
    def test_try_except_with_context_no_error(self, mock_logger):
        """Should return function result when no error occurs."""

        @try_except_with_context({"component": "TestComponent"})
        def func_no_error():
            return "success"

        result = func_no_error()
        self.assertEqual(result, "success")
        mock_logger.error.assert_not_called()
        mock_logger.exception.assert_not_called()

    @patch("utils.exceptions.logger")
    def test_try_except_with_context_cfab_error(self, mock_logger):
        """Should add context to CFABError and re-raise."""

        @try_except_with_context({"component": "TestComponent"})
        def func_cfab_error():
            raise ValidationError("Invalid data")

        # Reset mock to clear the initial error log from ValidationError
        mock_logger.reset_mock()

        with self.assertRaises(ValidationError):
            func_cfab_error()

        # Dwa wywołania logger.error:
        # 1. Z konstruktora ValidationError
        # 2. Z funkcji log_error_with_context wywoływanej w try_except_with_context
        self.assertEqual(mock_logger.error.call_count, 2)

        # Sprawdzamy, że drugie wywołanie zawiera dodatkowy kontekst
        # (Pierwszy argument to format string, drugi to dodatkowe parametry)
        context_log_call = mock_logger.error.call_args_list[1]
        self.assertIn("(Contextual Log)", context_log_call[0][0])
        self.assertIn("additional_context", context_log_call[1]["extra"]["details"])
        self.assertEqual(
            context_log_call[1]["extra"]["details"]["additional_context"],
            {"component": "TestComponent", "function": "func_cfab_error"},
        )

    @patch("utils.exceptions.logger")
    def test_try_except_with_context_standard_error(self, mock_logger):
        """Should wrap standard error in CFABError with context."""

        @try_except_with_context({"component": "TestComponent"})
        def func_standard_error():
            raise ValueError("Standard error")

        with self.assertRaises(CFABError) as cm:
            func_standard_error()

        self.assertEqual(cm.exception.error_code, ErrorCode.UNEXPECTED)
        self.assertIn("func_standard_error", cm.exception.message)
        self.assertEqual(cm.exception.details["component"], "TestComponent")
        self.assertEqual(cm.exception.details["function"], "func_standard_error")
        mock_logger.exception.assert_called_once()

    @patch("utils.exceptions.logger")
    def test_safe_operation_no_error(self, mock_logger):
        """Should return function result when no error."""

        @safe_operation(default_value=None)
        def func_no_error():
            return "success"

        result = func_no_error()
        self.assertEqual(result, "success")
        mock_logger.error.assert_not_called()

    @patch("utils.exceptions.logger")
    def test_safe_operation_with_error(self, mock_logger):
        """Should return default value and log when error occurs."""

        @safe_operation(default_value=[], error_code=ErrorCode.FILE)
        def func_with_error():
            raise FileNotFoundError("File not found")

        result = func_with_error()
        self.assertEqual(result, [])
        mock_logger.error.assert_called_once()
        # Verify error_code is passed to logger
        self.assertIn("error_code", mock_logger.error.call_args[1]["extra"])
        self.assertEqual(
            mock_logger.error.call_args[1]["extra"]["error_code"], ErrorCode.FILE.value
        )


if __name__ == "__main__":
    unittest.main()
