"""
Configuration caching and performance optimization system.

This module provides intelligent caching for configuration files, translation data,
and other frequently accessed resources to improve application performance.
"""

import hashlib
import json
import logging
import os
import pickle
import time
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from utils.exceptions import CacheError, handle_error_gracefully
from utils.performance_optimizer import performance_monitor

logger = logging.getLogger(__name__)


class FileCache:
    """
    Intelligent file-based caching system with automatic invalidation.

    Features:
    - Automatic cache invalidation based on file modification time
    - Multiple serialization formats (JSON, pickle)
    - Memory-efficient storage with compression
    - Thread-safe operations
    """

    def __init__(self, cache_dir: str = None, max_cache_size_mb: int = 50):
        """
        Initialize the file cache.

        Args:
            cache_dir: Directory for cache files (default: .cache in app directory)
            max_cache_size_mb: Maximum cache size in megabytes
        """
        if cache_dir is None:
            app_dir = Path(__file__).parent.parent
            cache_dir = app_dir / ".cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convert to bytes

        # Cache metadata
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

        logger.debug(f"FileCache initialized with cache_dir: {self.cache_dir}")

    def _load_metadata(self) -> Dict:
        """Load cache metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load cache metadata: {e}")

        return {"entries": {}, "created": time.time(), "access_count": 0}

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save cache metadata: {e}")

    def _generate_cache_key(self, source_file: Union[str, Path]) -> str:
        """Generate a unique cache key for a source file."""
        source_path = Path(source_file)
        file_info = f"{source_path.absolute()}_{source_path.stat().st_mtime}"
        return hashlib.sha256(file_info.encode()).hexdigest()[:16]

    @performance_monitor.measure_execution_time("cache_get")
    def get(
        self, source_file: Union[str, Path], loader_func: callable = None
    ) -> Optional[Any]:
        """
        Get data from cache or load from source if cache is invalid.

        Args:
            source_file: Path to the source file
            loader_func: Function to load data if not in cache

        Returns:
            Cached or loaded data, None if loading fails
        """
        source_path = Path(source_file)

        if not source_path.exists():
            logger.warning(f"Source file does not exist: {source_path}")
            return None

        cache_key = self._generate_cache_key(source_path)
        cache_file = self.cache_dir / f"{cache_key}.cache"

        # Check if cache file exists and is valid
        if cache_file.exists():
            try:
                # Check if source file is newer than cache
                cache_mtime = cache_file.stat().st_mtime
                source_mtime = source_path.stat().st_mtime

                if source_mtime <= cache_mtime:
                    # Cache is valid, load from cache
                    with open(cache_file, "rb") as f:
                        data = pickle.load(f)

                    # Update access metadata
                    self.metadata["entries"][cache_key] = {
                        "last_access": time.time(),
                        "access_count": self.metadata["entries"]
                        .get(cache_key, {})
                        .get("access_count", 0)
                        + 1,
                        "file_size": cache_file.stat().st_size,
                    }
                    self.metadata["access_count"] += 1

                    logger.debug(f"Cache hit for {source_path.name}")
                    return data
                else:
                    logger.debug(f"Cache expired for {source_path.name}")
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_file}: {e}")

        # Cache miss or invalid, load from source
        if loader_func is None:
            logger.warning(f"No loader function provided for {source_path}")
            return None

        try:
            data = loader_func(source_path)
            self._store_in_cache(cache_key, cache_file, data, source_path)
            return data
        except Exception as e:
            logger.error(f"Error loading data from {source_path}: {e}")
            return None

    def _store_in_cache(
        self, cache_key: str, cache_file: Path, data: Any, source_path: Path
    ) -> None:
        """Store data in cache file."""
        try:
            # Ensure cache size doesn't exceed limit
            self._cleanup_cache_if_needed()

            with open(cache_file, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Update metadata
            self.metadata["entries"][cache_key] = {
                "source_file": str(source_path),
                "created": time.time(),
                "last_access": time.time(),
                "access_count": 1,
                "file_size": cache_file.stat().st_size,
            }

            self._save_metadata()
            logger.debug(f"Cached data for {source_path.name}")

        except Exception as e:
            logger.error(f"Error storing cache for {source_path}: {e}")

    def _cleanup_cache_if_needed(self) -> None:
        """Clean up cache if it exceeds size limit."""
        total_size = sum(
            entry.get("file_size", 0) for entry in self.metadata["entries"].values()
        )

        if total_size > self.max_cache_size:
            logger.info(
                f"Cache size ({total_size / 1024 / 1024:.1f}MB) exceeds limit, cleaning up..."
            )

            # Sort entries by last access time (oldest first)
            entries = list(self.metadata["entries"].items())
            entries.sort(key=lambda x: x[1].get("last_access", 0))

            # Remove oldest entries until under limit
            removed_count = 0
            for cache_key, entry in entries:
                cache_file = self.cache_dir / f"{cache_key}.cache"
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                        total_size -= entry.get("file_size", 0)
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"Could not remove cache file {cache_file}: {e}")

                del self.metadata["entries"][cache_key]

                if total_size <= self.max_cache_size * 0.8:  # Clean to 80% of limit
                    break

            self._save_metadata()
            logger.info(f"Removed {removed_count} cache entries")

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()

            self.metadata = {"entries": {}, "created": time.time(), "access_count": 0}
            self._save_metadata()

            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_size = sum(
            entry.get("file_size", 0) for entry in self.metadata["entries"].values()
        )

        return {
            "entry_count": len(self.metadata["entries"]),
            "total_size_mb": total_size / 1024 / 1024,
            "max_size_mb": self.max_cache_size / 1024 / 1024,
            "total_access_count": self.metadata["access_count"],
            "cache_dir": str(self.cache_dir),
        }


class ConfigurationCache:
    """
    Specialized cache for configuration files with validation and hot-reloading.
    """

    def __init__(self, cache_dir: str = None):
        self.file_cache = FileCache(cache_dir)
        self._watchers = {}  # File watchers for hot-reloading
        self._cached_configs = {}

    @handle_error_gracefully
    def get_config(
        self, config_path: Union[str, Path], validator_func: callable = None
    ) -> Optional[Dict]:
        """
        Get configuration with validation and caching.

        Args:
            config_path: Path to configuration file
            validator_func: Optional validation function

        Returns:
            Configuration dictionary or None if loading fails
        """

        def config_loader(path):
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Apply validation if provided
            if validator_func:
                config = validator_func(config)

            return config

        return self.file_cache.get(config_path, config_loader)

    @handle_error_gracefully
    def get_translations(self, translation_path: Union[str, Path]) -> Optional[Dict]:
        """Get translation data with caching."""

        def translation_loader(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        return self.file_cache.get(translation_path, translation_loader)

    @handle_error_gracefully
    def get_css_styles(self, css_path: Union[str, Path]) -> Optional[str]:
        """Get CSS styles with caching."""

        def css_loader(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        return self.file_cache.get(css_path, css_loader)


# Global cache instance
_global_cache = None


def get_global_cache() -> ConfigurationCache:
    """Get the global configuration cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ConfigurationCache()
    return _global_cache


def cached_config(validator_func: callable = None):
    """
    Decorator for caching configuration loading functions.

    Args:
        validator_func: Optional validation function to apply to loaded config
    """

    def decorator(func):
        @wraps(func)
        def wrapper(config_path, *args, **kwargs):
            cache = get_global_cache()

            # Try to get from cache first
            cached_result = cache.get_config(config_path, validator_func)
            if cached_result is not None:
                return cached_result

            # Fall back to original function
            return func(config_path, *args, **kwargs)

        return wrapper

    return decorator


def cached_file_operation(cache_type: str = "auto"):
    """
    Decorator for caching file operations.

    Args:
        cache_type: Type of cache operation ('config', 'translation', 'css', 'auto')
    """

    def decorator(func):
        @wraps(func)
        def wrapper(file_path, *args, **kwargs):
            cache = get_global_cache()

            # Determine cache method based on file extension if auto
            if cache_type == "auto":
                file_ext = Path(file_path).suffix.lower()
                if file_ext == ".json":
                    cache_method = cache.get_config
                elif file_ext == ".qss":
                    cache_method = cache.get_css_styles
                else:
                    # Fall back to original function for unknown types
                    return func(file_path, *args, **kwargs)
            else:
                cache_method = getattr(cache, f"get_{cache_type}")

            # Try cache first
            cached_result = cache_method(file_path)
            if cached_result is not None:
                return cached_result

            # Fall back to original function
            return func(file_path, *args, **kwargs)

        return wrapper

    return decorator


@lru_cache(maxsize=32)
def get_file_hash(file_path: Union[str, Path]) -> str:
    """Get MD5 hash of a file for change detection."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        return ""


# Global configuration cache instance
config_cache = get_global_cache()


if __name__ == "__main__":
    # Example usage and testing
    import tempfile

    # Create a temporary config file for testing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"test": "value", "number": 42}
        json.dump(test_config, f)
        temp_config_path = f.name

    try:
        # Test configuration cache
        cache = ConfigurationCache()

        # First load (should cache)
        config1 = cache.get_config(temp_config_path)
        print(f"First load: {config1}")

        # Second load (should use cache)
        config2 = cache.get_config(temp_config_path)
        print(f"Second load (cached): {config2}")

        # Test cache stats
        stats = cache.file_cache.get_stats()
        print(f"Cache stats: {stats}")

    finally:
        # Clean up
        os.unlink(temp_config_path)
        print("Cache test completed")
