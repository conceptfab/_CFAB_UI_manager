"""
Unit tests for CFAB UI Manager security and stability improvements.
Tests the new secure command execution, thread management, and validation systems.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from utils.exceptions import (
    CFABError,
    CommandExecutionError,
    ConfigurationError,
    SecurityError,
    ValidationError,
)
from utils.improved_thread_manager import ImprovedThreadManager
from utils.secure_commands import HardwareDetector, SecureCommandRunner
from utils.validators import ConfigValidator, DataIntegrityValidator, InputValidator


class TestSecureCommands(unittest.TestCase):
    """Test secure command execution utilities."""

    def setUp(self):
        self.runner = SecureCommandRunner()

    def test_command_validation_success(self):
        """Test successful command validation."""
        valid_commands = [
            ["echo", "hello"],
            ["python", "--version"],
            ["dir"],  # Windows command
        ]

        for cmd in valid_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.runner._validate_command(cmd))

    def test_command_validation_failure(self):
        """Test command validation with dangerous inputs."""
        dangerous_commands = [
            ["rm", "-rf", "/"],
            ["del", "/f", "/q", "C:\\"],
            ["format", "C:"],
            ["echo", "test; rm -rf /"],
            ["powershell", "-c", "Remove-Item -Recurse"],
        ]

        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.runner._validate_command(cmd))

    def test_timeout_handling(self):
        """Test command timeout handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutError("Command timed out")

            with self.assertRaises(CommandExecutionError):
                self.runner.run_command(["sleep", "10"], timeout=1)

    def test_hardware_detector_cpu_info(self):
        """Test CPU information detection."""
        detector = HardwareDetector()

        with patch("platform.processor") as mock_processor:
            mock_processor.return_value = "Intel(R) Core(TM) i7-8700K"
            cpu_info = detector.get_cpu_info()

            self.assertIsInstance(cpu_info, dict)
            self.assertIn("model", cpu_info)
            self.assertIn("Intel", cpu_info["model"])


class TestImprovedThreadManager(unittest.TestCase):
    """Test improved thread management."""

    def setUp(self):
        self.thread_manager = ImprovedThreadManager()

    def tearDown(self):
        self.thread_manager.cleanup()

    def test_task_execution(self):
        """Test basic task execution."""
        result = []

        def test_task():
            result.append("executed")
            return "success"

        future = self.thread_manager.run_in_thread(test_task)
        future.waitForFinished()

        self.assertEqual(result, ["executed"])
        self.assertEqual(future.result(), "success")

    def test_task_cancellation(self):
        """Test task cancellation."""
        cancelled = []

        def long_task():
            import time

            for i in range(100):
                time.sleep(0.01)
            return "completed"

        task_id = self.thread_manager.run_in_thread(long_task)
        success = self.thread_manager.cancel_task(task_id.property("task_id"))

        # Note: Actual cancellation depends on the task implementation
        # This test mainly verifies the cancellation interface
        self.assertIsInstance(success, bool)

    def test_resource_cleanup(self):
        """Test resource cleanup."""
        # Create some tasks
        for i in range(5):
            self.thread_manager.run_in_thread(lambda: "task")

        # Cleanup should not raise exceptions
        self.thread_manager.cleanup()

        # Verify cleanup worked
        self.assertIsNotNone(self.thread_manager.thread_pool)


class TestValidators(unittest.TestCase):
    """Test validation utilities."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_config_validation_success(self):
        """Test successful configuration validation."""
        valid_config = {
            "language": "pl",
            "show_splash": True,
            "log_to_file": False,
            "log_ui_to_console": True,
        }

        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(valid_config, f)

        result = ConfigValidator.validate_config_file(config_path)
        self.assertEqual(result["language"], "pl")
        self.assertTrue(result["show_splash"])

    def test_config_validation_missing_required(self):
        """Test configuration validation with missing required keys."""
        invalid_config = {
            "show_splash": True,
            # Missing required "language" key
        }

        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(invalid_config, f)

        with self.assertRaises(ConfigurationError):
            ConfigValidator.validate_config_file(config_path)

    def test_config_validation_invalid_language(self):
        """Test configuration validation with invalid language code."""
        invalid_config = {
            "language": "invalid_language_code",
            "show_splash": True,
            "log_to_file": False,
            "log_ui_to_console": True,
        }

        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(invalid_config, f)

        with self.assertRaises(ConfigurationError):
            ConfigValidator.validate_config_file(config_path)

    def test_filename_validation(self):
        """Test filename validation."""
        valid_names = ["config.json", "hardware_profile.json", "test-file.txt"]
        invalid_names = ["con.txt", "file<name>.txt", "file|name.txt", ""]

        for name in valid_names:
            with self.subTest(name=name):
                self.assertTrue(InputValidator.validate_filename(name))

        for name in invalid_names:
            with self.subTest(name=name):
                self.assertFalse(InputValidator.validate_filename(name))

    def test_path_validation(self):
        """Test path validation."""
        valid_paths = [
            self.temp_dir,
            os.path.join(self.temp_dir, "subdir"),
            "/valid/unix/path",
            "C:\\valid\\windows\\path",
        ]

        invalid_paths = [
            "",
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
        ]

        for path in valid_paths:
            with self.subTest(path=path):
                self.assertTrue(InputValidator.validate_path(path))

        for path in invalid_paths:
            with self.subTest(path=path):
                self.assertFalse(InputValidator.validate_path(path))

    def test_json_validation(self):
        """Test JSON string validation."""
        valid_json = ['{"key": "value"}', "[]", '{"nested": {"object": true}}']
        invalid_json = ["invalid", '{"unclosed": ', "{invalid: json}"]

        for json_str in valid_json:
            with self.subTest(json_str=json_str):
                self.assertTrue(InputValidator.validate_json_string(json_str))

        for json_str in invalid_json:
            with self.subTest(json_str=json_str):
                self.assertFalse(InputValidator.validate_json_string(json_str))

    def test_string_sanitization(self):
        """Test string sanitization."""
        test_cases = [
            ("normal string", "normal string"),
            ("string\x00with\x01nulls", "stringwithnulls"),
            ("a" * 2000, "a" * 1000),  # Length limitation
            ("string\nwith\tvalid\nchars", "string\nwith\tvalid\nchars"),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = InputValidator.sanitize_string(input_str)
                self.assertEqual(result, expected)

    def test_hardware_data_validation(self):
        """Test hardware data validation."""
        valid_data = {
            "cpu": {"model": "Intel i7", "cores": 8},
            "memory": {"total": 16000000000, "available": 8000000000},
            "system": {"os": "Windows 10", "architecture": "x64"},
        }

        invalid_data = {
            "cpu": {"cores": 8},  # Missing model
            "memory": {"total": "invalid"},  # Wrong type
        }

        self.assertTrue(DataIntegrityValidator.validate_hardware_data(valid_data))
        self.assertFalse(DataIntegrityValidator.validate_hardware_data(invalid_data))

    def test_benchmark_results_validation(self):
        """Test benchmark results validation."""
        valid_results = {
            "timestamp": "2023-01-01T12:00:00Z",
            "duration": 45.5,
            "score": 1234,
        }

        invalid_results = {
            "timestamp": "2023-01-01T12:00:00Z",
            "duration": -10,  # Negative duration
            "score": "invalid",  # Wrong type
        }

        self.assertTrue(
            DataIntegrityValidator.validate_benchmark_results(valid_results)
        )
        self.assertFalse(
            DataIntegrityValidator.validate_benchmark_results(invalid_results)
        )


class TestExceptionHandling(unittest.TestCase):
    """Test exception handling and error infrastructure."""

    def test_cfab_error_hierarchy(self):
        """Test exception hierarchy."""
        security_error = SecurityError("Test security error")
        validation_error = ValidationError("Test validation error")
        config_error = ConfigurationError("Test config error")

        # All should be instances of CFABError
        self.assertIsInstance(security_error, CFABError)
        self.assertIsInstance(validation_error, CFABError)
        self.assertIsInstance(config_error, CFABError)

    def test_error_graceful_handling(self):
        """Test graceful error handling decorator."""
        from utils.exceptions import handle_error_gracefully

        @handle_error_gracefully
        def test_function_with_error():
            raise ValueError("Test error")

        @handle_error_gracefully
        def test_function_success():
            return "success"

        # Should not raise exception, but return None
        result = test_function_with_error()
        self.assertIsNone(result)

        # Should work normally for successful function
        result = test_function_success()
        self.assertEqual(result, "success")


if __name__ == "__main__":
    # Configure logging for tests
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    unittest.main(verbosity=2)
