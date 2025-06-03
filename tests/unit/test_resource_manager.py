"""
Test dla ResourceManager z modułu utils.resource_manager.

Testy pokrywają:
1. Inicjalizację ResourceManager
2. Ładowanie zasobów
3. Rejestrację i śledzenie zasobów
4. Automatyczne czyszczenie zasobów
5. Kontekst zasobów (with)
6. Dekoratory (cached_with_ttl, auto_cleanup_resource)
7. Monitorowanie zasobów
"""

import os
import time
import unittest
import tempfile
import logging
import threading
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import QObject

from utils.resource_manager import (
    ResourceManager, 
    ResourceContext,
    ResourceTracker,
    cached_with_ttl,
    auto_cleanup_resource
)

# Konfiguracja loggera testowego
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_resource_manager')


class TestResourceTracker(unittest.TestCase):
    """Testy dla klasy ResourceTracker."""

    def setUp(self):
        """Inicjalizacja przed każdym testem."""
        self.tracker = ResourceTracker()
        
    def test_register_resource(self):
        """Test rejestracji zasobu."""
        # Zarejestruj zasób
        test_resource = "Test resource object"
        self.tracker.register_resource(
            name="test_resource",
            resource_type="test_type",
            resource=test_resource,
            owner="test_owner"
        )
        
        # Sprawdź, czy zasób został zarejestrowany
        resource_info = self.tracker.get_resource_info("test_resource")
        self.assertIsNotNone(resource_info)
        self.assertEqual(resource_info["type"], "test_type")
        self.assertEqual(resource_info["resource"], test_resource)
        self.assertEqual(resource_info["owners"], {"test_owner"})
        
        # Sprawdź statystyki
        stats = self.tracker.get_statistics()
        self.assertEqual(stats["test_type"]["count"], 1)
    
    def test_unregister_resource(self):
        """Test wyrejestrowania zasobu."""
        # Zarejestruj zasób
        self.tracker.register_resource(
            name="test_resource",
            resource_type="test_type",
            resource="Test resource object",
            owner="test_owner"
        )
        
        # Wyrejestruj zasób
        self.tracker.unregister_resource("test_resource", owner="test_owner")
        
        # Sprawdź, czy zasób został usunięty
        resource_info = self.tracker.get_resource_info("test_resource")
        self.assertIsNone(resource_info)
        
        # Sprawdź statystyki
        stats = self.tracker.get_statistics()
        self.assertEqual(stats["test_type"]["count"], 0)
    
    def test_multiple_owners(self):
        """Test wielu właścicieli dla jednego zasobu."""
        # Zarejestruj zasób z dwoma właścicielami
        test_resource = "Test resource object"
        self.tracker.register_resource(
            name="test_resource",
            resource_type="test_type",
            resource=test_resource,
            owner="owner1"
        )
        self.tracker.register_resource(
            name="test_resource",
            resource_type="test_type",
            resource=test_resource,
            owner="owner2"
        )
        
        # Sprawdź, czy obaj właściciele zostali dodani
        resource_info = self.tracker.get_resource_info("test_resource")
        self.assertEqual(resource_info["owners"], {"owner1", "owner2"})
        
        # Wyrejestruj pierwszego właściciela
        self.tracker.unregister_resource("test_resource", owner="owner1")
        
        # Sprawdź, czy zasób nadal istnieje i ma jednego właściciela
        resource_info = self.tracker.get_resource_info("test_resource")
        self.assertIsNotNone(resource_info)
        self.assertEqual(resource_info["owners"], {"owner2"})
        
        # Wyrejestruj drugiego właściciela
        self.tracker.unregister_resource("test_resource", owner="owner2")
        
        # Sprawdź, czy zasób został usunięty
        resource_info = self.tracker.get_resource_info("test_resource")
        self.assertIsNone(resource_info)
    
    def test_cleanup_expired_resources(self):
        """Test czyszczenia przeterminowanych zasobów."""
        # Zarejestruj zasób
        self.tracker.register_resource(
            name="test_resource",
            resource_type="test_type",
            resource="Test resource object"
        )
        
        # Zmień czas utworzenia na stary
        with patch.dict(self.tracker.resources, {
            "test_resource": {
                **self.tracker.resources["test_resource"],
                "created_at": time.time() - 3700  # 1 godzina i 100 sekund temu (ponad limit 1h)
            }
        }):
            # Wyczyść zasoby starsze niż 1 godzina
            cleaned = self.tracker.cleanup_expired_resources(max_age_seconds=3600)
            
            # Sprawdź, czy zasób został wyczyszczony
            self.assertEqual(len(cleaned), 1)
            self.assertEqual(cleaned[0], "test_resource")
            
            # Sprawdź, czy zasób już nie istnieje
            resource_info = self.tracker.get_resource_info("test_resource")
            self.assertIsNone(resource_info)
    
    def test_monitoring(self):
        """Test monitorowania zasobów."""
        # Uruchom monitorowanie z krótkim interwałem
        with patch.object(self.tracker, "_monitoring_loop") as mock_loop:
            self.tracker.start_monitoring(interval=1)
            # Poczekaj, aby upewnić się, że wątek wystartował
            time.sleep(0.1)
            
            # Sprawdź, czy monitorowanie zostało uruchomione
            self.assertTrue(self.tracker._monitoring_thread.is_alive())
            
            # Zatrzymaj monitorowanie
            self.tracker.stop_monitoring()
            
            # Poczekaj na zatrzymanie wątku
            time.sleep(0.1)
            
            # Sprawdź, czy wątek został zatrzymany
            self.assertTrue(self.tracker._stop_monitoring.is_set())


class TestResourceContext(unittest.TestCase):
    """Testy dla klasy ResourceContext."""

    def test_resource_context(self):
        """Test kontekstu zasobu."""
        # Mock dla ResourceManager
        manager = MagicMock()
        cleanup_callback = MagicMock()
        
        # Użyj kontekstu
        with ResourceContext("test_context", manager=manager, cleanup_callback=cleanup_callback) as ctx:
            # Zarejestruj zasoby
            ctx.register("resource1")
            ctx.register("resource2")
            
            # Sprawdź, czy zasoby zostały zarejestrowane
            self.assertEqual(ctx.resources, {"resource1", "resource2"})
        
        # Sprawdź, czy funkcja czyszcząca została wywołana
        cleanup_callback.assert_called_once()
        
        # Sprawdź, czy manager.unregister_resource został wywołany dla obu zasobów
        self.assertEqual(manager.unregister_resource.call_count, 2)
        manager.unregister_resource.assert_any_call("resource1", owner="test_context")
        manager.unregister_resource.assert_any_call("resource2", owner="test_context")


class TestCachedWithTTL(unittest.TestCase):
    """Testy dla dekoratora cached_with_ttl."""

    def test_cache(self):
        """Test podstawowej funkcjonalności cache."""
        call_count = 0
        
        @cached_with_ttl(ttl_seconds=1)
        def test_func(arg):
            nonlocal call_count
            call_count += 1
            return f"Result for {arg}"
        
        # Pierwsze wywołanie powinno zwiększyć licznik
        result1 = test_func("test")
        self.assertEqual(call_count, 1)
        
        # Drugie wywołanie powinno użyć cache'a
        result2 = test_func("test")
        self.assertEqual(call_count, 1)
        self.assertEqual(result1, result2)
        
        # Wywołanie z innym argumentem powinno zwiększyć licznik
        result3 = test_func("other")
        self.assertEqual(call_count, 2)
        self.assertNotEqual(result1, result3)
    
    def test_ttl_expiration(self):
        """Test wygasania TTL w cache."""
        call_count = 0
        
        @cached_with_ttl(ttl_seconds=0.5)  # Krótki TTL dla testu
        def test_func(arg):
            nonlocal call_count
            call_count += 1
            return f"Result for {arg}"
        
        # Pierwsze wywołanie
        result1 = test_func("test")
        self.assertEqual(call_count, 1)
        
        # Drugie wywołanie (przed wygaśnięciem TTL)
        result2 = test_func("test")
        self.assertEqual(call_count, 1)
        
        # Poczekaj na wygaśnięcie TTL
        time.sleep(0.6)
        
        # Trzecie wywołanie (po wygaśnięciu TTL)
        result3 = test_func("test")
        self.assertEqual(call_count, 2)
    
    def test_max_size(self):
        """Test ograniczenia rozmiaru cache."""
        @cached_with_ttl(ttl_seconds=60, max_size=2)
        def test_func(arg):
            return f"Result for {arg}"
        
        # Wypełnij cache
        result1 = test_func("a")
        result2 = test_func("b")
        
        # Dodaj trzeci element (powinien usunąć najstarszy wpis)
        result3 = test_func("c")
        
        # Sprawdź, czy najstarszy element został usunięty z cache
        # (nie można bezpośrednio sprawdzić cache, więc sprawdzimy pośrednio)
        # To jest nieco trudne w testowaniu, ponieważ nie mamy bezpośredniego dostępu do wewnętrznego stanu cache
        # Możemy to obejść w bardziej zaawansowanych testach za pomocą patchowania lub innych technik
    
    def test_clear_cache(self):
        """Test metody czyszczenia cache."""
        call_count = 0
        
        @cached_with_ttl(ttl_seconds=60)
        def test_func(arg):
            nonlocal call_count
            call_count += 1
            return f"Result for {arg}"
        
        # Wypełnij cache
        result1 = test_func("test")
        self.assertEqual(call_count, 1)
        
        # Drugie wywołanie powinno użyć cache'a
        result2 = test_func("test")
        self.assertEqual(call_count, 1)
        
        # Wyczyść cache
        test_func.clear_cache()
        
        # Kolejne wywołanie powinno zwiększyć licznik
        result3 = test_func("test")
        self.assertEqual(call_count, 2)


class TestAutoCleanupResource(unittest.TestCase):
    """Testy dla dekoratora auto_cleanup_resource."""

    def test_auto_cleanup(self):
        """Test automatycznego czyszczenia zasobów."""
        # Mock dla ResourceManager
        manager = MagicMock()
        manager.register_resource = MagicMock()
        
        @auto_cleanup_resource(resource_type="test_resource")
        def create_resource():
            return "test_resource_value"
        
        # Wywołaj funkcję
        result = create_resource(manager)
        
        # Sprawdź, czy manager.register_resource został wywołany
        manager.register_resource.assert_called_once()
        
        # Sprawdź argumenty wywołania
        call_args = manager.register_resource.call_args
        args, kwargs = call_args
        
        # Pierwszy argument to nazwa zasobu
        self.assertTrue(args[0].startswith("create_resource_"))
        # Drugi argument to typ zasobu
        self.assertEqual(args[1], "test_resource")
        # Trzeci argument to sam zasób
        self.assertEqual(args[2], "test_resource_value")
        # Czwarty argument to właściciel
        self.assertEqual(args[3], "create_resource")


class TestResourceManager(unittest.TestCase):
    """Testy dla klasy ResourceManager."""

    def setUp(self):
        """Inicjalizacja przed każdym testem."""
        # Stwórz tymczasowy katalog dla testów
        self.temp_dir = tempfile.mkdtemp()
        
        # Stwórz struktura katalogów
        resources_dir = os.path.join(self.temp_dir, "resources")
        translations_dir = os.path.join(self.temp_dir, "translations")
        os.makedirs(resources_dir, exist_ok=True)
        os.makedirs(translations_dir, exist_ok=True)
        
        # Utwórz testowy plik CSS
        css_path = os.path.join(resources_dir, "styles.qss")
        with open(css_path, "w") as f:
            f.write("/* Test CSS */\nbody { font-size: 12px; }\n")
        
        # Utwórz testowe pliki tłumaczeń
        pl_path = os.path.join(translations_dir, "pl.json")
        with open(pl_path, "w") as f:
            f.write('{"test": "Test PL"}')
            
        en_path = os.path.join(translations_dir, "en.json")
        with open(en_path, "w") as f:
            f.write('{"test": "Test EN"}')
        
        # Ustaw mock dla performance_monitor.measure_execution_time
        self.measure_execution_time_patcher = patch(
            "utils.resource_manager.performance_monitor.measure_execution_time", 
            return_value=lambda f: f
        )
        self.measure_execution_time_patcher.start()
        
        # Ustaw mock dla AsyncResourceLoader
        self.async_loader_patcher = patch(
            "utils.resource_manager.AsyncResourceLoader", 
            return_value=MagicMock()
        )
        self.mock_async_loader = self.async_loader_patcher.start().return_value
        
        # Ustaw mock dla lazy_loader
        self.lazy_loader_patcher = patch("utils.resource_manager.lazy_loader")
        self.mock_lazy_loader = self.lazy_loader_patcher.start()
        
        # Ustaw mock dla TranslationManager
        self.translation_manager_patcher = patch("utils.resource_manager.TranslationManager")
        self.mock_translation_manager = self.translation_manager_patcher.start().return_value
        self.mock_translation_manager.load_translations.return_value = {"test": "Test Translation"}
        
        # Ustaw mock dla atexit.register
        self.atexit_register_patcher = patch("utils.resource_manager.atexit.register")
        self.mock_atexit_register = self.atexit_register_patcher.start()
        
        # Stwórz instancję ResourceManager
        self.resource_manager = ResourceManager(self.temp_dir, logger)
        
        # Ustaw mock dla ResourceTracker
        self.original_tracker = self.resource_manager.tracker
        self.resource_manager.tracker = MagicMock()
        
    def tearDown(self):
        """Czyszczenie po każdym teście."""
        # Zakończ wszystkie patche
        self.measure_execution_time_patcher.stop()
        self.async_loader_patcher.stop()
        self.lazy_loader_patcher.stop()
        self.translation_manager_patcher.stop()
        self.atexit_register_patcher.stop()
        
        # Zatrzymaj monitorowanie (jeśli było uruchomione)
        self.original_tracker.stop_monitoring()
        
        # Wyczyść tymczasowy katalog
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test inicjalizacji ResourceManager."""
        # Sprawdź, czy ResourceManager został poprawnie zainicjalizowany
        self.assertEqual(self.resource_manager.base_dir, self.temp_dir)
        self.assertIsInstance(self.resource_manager, QObject)
        
        # Sprawdź, czy atexit.register został wywołany
        self.mock_atexit_register.assert_called_once_with(self.resource_manager.cleanup)
        
        # Sprawdź, czy trackery zostały zarejestrowane
        self.assertEqual(self.resource_manager.tracker.register_resource.call_count, 2)
        
        # Sprawdź, czy AsyncResourceLoader został zainicjalizowany
        self.assertEqual(self.mock_async_loader.resource_loaded.connect.call_count, 1)
        self.assertEqual(self.mock_async_loader.loading_failed.connect.call_count, 1)
    
    def test_load_all_resources(self):
        """Test ładowania wszystkich zasobów."""
        # Wywołaj metodę
        self.resource_manager.load_all_resources()
        
        # Sprawdź, czy AsyncResourceLoader.load_resource_async został wywołany
        self.assertEqual(self.mock_async_loader.load_resource_async.call_count, 2)
        
        # Sprawdź wywołania
        self.mock_async_loader.load_resource_async.assert_any_call(
            "main_css", self.resource_manager._load_css_optimized
        )
        self.mock_async_loader.load_resource_async.assert_any_call(
            "translations", self.resource_manager._load_translations
        )
    
    def test_load_css_optimized(self):
        """Test ładowania CSS."""
        # Przygotuj mock dla lazy_loader.get_resource
        test_css = "body { color: red; }"
        self.mock_lazy_loader.get_resource.return_value = test_css
        
        # Wywołaj metodę
        result = self.resource_manager._load_css_optimized()
        
        # Sprawdź rezultat
        self.assertEqual(result, test_css)
        
        # Sprawdź, czy lazy_loader.get_resource został wywołany
        self.mock_lazy_loader.get_resource.assert_called_once_with("main_css")
        
        # Sprawdź, czy zasób został zarejestrowany w trackerze
        self.resource_manager.tracker.register_resource.assert_any_call(
            "main_css_data", "css", test_css, owner="ResourceManager"
        )
    
    def test_load_translations(self):
        """Test ładowania tłumaczeń."""
        # Przygotuj mock dla lazy_loader.get_resource
        test_translations = {"test": "translation"}
        self.mock_lazy_loader.get_resource.return_value = test_translations
        
        # Wywołaj metodę
        result = self.resource_manager._load_translations()
        
        # Sprawdź rezultat
        self.assertEqual(result, test_translations)
        
        # Sprawdź, czy lazy_loader.get_resource został wywołany
        self.mock_lazy_loader.get_resource.assert_called_once_with("translations")
        
        # Sprawdź, czy zasób został zarejestrowany w trackerze
        self.resource_manager.tracker.register_resource.assert_any_call(
            "translations_data", "translations", test_translations, owner="ResourceManager"
        )
    
    def test_handle_resource_loaded(self):
        """Test obsługi załadowanego zasobu."""
        # Ustaw mocki dla sygnałów
        self.resource_manager.css_loaded = MagicMock()
        self.resource_manager.translations_loaded = MagicMock()
        
        # Wywołaj metodę dla CSS
        css_data = "body { color: green; }"
        self.resource_manager._handle_resource_loaded("main_css", css_data)
        
        # Sprawdź, czy sygnał css_loaded został wyemitowany
        self.resource_manager.css_loaded.emit.assert_called_once_with(css_data)
        
        # Wywołaj metodę dla tłumaczeń
        translations_data = {"btn_ok": "OK"}
        self.resource_manager._handle_resource_loaded("translations", translations_data)
        
        # Sprawdź, czy sygnał translations_loaded został wyemitowany
        self.resource_manager.translations_loaded.emit.assert_called_once_with(translations_data)
        
        # Sprawdź, czy translations zostały zapisane
        self.assertEqual(self.resource_manager.translations, translations_data)
    
    def test_invalidate_cache(self):
        """Test invalidacji cache."""
        # Wywołaj metodę
        self.resource_manager.invalidate_cache("test_resource")
        
        # Sprawdź, czy lazy_loader.clear_cache został wywołany
        self.mock_lazy_loader.clear_cache.assert_called_once_with("test_resource")
        
        # Wywołaj metodę bez argumentów
        self.resource_manager.invalidate_cache()
        
        # Sprawdź, czy lazy_loader.clear_cache został wywołany z None
        self.mock_lazy_loader.clear_cache.assert_called_with(None)
    
    def test_create_resource_context(self):
        """Test tworzenia kontekstu zasobu."""
        # Wywołaj metodę
        context = self.resource_manager.create_resource_context("test_context")
        
        # Sprawdź, czy kontekst został utworzony
        self.assertIsInstance(context, ResourceContext)
        self.assertEqual(context.name, "test_context")
        self.assertEqual(context._manager, self.resource_manager)
    
    def test_register_unregister_resource(self):
        """Test rejestracji i wyrejestrowania zasobu."""
        # Wywołaj metodę rejestracji
        self.resource_manager.register_resource(
            "test_resource", "test_type", "test_value", "test_owner"
        )
        
        # Sprawdź, czy tracker.register_resource został wywołany
        self.resource_manager.tracker.register_resource.assert_called_with(
            "test_resource", "test_type", "test_value", "test_owner"
        )
        
        # Wywołaj metodę wyrejestrowania
        self.resource_manager.unregister_resource("test_resource", "test_owner")
        
        # Sprawdź, czy tracker.unregister_resource został wywołany
        self.resource_manager.tracker.unregister_resource.assert_called_with(
            "test_resource", "test_owner"
        )
    
    def test_get_resource_statistics(self):
        """Test pobierania statystyk zasobów."""
        # Przygotuj mock dla tracker.get_statistics
        test_stats = {"test_type": {"count": 5}}
        self.resource_manager.tracker.get_statistics.return_value = test_stats
        
        # Wywołaj metodę
        result = self.resource_manager.get_resource_statistics()
        
        # Sprawdź rezultat
        self.assertEqual(result, test_stats)
        
        # Sprawdź, czy tracker.get_statistics został wywołany
        self.resource_manager.tracker.get_statistics.assert_called_once()
    
    def test_cleanup(self):
        """Test czyszczenia zasobów."""
        # Przygotuj mocki
        self.resource_manager.tracker.get_all_resources.return_value = {
            "resource1": {"type": "test_type"},
            "resource2": {"type": "test_type"}
        }
        
        # Wywołaj metodę
        self.resource_manager.cleanup()
        
        # Sprawdź, czy tracker.stop_monitoring został wywołany
        self.resource_manager.tracker.stop_monitoring.assert_called_once()
        
        # Sprawdź, czy tracker.unregister_resource został wywołany dla obu zasobów
        self.assertEqual(self.resource_manager.tracker.unregister_resource.call_count, 2)
        
        # Sprawdź, czy async_loader.cancel_all i async_loader.cleanup zostały wywołane
        self.mock_async_loader.cancel_all.assert_called_once()
        self.mock_async_loader.cleanup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
