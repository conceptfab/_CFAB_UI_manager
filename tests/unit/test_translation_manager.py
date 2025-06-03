"""
Test dla TranslationManager z modułu utils.translation_manager.

Testy pokrywają:
1. Inicjalizację TranslationManager
2. Ładowanie tłumaczeń
3. Przełączanie między językami
4. Walidację tłumaczeń
5. Generowanie raportów
"""

import json
import logging
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from utils.translation_manager import TranslationManager

# Konfiguracja loggera testowego
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_translation_manager")


class TestTranslationManager(unittest.TestCase):
    """Testy dla klasy TranslationManager."""

    def setUp(self):
        """Inicjalizacja przed każdym testem."""
        # Resetuj singleton
        TranslationManager._instance = None
        TranslationManager._translatable_widgets = []
        TranslationManager._translations = {}
        TranslationManager._current_language = "pl"
        TranslationManager._translation_cache = {}
        TranslationManager._available_languages_cache = None
        TranslationManager._missing_keys_cache = {}
        TranslationManager._validation_errors = {}

        # Stwórz tymczasowy katalog dla testów
        self.temp_dir = tempfile.mkdtemp()
        self.translations_dir = os.path.join(self.temp_dir, "translations")
        os.makedirs(self.translations_dir, exist_ok=True)

        # Stwórz testowe pliki tłumaczeń
        self.pl_translations = {
            "common": {"ok": "OK", "cancel": "Anuluj", "save": "Zapisz"},
            "errors": {
                "not_found": "Nie znaleziono: {0}",
                "invalid_input": "Nieprawidłowe dane wejściowe",
            },
            "ui": {"title": "Tytuł aplikacji", "welcome": "Witaj {0}!"},
        }

        self.en_translations = {
            "common": {"ok": "OK", "cancel": "Cancel", "save": "Save"},
            "errors": {"not_found": "Not found: {0}", "invalid_input": "Invalid input"},
            "ui": {"title": "Application title", "welcome": "Welcome {0}!"},
        }

        # Niekompletne tłumaczenie niemieckie (dla testów walidacji)
        self.de_translations = {
            "common": {
                "ok": "OK",
                "cancel": "Abbrechen",
                # brak klucza "save"
            },
            "errors": {
                "not_found": "Nicht gefunden: {0}"
                # brak klucza "invalid_input"
            },
            "ui": {"title": "Anwendungstitel", "welcome": "Willkommen {0}!"},
        }

        # Utwórz pliki tłumaczeń
        with open(
            os.path.join(self.translations_dir, "pl.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(self.pl_translations, f, ensure_ascii=False, indent=2)

        with open(
            os.path.join(self.translations_dir, "en.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(self.en_translations, f, ensure_ascii=False, indent=2)

        with open(
            os.path.join(self.translations_dir, "de.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(self.de_translations, f, ensure_ascii=False, indent=2)

        # Stwórz plik konfiguracyjny
        self.config_path = os.path.join(self.temp_dir, "config.json")
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"language": "pl"}, f)

        # Patch dla ścieżek
        self.patcher = patch("os.path.dirname")
        self.mock_dirname = self.patcher.start()
        self.mock_dirname.return_value = self.temp_dir

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        # Zakończ patchowanie
        self.patcher.stop()

        # Usuń tymczasowy katalog
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test inicjalizacji TranslationManager."""
        # Inicjalizuj TranslationManager z testową konfiguracją
        TranslationManager.initialize(
            config_path=self.config_path, default_language="en"
        )

        # Sprawdź, czy instancja została utworzona
        inst = TranslationManager.get_instance()
        self.assertIsNotNone(inst)

        # Sprawdź, czy język został ustawiony na podstawie konfiguracji
        self.assertEqual(inst._current_language, "pl")

        # Sprawdź, czy tłumaczenia zostały załadowane
        self.assertIn("pl", inst._translations)
        self.assertEqual(inst._translations["pl"]["common"]["ok"], "OK")

    def test_load_translations(self):
        """Test ładowania tłumaczeń."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Załaduj tłumaczenia
        translations = TranslationManager.load_translations(self.translations_dir, "en")

        # Sprawdź, czy tłumaczenia zostały załadowane
        self.assertEqual(translations["common"]["ok"], "OK")
        self.assertEqual(translations["common"]["cancel"], "Cancel")
        self.assertEqual(translations["ui"]["welcome"], "Welcome {0}!")

    def test_translate(self):
        """Test tłumaczenia kluczy."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Przetłumacz klucze
        self.assertEqual(TranslationManager.translate("common.ok"), "OK")
        self.assertEqual(TranslationManager.translate("common.cancel"), "Anuluj")
        self.assertEqual(
            TranslationManager.translate("ui.welcome", "Jan"), "Witaj Jan!"
        )

        # Przetłumacz nieistniejący klucz (powinien zwrócić klucz jako default)
        self.assertEqual(
            TranslationManager.translate("common.not_existing"), "common.not_existing"
        )

    def test_set_language(self):
        """Test zmiany języka."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Zmień język na angielski
        result = TranslationManager.set_language("en")
        self.assertTrue(result)

        # Sprawdź, czy język został zmieniony
        self.assertEqual(TranslationManager.get_current_language(), "en")

        # Przetłumacz klucze w nowym języku
        self.assertEqual(TranslationManager.translate("common.cancel"), "Cancel")
        self.assertEqual(
            TranslationManager.translate("ui.welcome", "John"), "Welcome John!"
        )

        # Próba zmiany języka na nieistniejący
        with patch("os.path.exists", return_value=False):
            result = TranslationManager.set_language("fr")
            self.assertFalse(result)
            # Język nie powinien się zmienić
            self.assertEqual(TranslationManager.get_current_language(), "en")

    def test_get_available_languages(self):
        """Test pobierania dostępnych języków."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Pobierz dostępne języki
        languages = TranslationManager.get_available_languages()

        # Sprawdź, czy wszystkie języki zostały znalezione
        self.assertSetEqual(set(languages), {"pl", "en", "de"})

    def test_validate_translations(self):
        """Test walidacji tłumaczeń."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Waliduj tłumaczenia
        errors = TranslationManager.get_instance().validate_all_translations()

        # Sprawdź, czy błędy zostały znalezione dla niemieckiego
        self.assertIn("de", errors)

        # Sprawdź statystyki kompletności
        stats = TranslationManager.get_completion_stats()

        # Polski i angielski powinny mieć 100% kompletności
        self.assertEqual(stats["pl"]["completion_percent"], 100.0)
        self.assertEqual(stats["en"]["completion_percent"], 100.0)

        # Niemiecki powinien mieć niższą kompletność
        self.assertLess(stats["de"]["completion_percent"], 100.0)

        # Test funkcji is_complete
        self.assertFalse(TranslationManager.is_complete())
        self.assertTrue(
            TranslationManager.is_complete(80.0)
        )  # Zakładając, że niemieckie ma >80%

    def test_missing_keys(self):
        """Test wykrywania brakujących kluczy."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Waliduj tłumaczenia
        TranslationManager.get_instance().validate_all_translations()

        # Pobierz brakujące klucze dla niemieckiego
        missing_keys = TranslationManager.get_missing_keys("de")

        # Powinny być 2 brakujące klucze
        self.assertEqual(len(missing_keys["de"]), 2)
        self.assertIn("common.save", missing_keys["de"])
        self.assertIn("errors.invalid_input", missing_keys["de"])

        # Test z nieistniejącym tłumaczeniem
        self.assertEqual(
            TranslationManager.translate("errors.invalid_input"),
            "Nieprawidłowe dane wejściowe",
        )

        # Zmień język na niemiecki
        TranslationManager.set_language("de")

        # Tłumaczenie powinno zwrócić klucz jako default
        self.assertEqual(
            TranslationManager.translate("errors.invalid_input"), "errors.invalid_input"
        )

    def test_export_report(self):
        """Test eksportu raportu brakujących kluczy."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Waliduj tłumaczenia
        TranslationManager.get_instance().validate_all_translations()

        # Eksportuj raport
        report_path = os.path.join(self.temp_dir, "report.md")
        result = TranslationManager.export_missing_keys_report(report_path)

        # Sprawdź, czy raport został utworzony
        self.assertTrue(result)
        self.assertTrue(os.path.exists(report_path))

        # Sprawdź zawartość raportu
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Raport powinien zawierać informacje o brakujących kluczach
        self.assertIn("brakujących kluczy", content)
        self.assertIn("de", content)
        self.assertIn("common.save", content)
        self.assertIn("errors.invalid_input", content)

    def test_register_widgets(self):
        """Test rejestracji widgetów do aktualizacji."""
        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Stwórz mock widgetu
        widget = MagicMock()
        widget.update_translations = MagicMock()

        # Zarejestruj widget
        TranslationManager.register_widget(widget)

        # Zmień język
        TranslationManager.set_language("en")

        # Sprawdź, czy metoda update_translations została wywołana
        widget.update_translations.assert_called_once()

        # Wyrejestruj widget
        TranslationManager.unregister_widget(widget)

        # Zresetuj mock
        widget.update_translations.reset_mock()

        # Zmień język ponownie
        TranslationManager.set_language("pl")

        # Metoda update_translations nie powinna być wywołana
        widget.update_translations.assert_not_called()

    def test_broken_json(self):
        """Test obsługi uszkodzonego pliku JSON."""
        # Stwórz uszkodzony plik JSON
        with open(
            os.path.join(self.translations_dir, "broken.json"), "w", encoding="utf-8"
        ) as f:
            f.write("{Invalid JSON")

        # Inicjalizuj TranslationManager
        TranslationManager.initialize(config_path=self.config_path)

        # Próba załadowania uszkodzonego pliku powinna zwrócić pusty słownik
        translations = TranslationManager.load_translations(
            self.translations_dir, "broken"
        )
        self.assertEqual(translations, {})

        # Powinien być błąd walidacji
        errors = TranslationManager.get_validation_errors()
        self.assertIn("broken", errors)
        self.assertTrue(any("dekodowania" in error for error in errors["broken"]))


if __name__ == "__main__":
    unittest.main()
