"""
Input validation utilities for CFAB UI Manager.
Provides secure validation for configuration files, user inputs, and data integrity.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


class ConfigValidator:
    """
    Validates configuration files and user inputs.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the validator with an optional configuration dictionary.

        Args:
            config: The configuration dictionary to validate.
        """
        self.config = config if config is not None else {}

    # Required configuration keys and their expected types
    REQUIRED_CONFIG_KEYS = {
        "language": str,
        "show_splash": bool,
        "log_to_file": bool,
        "log_to_system_console": bool,  # Zmieniona nazwa z log_ui_to_console
    }

    # Optional configuration keys and their expected types
    OPTIONAL_CONFIG_KEYS = {
        "theme": str,
        "window_geometry": dict,
        "recent_files": list,
        "hardware_scan_interval": int,
        "auto_save": bool,
        "debug_mode": bool,
        "window_size": dict,
        "window_position": dict,
        "remember_window_size": bool,
        "log_level": str,
        "logger_debug_mode": bool,
    }

    # Valid language codes
    VALID_LANGUAGES = ["pl", "en"]

    def validate(self) -> None:
        """
        Validates the loaded configuration.
        Raises ValidationError if the configuration is invalid.
        """
        if not self.config:
            # This case should ideally be handled before calling validate,
            # but as a safeguard:
            raise ValidationError("Configuration is empty or not loaded.")

        self._check_required_keys()
        self._check_optional_keys()
        self._validate_specific_values()
        # Add more validation steps as needed
        logger.info("Configuration validated successfully.")

    @classmethod
    def validate_config_file(cls, config_path: str) -> Dict[str, Any]:
        """
        Validates a configuration file and returns the validated config.

        Args:
            config_path: Path to the configuration file

        Returns:
            Dict containing validated configuration

        Raises:
            ValidationError: If validation fails
            ConfigurationError: If file structure is invalid
        """
        if not os.path.exists(config_path):
            raise ValidationError(f"Configuration file not found: {config_path}")

        if not os.path.isfile(config_path):
            raise ValidationError(f"Configuration path is not a file: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {e}", config_path=config_path
            )
        except Exception as e:
            raise ValidationError(f"Failed to read configuration file: {e}")

        if not isinstance(config, dict):
            raise ConfigurationError(
                "Configuration file must contain a JSON object", config_path=config_path
            )

        return cls._validate_config_structure(config, config_path)

    @classmethod
    def _validate_config_structure(
        cls, config: Dict[str, Any], config_path: str
    ) -> Dict[str, Any]:
        """
        Validates the structure and content of configuration data.
        """
        validated_config = {}

        # Check required keys
        for key, expected_type in cls.REQUIRED_CONFIG_KEYS.items():
            if key not in config:
                raise ConfigurationError(
                    f"Missing required configuration key: {key}",
                    config_path=config_path,
                )

            value = config[key]
            if not isinstance(value, expected_type):
                raise ConfigurationError(
                    f"Invalid type for '{key}': expected {expected_type.__name__}, got {type(value).__name__}",
                    config_path=config_path,
                )

            # Additional validation for specific keys
            if key == "language" and value not in cls.VALID_LANGUAGES:
                raise ConfigurationError(
                    f"Invalid language code '{value}'. Must be one of: {cls.VALID_LANGUAGES}",
                    config_path=config_path,
                )

            validated_config[key] = value

        # Check optional keys
        for key, expected_type in cls.OPTIONAL_CONFIG_KEYS.items():
            if key in config:
                value = config[key]
                if not isinstance(value, expected_type):
                    logger.warning(
                        f"Invalid type for optional key '{key}': expected {expected_type.__name__}, "
                        f"got {type(value).__name__}. Skipping."
                    )
                    continue
                validated_config[key] = value

        # Check for unknown keys
        known_keys = set(cls.REQUIRED_CONFIG_KEYS.keys()) | set(
            cls.OPTIONAL_CONFIG_KEYS.keys()
        )
        unknown_keys = set(config.keys()) - known_keys
        if unknown_keys:
            logger.warning(f"Unknown configuration keys found: {unknown_keys}")

        return validated_config

    @classmethod
    def validate_hardware_profile(cls, profile_path: str) -> Dict[str, Any]:
        """
        Validates a hardware profile file.

        Args:
            profile_path: Path to the hardware profile file

        Returns:
            Dict containing validated profile data

        Raises:
            ValidationError: If validation fails
        """
        if not os.path.exists(profile_path):
            raise ValidationError(f"Hardware profile file not found: {profile_path}")

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in hardware profile: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to read hardware profile: {e}")

        if not isinstance(profile, dict):
            raise ValidationError("Hardware profile must be a JSON object")

        # Check for required profile fields
        required_fields = [
            "uuid",
            "timestamp",
            "system",
            "processor",
            "cpu_count_logical",
            "cpu_count_physical",
            "memory_total",
            "gpu",
        ]

        # Sprawdź wszystkie wymagane pola i zapisz listę brakujących
        missing_fields = []
        for field in required_fields:
            if field not in profile:
                missing_fields.append(field)
                logger.error(f"Walidacja profilu: brakujące pole '{field}'")
            elif field == "timestamp":
                logger.debug(
                    f"Walidacja profilu: pole timestamp obecne, wartość: '{profile[field]}', typ: {type(profile[field])}"
                )

        # Jeśli są brakujące pola, zgłoś wyjątek
        if missing_fields:
            raise ValidationError(
                f"Missing required field(s) in hardware profile: {', '.join(missing_fields)}"
            )

        # Validate field types
        if not isinstance(profile["uuid"], str):
            raise ValidationError("UUID must be a string")
        if not isinstance(profile["timestamp"], str):
            raise ValidationError("Timestamp must be a string")
        if not isinstance(profile["system"], str):
            raise ValidationError("System must be a string")
        if not isinstance(profile["processor"], str):
            raise ValidationError("Processor must be a string")
        if not isinstance(profile["cpu_count_logical"], int):
            raise ValidationError("CPU count logical must be an integer")
        if not isinstance(profile["cpu_count_physical"], int):
            raise ValidationError("CPU count physical must be an integer")
        if not isinstance(profile["memory_total"], (int, float)):
            raise ValidationError("Memory total must be a number")
        if not isinstance(profile["gpu"], str):
            raise ValidationError("GPU must be a string")

        return profile


class InputValidator:
    """
    Validates user inputs and form data.
    """

    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validates a filename for security and filesystem compatibility.

        Args:
            filename: The filename to validate

        Returns:
            True if valid, False otherwise
        """
        if not filename or not isinstance(filename, str):
            return False

        # Check for dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\0"]
        if any(char in filename for char in dangerous_chars):
            return False

        # Check for reserved names on Windows
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]
        if filename.upper().split(".")[0] in reserved_names:
            return False

        # Check length
        if len(filename) > 255:
            return False

        return True

    @staticmethod
    def validate_path(path: str, must_exist: bool = False) -> bool:
        """
        Validates a file or directory path.

        Args:
            path: The path to validate
            must_exist: Whether the path must exist

        Returns:
            True if valid, False otherwise
        """
        if not path or not isinstance(path, str):
            return False

        try:
            # Use pathlib for cross-platform path validation
            path_obj = Path(path)

            # Check if path exists if required
            if must_exist and not path_obj.exists():
                return False

            # Check if path is absolute and within allowed boundaries
            if path_obj.is_absolute():
                # Prevent path traversal attacks
                resolved_path = path_obj.resolve()
                if ".." in str(resolved_path):
                    return False

            return True
        except (ValueError, OSError):
            return False

    @staticmethod
    def validate_json_string(json_str: str) -> bool:
        """
        Validates a JSON string.

        Args:
            json_str: The JSON string to validate

        Returns:
            True if valid JSON, False otherwise
        """
        if not isinstance(json_str, str):
            return False

        try:
            json.loads(json_str)
            return True
        except json.JSONDecodeError:
            return False

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """
        Sanitizes a string by removing dangerous characters and limiting length.

        Args:
            input_str: The string to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(input_str, str):
            return ""

        # Remove null bytes and control characters (except newlines and tabs)
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", input_str)

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @staticmethod
    def validate_language_code(lang_code: str) -> bool:
        """
        Validates a language code.

        Args:
            lang_code: The language code to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(lang_code, str):
            return False

        # Simple validation for ISO 639-1 codes
        return bool(re.match(r"^[a-z]{2}$", lang_code.lower()))


class DataIntegrityValidator:
    """
    Validates data integrity and prevents corruption.
    """

    @staticmethod
    def validate_hardware_data(data: Dict[str, Any]) -> bool:
        """
        Validates hardware profiling data structure.

        Args:
            data: Hardware data dictionary

        Returns:
            True if data structure is valid, False otherwise
        """
        if not isinstance(data, dict):
            return False

        # Check for basic required structure
        required_sections = ["cpu", "memory", "system"]
        for section in required_sections:
            if section not in data or not isinstance(data[section], dict):
                logger.warning(f"Invalid or missing hardware data section: {section}")
                return False

        # Validate CPU data
        cpu_data = data["cpu"]
        if "model" not in cpu_data or not isinstance(cpu_data["model"], str):
            return False

        # Validate memory data
        memory_data = data["memory"]
        if "total" not in memory_data or not isinstance(
            memory_data["total"], (int, float)
        ):
            return False

        return True

    @staticmethod
    def validate_benchmark_results(results: Dict[str, Any]) -> bool:
        """
        Validates benchmark results data.

        Args:
            results: Benchmark results dictionary

        Returns:
            True if results are valid, False otherwise
        """
        if not isinstance(results, dict):
            return False

        # Check for required fields
        required_fields = ["timestamp", "duration", "score"]
        for field in required_fields:
            if field not in results:
                return False

        # Validate timestamp
        if not isinstance(results["timestamp"], (str, float, int)):
            return False

        # Validate duration (should be positive)
        if (
            not isinstance(results["duration"], (int, float))
            or results["duration"] <= 0
        ):
            return False

        # Validate score (should be numeric)
        if not isinstance(results["score"], (int, float)):
            return False

        return True
