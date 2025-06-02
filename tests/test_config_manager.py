#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testy jednostkowe dla ConfigManager.

Ten moduł zawiera testy sprawdzające funkcjonalność klasy ConfigManager
z modułu architecture.config_management.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from architecture.config_management import ConfigManager
from utils.exceptions import ConfigurationError, ValidationError


class TestConfigManager(unittest.TestCase):
    """Testy jednostkowe dla klasy ConfigManager."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        # Utwórz tymczasowy katalog do testów
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "config.json")
        self.invalid_config_path = os.path.join(self.test_dir, "invalid_config.json")

        # Przygotuj przykładową konfigurację
        self.test_config = {
            "language": "pl",
            "show_splash": True,
            "log_to_file": False,
            "log_to_system_console": False,
            "window_size": {"width": 1024, "height": 768},
            "window_position": {"x": 100, "y": 100},
            "remember_window_size": True,
            "log_level": "INFO",
        }

        # Zapisz przykładową konfigurację
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.test_config, f)

        # Zapisz nieprawidłową konfigurację
        with open(self.invalid_config_path, "w", encoding="utf-8") as f:
            f.write("{ This is not valid JSON }")

        # Zresetuj singleton przed każdym testem
        ConfigManager._instance = None

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        # Usuń tymczasowy katalog
        shutil.rmtree(self.test_dir)

        # Zresetuj singleton po każdym teście
        ConfigManager._instance = None

    def test_singleton_pattern(self):
        """Test wzorca Singleton."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        self.assertIs(manager1, manager2)

    def test_load_config(self):
        """Test ładowania konfiguracji."""
        manager = ConfigManager()
        config = manager.load_config(self.config_path)

        self.assertEqual(config["language"], "pl")
        self.assertTrue(config["show_splash"])
        self.assertEqual(config["window_size"]["width"], 1024)

    def test_load_config_use_cache(self):
        """Test używania pamięci podręcznej przy ładowaniu konfiguracji."""
        manager = ConfigManager()
        # Pierwsze ładowanie
        manager.load_config(self.config_path)

        # Zapiszmy oryginalną wartość
        original_language = manager.get_config_value("language")

        # Modyfikujemy oryginalny plik
        modified_config = self.test_config.copy()
        modified_config["language"] = "en" if original_language == "pl" else "pl"
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(modified_config, f)

        # Drugie ładowanie z cache - powinniśmy zobaczyć oryginalną wartość
        cached_config = manager.load_config(self.config_path, use_cache=True)
        self.assertEqual(cached_config["language"], original_language)

        # Trzecie ładowanie bez cache - powinniśmy zobaczyć nową wartość
        fresh_config = manager.load_config(self.config_path, use_cache=False)
        self.assertEqual(
            fresh_config["language"], "en" if original_language == "pl" else "pl"
        )

    def test_create_default_config(self):
        """Test tworzenia domyślnej konfiguracji."""
        non_existent_path = os.path.join(self.test_dir, "new_config.json")

        manager = ConfigManager()
        config = manager.load_config(non_existent_path)

        # Sprawdź, czy plik został utworzony
        self.assertTrue(os.path.exists(non_existent_path))

        # Sprawdź, czy zawiera domyślne wartości
        self.assertEqual(config["language"], "pl")
        self.assertTrue(config["show_splash"])

    def test_get_config_value(self):
        """Test pobierania wartości konfiguracji."""
        manager = ConfigManager()
        manager.load_config(self.config_path)

        # Test podstawowej wartości
        self.assertEqual(manager.get_config_value("language"), "pl")

        # Test wartości zagnieżdżonej
        self.assertEqual(manager.get_config_value("window_size.width"), 1024)

        # Test wartości domyślnej dla nieistniejącego klucza
        self.assertEqual(manager.get_config_value("non_existent", "default"), "default")

        # Test wartości domyślnej dla nieistniejącego klucza zagnieżdżonego
        self.assertEqual(manager.get_config_value("window_size.non_existent", 42), 42)

    def test_set_config_value(self):
        """Test ustawiania wartości konfiguracji."""
        manager = ConfigManager()
        manager.load_config(self.config_path)

        # Ustaw podstawową wartość
        manager.set_config_value("language", "en")
        self.assertEqual(manager.get_config_value("language"), "en")

        # Ustaw wartość zagnieżdżoną
        manager.set_config_value("window_size.width", 1280)
        self.assertEqual(manager.get_config_value("window_size.width"), 1280)

        # Ustaw nowy klucz
        manager.set_config_value("new_key", "new_value")
        self.assertEqual(manager.get_config_value("new_key"), "new_value")

        # Ustaw nowy klucz zagnieżdżony w nieistniejącej sekcji
        manager.set_config_value("new_section.key", "value")
        self.assertEqual(manager.get_config_value("new_section.key"), "value")

    def test_save_config(self):
        """Test zapisywania konfiguracji."""
        manager = ConfigManager()
        manager.load_config(self.config_path)

        # Zmień konfigurację
        manager.set_config_value("language", "en")
        manager.set_config_value("window_size.width", 1280)

        # Zapisz konfigurację
        save_path = os.path.join(self.test_dir, "saved_config.json")
        manager.save_config(save_path)

        # Załaduj zapisaną konfigurację i sprawdź, czy zmiany zostały zapisane
        with open(save_path, "r") as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config["language"], "en")
        self.assertEqual(saved_config["window_size"]["width"], 1280)

    def test_transaction(self):
        """Test mechanizmu transakcji."""
        manager = ConfigManager()
        manager.load_config(self.config_path)

        # Zmień konfigurację w transakcji
        with manager.transaction():
            manager.set_config_value("language", "en")
            manager.set_config_value("window_size.width", 1280)

        # Sprawdź, czy zmiany zostały zatwierdzone
        self.assertEqual(manager.get_config_value("language"), "en")
        self.assertEqual(manager.get_config_value("window_size.width"), 1280)

        # Spróbuj transakcję z wyjątkiem
        try:
            with manager.transaction():
                manager.set_config_value("language", "de")
                manager.set_config_value("window_size.width", 1920)
                raise Exception("Test exception")
        except Exception:
            pass

        # Sprawdź, czy zmiany zostały wycofane
        self.assertEqual(manager.get_config_value("language"), "en")
        self.assertEqual(manager.get_config_value("window_size.width"), 1280)

    def test_language_settings(self):
        """Test metod do obsługi ustawień języka."""
        manager = ConfigManager()
        manager.load_config(self.config_path)

        # Domyślny język
        self.assertEqual(manager.get_language_setting(), "pl")

        # Zmiana języka
        manager.set_language_setting("en", save=False)
        self.assertEqual(manager.get_language_setting(), "en")

        # Próba ustawienia niepoprawnego języka (powinno użyć domyślnego)
        manager.set_language_setting("invalid", save=False)
        self.assertEqual(manager.get_language_setting(), "pl")

    def test_invalid_config(self):
        """Test obsługi niepoprawnego pliku konfiguracyjnego."""
        manager = ConfigManager()

        # Próba załadowania niepoprawnego pliku JSON
        with self.assertRaises(ConfigurationError):
            manager.load_config(self.invalid_config_path)

    def test_merge_config(self):
        """Test scalania konfiguracji."""
        manager = ConfigManager()
        manager.load_config(self.config_path)

        # Przygotuj konfigurację do scalenia
        new_config = {
            "language": "en",
            "window_size": {"width": 1280},
            "new_section": {"key": "value"},
        }

        # Scal konfiguracje
        manager.merge_config(new_config, save=False)

        # Sprawdź, czy wartości zostały scalone prawidłowo
        self.assertEqual(manager.get_config_value("language"), "en")
        self.assertEqual(manager.get_config_value("window_size.width"), 1280)
        self.assertEqual(
            manager.get_config_value("window_size.height"), 768
        )  # zachowany z oryginalnej konfiguracji
        self.assertEqual(manager.get_config_value("new_section.key"), "value")

    def test_reset_to_defaults(self):
        """Test resetowania konfiguracji do wartości domyślnych."""
        manager = ConfigManager()
        manager.load_config(self.config_path)

        # Zmień konfigurację
        manager.set_config_value("language", "en")
        manager.set_config_value("custom_key", "custom_value")

        # Resetuj konfigurację
        manager.reset_to_defaults(save=False)

        # Sprawdź, czy przywrócono wartości domyślne
        self.assertEqual(manager.get_config_value("language"), "pl")
        self.assertIsNone(manager.get_config_value("custom_key"))


if __name__ == "__main__":
    unittest.main()
