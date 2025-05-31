import json
import logging
import os
from typing import Any, Dict, Optional

# TODO: Uncomment and adjust imports when ConfigValidator and ConfigurationError are integrated
# from utils.validators import ConfigValidator
# from utils.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class ConfigManager:
    _instance: Optional['ConfigManager'] = None
    _config_data: Dict[str, Any] = {}
    _config_file_path: str # Will be initialized in __new__ or _load_initial_config
    # _validator: Optional[ConfigValidator] = None # Example if validator is integrated

    def __new__(cls, *args, **kwargs) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize attributes that should only be set once for the instance
            cls._instance._config_data = {}
            
            # Determine initial config file path
            initial_config_path = kwargs.get('config_file_path', "config.json")
            if not os.path.isabs(initial_config_path):
                # Assuming relative paths should be based on the current working directory,
                # or a project root directory if available. For now, CWD.
                # This should ideally be made more robust, e.g., by passing a base_path.
                cls._instance._config_file_path = os.path.abspath(initial_config_path)
            else:
                cls._instance._config_file_path = initial_config_path
            
            # cls._instance._validator = ConfigValidator() # If validator is to be used
            cls._instance._load_initial_config() # Load config using the determined path
        return cls._instance

    def _load_initial_config(self, file_path: Optional[str] = None) -> None:
        path_to_load = file_path or self._config_file_path
        
        if not os.path.isabs(path_to_load):
            path_to_load = os.path.abspath(path_to_load)
        
        # Update instance's config file path if a new one is explicitly passed for loading
        self._config_file_path = path_to_load

        try:
            if os.path.exists(self._config_file_path):
                with open(self._config_file_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                # TODO: Add validation step here if validator is integrated
                # if self._validator and not self._validator.validate(loaded_data):
                #     logger.error(f"Configuration from {self._config_file_path} is invalid according to schema.")
                #     self._config_data = self._get_default_config()
                # else:
                self._config_data = loaded_data
                logger.info(f"Configuration loaded from {self._config_file_path}")
            else:
                logger.warning(f"Config file '{self._config_file_path}' not found. Using default configuration.")
                self._config_data = self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from '{self._config_file_path}': {e}. Using default configuration.")
            self._config_data = self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load configuration from '{self._config_file_path}': {e}. Using default configuration.")
            self._config_data = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        logger.info("Providing default configuration structure.")
        return {
            "application_name": "CFAB UI Manager",
            "version": "1.0.0",
            "show_splash": True,
            "log_to_file": False,
            "log_filename": "app.log",
            "log_level": "INFO",
            "language": "pl",
            "supported_languages": ["en", "pl"],
            "last_used_profile": None,
            "ui_theme": "default",
        }

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config_data
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    logger.warning(f"Config path for key '{key}' is invalid (intermediate value is not a dictionary). Returning default: {default}")
                    return default
            return value
        except KeyError:
            logger.warning(f"Config key '{key}' not found. Returning default: {default}")
            return default
        except TypeError:
             logger.warning(f"Config path for key '{key}' is invalid (TypeError). Returning default: {default}")
             return default

    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        data_ptr = self._config_data
        
        if not keys:
            logger.warning("Attempted to set config with an empty key.")
            return

        for k in keys[:-1]:
            if not isinstance(data_ptr.get(k), dict):
                data_ptr[k] = {}
            data_ptr = data_ptr[k]
        
        data_ptr[keys[-1]] = value
        logger.info(f"Config key '{key}' set to '{value}'. Call save_config() to persist.")

    def save_config(self, file_path: Optional[str] = None) -> bool:
        path_to_save = file_path or self._config_file_path
        if not os.path.isabs(path_to_save):
            path_to_save = os.path.abspath(path_to_save)

        # TODO: Add validation step here if validator is integrated
        # if self._validator and not self._validator.validate(self._config_data):
        #     logger.error("Attempted to save invalid configuration.")
        #     return False
        try:
            os.makedirs(os.path.dirname(path_to_save), exist_ok=True)
            with open(path_to_save, "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuration saved to {path_to_save}")
            # Update self._config_file_path if saved to a new location successfully
            self._config_file_path = path_to_save
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration to {path_to_save}: {e}")
            return False

    def reload_config(self, file_path: Optional[str] = None) -> None:
        logger.info(f"Reloading configuration from '{file_path or self._config_file_path}'...")
        self._load_initial_config(file_path) # file_path here can be None

    def get_config_file_path(self) -> str:
        return self._config_file_path

    def get_all_config(self) -> Dict[str, Any]:
        """Returns a copy of the entire configuration data."""
        return self._config_data.copy()

# Global instance (singleton)
# To instantiate with a specific config file:
# config_manager = ConfigManager(config_file_path="path/to/your/config.json")
# Otherwise, it defaults to "config.json" in the CWD or path passed to constructor.
config_manager = ConfigManager()
