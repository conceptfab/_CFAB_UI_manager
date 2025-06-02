"""
Tests for the config cache module
"""

import json
import os
import pickle
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from utils.config_cache import (
    ConfigurationCache,
    FileCache,
    cached_config,
    cached_file_operation,
    get_file_hash,
    get_global_cache,
)


class FileCacheTest(unittest.TestCase):
    """Test the FileCache class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        self.cache = FileCache(cache_dir=self.cache_dir, max_cache_size_mb=1)

        # Create a test source file
        self.source_file = os.path.join(self.temp_dir, "test.json")
        self.test_data = {"test": "value", "number": 42}
        with open(self.source_file, "w") as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cache_initialization(self):
        """Should initialize cache with proper directory and metadata"""
        self.assertTrue(os.path.exists(self.cache_dir))
        self.assertIsInstance(self.cache.metadata, dict)
        self.assertIn("entries", self.cache.metadata)

    def test_cache_key_generation(self):
        """Should generate consistent cache keys"""
        key1 = self.cache._generate_cache_key(self.source_file)
        key2 = self.cache._generate_cache_key(self.source_file)
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 16)  # SHA256 hash truncated to 16 chars

    def test_cache_miss_and_store(self):
        """Should load data on cache miss and store in cache"""

        def loader_func(path):
            with open(path, "r") as f:
                return json.load(f)

        # First call should be cache miss
        result = self.cache.get(self.source_file, loader_func)
        self.assertEqual(result, self.test_data)

        # Check that cache file was created
        cache_key = self.cache._generate_cache_key(self.source_file)
        cache_file = Path(self.cache_dir) / f"{cache_key}.cache"
        self.assertTrue(cache_file.exists())

    def test_cache_hit(self):
        """Should use cached data on subsequent calls"""

        def loader_func(path):
            with open(path, "r") as f:
                return json.load(f)

        # First call to populate cache
        self.cache.get(self.source_file, loader_func)

        # Mock the loader to ensure it's not called on cache hit
        loader_mock = MagicMock(side_effect=loader_func)

        # Second call should use cache
        result = self.cache.get(self.source_file, loader_mock)
        self.assertEqual(result, self.test_data)
        loader_mock.assert_not_called()

    def test_cache_invalidation_on_file_change(self):
        """Should invalidate cache when source file changes"""

        def loader_func(path):
            with open(path, "r") as f:
                return json.load(f)

        # First call to populate cache
        original_result = self.cache.get(self.source_file, loader_func)

        # Modify source file
        time.sleep(0.1)  # Ensure different mtime
        modified_data = {"test": "modified", "number": 100}
        with open(self.source_file, "w") as f:
            json.dump(modified_data, f)

        # Should reload from source due to cache invalidation
        result = self.cache.get(self.source_file, loader_func)
        self.assertEqual(result, modified_data)
        self.assertNotEqual(result, original_result)

    def test_cache_cleanup_on_size_limit(self):
        """Should clean up old entries when cache size exceeds limit"""
        # Create multiple cache entries to exceed size limit
        for i in range(10):
            test_file = os.path.join(self.temp_dir, f"test_{i}.json")
            with open(test_file, "w") as f:
                json.dump({"data": "x" * 10000}, f)  # Large data

            def loader_func(path):
                with open(path, "r") as f:
                    return json.load(f)

            self.cache.get(test_file, loader_func)

        # Cache should have cleaned up some entries
        total_size = sum(
            entry.get("file_size", 0)
            for entry in self.cache.metadata["entries"].values()
        )
        max_size = self.cache.max_cache_size
        self.assertLessEqual(total_size, max_size)

    def test_cache_clear(self):
        """Should clear all cache entries"""

        def loader_func(path):
            with open(path, "r") as f:
                return json.load(f)

        # Populate cache
        self.cache.get(self.source_file, loader_func)
        self.assertGreater(len(self.cache.metadata["entries"]), 0)

        # Clear cache
        self.cache.clear()
        self.assertEqual(len(self.cache.metadata["entries"]), 0)

    def test_cache_stats(self):
        """Should provide accurate cache statistics"""

        def loader_func(path):
            with open(path, "r") as f:
                return json.load(f)

        # Populate cache
        self.cache.get(self.source_file, loader_func)

        stats = self.cache.get_stats()
        self.assertIn("entry_count", stats)
        self.assertIn("total_size_mb", stats)
        self.assertIn("max_size_mb", stats)
        self.assertIn("total_access_count", stats)
        self.assertGreater(stats["entry_count"], 0)

    def test_missing_source_file(self):
        """Should handle missing source files gracefully"""

        def loader_func(path):
            with open(path, "r") as f:
                return json.load(f)

        missing_file = os.path.join(self.temp_dir, "missing.json")
        result = self.cache.get(missing_file, loader_func)
        self.assertIsNone(result)

    def test_no_loader_function(self):
        """Should handle missing loader function gracefully"""
        result = self.cache.get(self.source_file, None)
        self.assertIsNone(result)


class ConfigurationCacheTest(unittest.TestCase):
    """Test the ConfigurationCache class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        self.config_cache = ConfigurationCache(cache_dir=self.cache_dir)

        # Create test configuration file
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.config_data = {
            "app_name": "Test App",
            "version": "1.0.0",
            "settings": {"debug": True, "timeout": 30},
        }
        with open(self.config_file, "w") as f:
            json.dump(self.config_data, f)

        # Create test translation file
        self.translation_file = os.path.join(self.temp_dir, "test_trans.json")
        self.translation_data = {"hello": "Cześć", "goodbye": "Do widzenia"}
        with open(self.translation_file, "w") as f:
            json.dump(self.translation_data, f)

        # Create test CSS file
        self.css_file = os.path.join(self.temp_dir, "test_styles.qss")
        self.css_data = "QWidget { background-color: #f0f0f0; }"
        with open(self.css_file, "w") as f:
            f.write(self.css_data)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_config(self):
        """Should load and cache configuration files"""
        # First call should load from file
        config = self.config_cache.get_config(self.config_file)
        self.assertEqual(config, self.config_data)

        # Second call should use cache
        config2 = self.config_cache.get_config(self.config_file)
        self.assertEqual(config2, self.config_data)

    def test_get_config_with_validator(self):
        """Should apply validator function to loaded config"""

        def validator(config):
            # Ensure debug is always False
            config["settings"]["debug"] = False
            return config

        config = self.config_cache.get_config(self.config_file, validator)
        self.assertFalse(config["settings"]["debug"])

    def test_get_translations(self):
        """Should load and cache translation files"""
        translations = self.config_cache.get_translations(self.translation_file)
        self.assertEqual(translations, self.translation_data)

    def test_get_css_styles(self):
        """Should load and cache CSS files"""
        styles = self.config_cache.get_css_styles(self.css_file)
        self.assertEqual(styles, self.css_data)

    def test_invalid_json_file(self):
        """Should handle invalid JSON files gracefully"""
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, "w") as f:
            f.write("{ invalid json")

        config = self.config_cache.get_config(invalid_file)
        self.assertIsNone(config)


class CacheDecoratorsTest(unittest.TestCase):
    """Test cache decorator functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Create test config file
        self.config_file = os.path.join(self.temp_dir, "test.json")
        self.config_data = {"test": "value"}
        with open(self.config_file, "w") as f:
            json.dump(self.config_data, f)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cached_config_decorator(self):
        """Should cache config loading with decorator"""

        @cached_config()
        def load_config(path):
            with open(path, "r") as f:
                return json.load(f)

        # First call should load from file
        config1 = load_config(self.config_file)
        self.assertEqual(config1, self.config_data)

        # Second call should use cache
        config2 = load_config(self.config_file)
        self.assertEqual(config2, self.config_data)

    def test_cached_file_operation_decorator(self):
        """Should cache file operations with decorator"""

        @cached_file_operation(cache_type="config")
        def load_file(path):
            with open(path, "r") as f:
                return json.load(f)

        # First call should load from file
        data1 = load_file(self.config_file)
        self.assertEqual(data1, self.config_data)

        # Second call should use cache
        data2 = load_file(self.config_file)
        self.assertEqual(data2, self.config_data)

    def test_cached_file_operation_auto_type(self):
        """Should auto-detect file type for caching"""

        @cached_file_operation(cache_type="auto")
        def load_file(path):
            with open(path, "r") as f:
                return json.load(f)

        # Should work with JSON files
        data = load_file(self.config_file)
        self.assertEqual(data, self.config_data)


class UtilityFunctionsTest(unittest.TestCase):
    """Test utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, "w") as f:
            f.write("test content")

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_file_hash(self):
        """Should generate consistent file hashes"""
        hash1 = get_file_hash(self.test_file)
        hash2 = get_file_hash(self.test_file)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 32)  # MD5 hash length

    def test_get_file_hash_nonexistent(self):
        """Should handle nonexistent files gracefully"""
        missing_file = os.path.join(self.temp_dir, "missing.txt")
        hash_result = get_file_hash(missing_file)
        self.assertEqual(hash_result, "")

    def test_global_cache_singleton(self):
        """Should return same instance for global cache"""
        cache1 = get_global_cache()
        cache2 = get_global_cache()
        self.assertIs(cache1, cache2)


class CacheIntegrationTest(unittest.TestCase):
    """Integration tests for cache consistency"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")
        self.config_data = {"test": "original"}

        with open(self.config_file, "w") as f:
            json.dump(self.config_data, f)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_cache_consistency_with_config_json(self):
        """Should maintain consistency with config.json changes"""
        cache = ConfigurationCache()

        # Load initial config
        config1 = cache.get_config(self.config_file)
        self.assertEqual(config1["test"], "original")

        # Modify config.json
        time.sleep(0.1)  # Ensure different mtime
        modified_data = {"test": "modified"}
        with open(self.config_file, "w") as f:
            json.dump(modified_data, f)

        # Should reflect changes after file modification
        config2 = cache.get_config(self.config_file)
        self.assertEqual(config2["test"], "modified")

    def test_cache_refresh_on_external_change(self):
        """Should refresh cache when files are modified externally"""
        cache = ConfigurationCache()

        # Load and cache initial data
        cache.get_config(self.config_file)

        # Simulate external modification
        time.sleep(0.1)
        modified_data = {"test": "external_change"}
        with open(self.config_file, "w") as f:
            json.dump(modified_data, f)

        # Cache should detect change and reload
        refreshed_config = cache.get_config(self.config_file)
        self.assertEqual(refreshed_config["test"], "external_change")


if __name__ == "__main__":
    unittest.main()
