# Advanced Configuration Management
# Transactional configuration management with backup and rollback support

import json
import logging
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

from utils.exceptions import ConfigurationError, FileOperationError
from utils.validators import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigTransaction:
    """
    Represents a configuration transaction that can be committed or rolled back
    """

    def __init__(self, config_manager, transaction_id: str):
        self.config_manager = config_manager
        self.transaction_id = transaction_id
        self.changes: Dict[str, Any] = {}
        self.original_values: Dict[str, Any] = {}
        self.committed = False
        self.rolled_back = False

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value within this transaction

        Args:
            key: Configuration key
            value: New value
        """
        if self.committed or self.rolled_back:
            raise ConfigurationError("Transaction is already closed")

        # Store original value if not already stored
        if key not in self.original_values:
            self.original_values[key] = self.config_manager.get(key)

        self.changes[key] = value
        logger.debug(f"Transaction {self.transaction_id}: Set {key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value, including pending changes

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        if key in self.changes:
            return self.changes[key]
        return self.config_manager.get(key, default)

    def commit(self) -> bool:
        """
        Commit the transaction

        Returns:
            True if successful
        """
        if self.committed or self.rolled_back:
            raise ConfigurationError("Transaction is already closed")

        try:
            # Apply all changes
            for key, value in self.changes.items():
                self.config_manager._set_without_transaction(key, value)

            # Save to disk
            self.config_manager.save()

            self.committed = True
            logger.info(
                f"Transaction {self.transaction_id} committed with {len(self.changes)} changes"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to commit transaction {self.transaction_id}: {e}")
            return False

    def rollback(self) -> None:
        """
        Rollback the transaction
        """
        if self.committed or self.rolled_back:
            raise ConfigurationError("Transaction is already closed")

        self.rolled_back = True
        logger.info(f"Transaction {self.transaction_id} rolled back")


class ConfigBackup:
    """
    Manages configuration backups
    """

    def __init__(self, backup_dir: str, max_backups: int = 10):
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        os.makedirs(backup_dir, exist_ok=True)

    def create_backup(self, config_file: str) -> str:
        """
        Create a backup of a configuration file

        Args:
            config_file: Path to configuration file

        Returns:
            Path to backup file
        """
        if not os.path.exists(config_file):
            raise FileOperationError(f"Configuration file not found: {config_file}")

        timestamp = int(time.time())
        filename = os.path.basename(config_file)
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)

        try:
            shutil.copy2(config_file, backup_path)
            logger.debug(f"Created backup: {backup_path}")

            # Clean old backups
            self._cleanup_old_backups(filename)

            return backup_path

        except Exception as e:
            raise FileOperationError(f"Failed to create backup: {e}")

    def restore_backup(self, backup_path: str, target_file: str) -> bool:
        """
        Restore a backup

        Args:
            backup_path: Path to backup file
            target_file: Target configuration file

        Returns:
            True if successful
        """
        try:
            shutil.copy2(backup_path, target_file)
            logger.info(f"Restored backup from {backup_path} to {target_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def list_backups(self, config_filename: str) -> List[str]:
        """
        List available backups for a configuration file

        Args:
            config_filename: Base configuration filename

        Returns:
            List of backup file paths
        """
        backups = []
        prefix = f"{config_filename}."

        for filename in os.listdir(self.backup_dir):
            if filename.startswith(prefix) and filename.endswith(".bak"):
                backups.append(os.path.join(self.backup_dir, filename))

        # Sort by modification time (newest first)
        backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return backups

    def _cleanup_old_backups(self, config_filename: str) -> None:
        """
        Remove old backups beyond the maximum limit

        Args:
            config_filename: Base configuration filename
        """
        backups = self.list_backups(config_filename)

        if len(backups) > self.max_backups:
            for backup in backups[self.max_backups :]:
                try:
                    os.remove(backup)
                    logger.debug(f"Removed old backup: {backup}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {backup}: {e}")


class AdvancedConfigManager:
    """
    Advanced configuration manager with transaction support and backups
    """

    def __init__(
        self, config_file: str, backup_dir: Optional[str] = None, validate: bool = True
    ):
        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file)
        self._data: Dict[str, Any] = {}
        self._transaction_counter = 0
        self._active_transactions: Dict[str, ConfigTransaction] = {}
        self._validate = validate  # Allow disabling validation for tests

        # Setup backup manager
        if backup_dir is None:
            backup_dir = os.path.join(self.config_dir, "backups")
        self.backup_manager = ConfigBackup(backup_dir)

        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)

        # Load configuration
        self.load()

        logger.info(f"Advanced configuration manager initialized: {config_file}")

    def load(self) -> bool:
        """
        Load configuration from file

        Returns:
            True if successful
        """
        try:
            if os.path.exists(self.config_file):
                # Validate before loading (if validation is enabled)
                if self._validate:
                    ConfigValidator.validate_config_file(self.config_file)

                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)

                logger.debug(f"Configuration loaded from {self.config_file}")
            else:
                self._data = {}
                logger.debug("No configuration file found, starting with empty config")

            return True

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def save(self) -> bool:
        """
        Save configuration to file with backup

        Returns:
            True if successful
        """
        try:
            # Create backup if file exists
            if os.path.exists(self.config_file):
                self.backup_manager.create_backup(self.config_file)

            # Write to temporary file first
            temp_file = f"{self.config_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)

            # Validate the temporary file (if validation is enabled)
            if self._validate:
                ConfigValidator.validate_config_file(temp_file)

            # Move temporary file to final location
            shutil.move(temp_file, self.config_file)

            logger.debug(f"Configuration saved to {self.config_file}")
            return True

        except Exception as e:
            # Clean up temporary file
            temp_file = f"{self.config_file}.tmp"
            if os.path.exists(temp_file):
                os.remove(temp_file)

            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        current = self._data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        self._set_without_transaction(key, value)
        self.save()

    def _set_without_transaction(self, key: str, value: Any) -> None:
        """
        Set a configuration value without saving

        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split(".")
        current = self._data

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value
        logger.debug(f"Configuration set: {key} = {value}")

    @contextmanager
    def transaction(self):
        """
        Context manager for configuration transactions

        Usage:
            with config_manager.transaction() as tx:
                tx.set('key1', 'value1')
                tx.set('key2', 'value2')
                # Automatically committed on exit, rolled back on exception
        """
        self._transaction_counter += 1
        transaction_id = f"tx_{self._transaction_counter}"

        transaction = ConfigTransaction(self, transaction_id)
        self._active_transactions[transaction_id] = transaction

        try:
            yield transaction

            # Auto-commit if not already committed or rolled back
            if not transaction.committed and not transaction.rolled_back:
                if not transaction.commit():
                    raise ConfigurationError("Failed to commit transaction")

        except Exception as e:
            # Auto-rollback on exception
            if not transaction.committed and not transaction.rolled_back:
                transaction.rollback()
            raise

        finally:
            # Clean up
            if transaction_id in self._active_transactions:
                del self._active_transactions[transaction_id]

    def migrate(self, migration_function: callable, version: str) -> bool:
        """
        Apply a configuration migration

        Args:
            migration_function: Function that takes (config_data) and returns modified data
            version: Migration version for tracking

        Returns:
            True if migration was applied
        """
        current_version = self.get("_migration_version", "0.0.0")

        if current_version >= version:
            logger.debug(
                f"Migration {version} already applied (current: {current_version})"
            )
            return False

        try:
            with self.transaction() as tx:
                # Apply migration
                migrated_data = migration_function(self._data.copy())

                # Update data
                self._data = migrated_data
                self._data["_migration_version"] = version

                logger.info(f"Applied migration {version}")
                return True

        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            raise ConfigurationError(f"Migration failed: {e}")

    def restore_from_backup(self, backup_index: int = 0) -> bool:
        """
        Restore configuration from a backup

        Args:
            backup_index: Index of backup to restore (0 = most recent)

        Returns:
            True if successful
        """
        config_filename = os.path.basename(self.config_file)
        backups = self.backup_manager.list_backups(config_filename)

        if not backups or backup_index >= len(backups):
            logger.error(f"No backup available at index {backup_index}")
            return False

        backup_path = backups[backup_index]

        try:
            # Validate backup before restoring
            ConfigValidator.validate_config_file(backup_path)

            # Restore backup
            if self.backup_manager.restore_backup(backup_path, self.config_file):
                self.load()  # Reload from restored file
                logger.info(f"Configuration restored from backup: {backup_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")

        return False

    def get_backup_info(self) -> List[Dict[str, Any]]:
        """
        Get information about available backups

        Returns:
            List of backup information dictionaries
        """
        config_filename = os.path.basename(self.config_file)
        backups = self.backup_manager.list_backups(config_filename)

        backup_info = []
        for backup in backups:
            stat = os.stat(backup)
            backup_info.append(
                {
                    "path": backup,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": time.ctime(stat.st_mtime),
                }
            )

        return backup_info


# Factory function for creating configuration managers
def create_config_manager(
    config_file: str, backup_dir: Optional[str] = None, validate: bool = True
) -> AdvancedConfigManager:
    """
    Create an advanced configuration manager

    Args:
        config_file: Path to configuration file
        backup_dir: Optional backup directory
        validate: Whether to validate configuration (disable for tests)

    Returns:
        Configured AdvancedConfigManager instance
    """
    return AdvancedConfigManager(config_file, backup_dir, validate)
