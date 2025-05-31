"""
Scentralizowany manager zasobów dla aplikacji.
Zarządza ładowaniem CSS, tłumaczeń i innych zasobów.
"""

import logging
import os
import time
from functools import lru_cache
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from utils.performance_optimizer import (
    AsyncResourceLoader,
    create_css_loader,
    lazy_loader,
    performance_monitor,
)
from utils.translation_manager import TranslationManager

logger = logging.getLogger(__name__)


class ResourceManager(QObject):
    """
    Scentralizowany manager zasobów aplikacji.
    """

    resources_loaded = pyqtSignal()
    css_loaded = pyqtSignal(str)
    translations_loaded = pyqtSignal(dict)
    loading_failed = pyqtSignal(str, str)  # resource_name, error_message

    def __init__(self, base_dir, app_logger: Optional[logging.Logger] = None):
        """
        Inicjalizacja ResourceManager.

        Args:
            base_dir: Ścieżka bazowa do głównego katalogu aplikacji
            app_logger: Opcjonalna instancja loggera aplikacji
        """
        super().__init__()
        self.base_dir = base_dir
        self.logger = app_logger if app_logger else logger
        self.css_loader = None
        self.translation_loader = None
        self.async_loader = AsyncResourceLoader(max_workers=2)
        self.translations = {}
        self._setup_loaders()

        # Podłącz sygnały
        self.async_loader.resource_loaded.connect(self._handle_resource_loaded)
        self.async_loader.loading_failed.connect(self.loading_failed)

    def _setup_loaders(self):
        """Konfiguracja loaderów dla różnych typów zasobów."""
        # CSS
        css_path = os.path.join(self.base_dir, "resources", "styles.qss")
        self.css_loader = create_css_loader(css_path)
        lazy_loader.register_loader("main_css", self.css_loader)

        # Translations
        self.translation_loader = self._create_translation_loader()
        lazy_loader.register_loader("translations", self.translation_loader)

    def load_all_resources(self):
        """Jednokrotne załadowanie wszystkich zasobów."""
        self.logger.info("Rozpoczynam ładowanie wszystkich zasobów...")

        # Załaduj CSS asynchronicznie
        self.async_loader.load_resource_async("main_css", self._load_css_optimized)

        # Załaduj tłumaczenia asynchronicznie
        self.async_loader.load_resource_async("translations", self._load_translations)

    @performance_monitor.measure_execution_time("css_loading")
    def _load_css_optimized(self):
        """Zoptymalizowane ładowanie CSS z wykorzystaniem lazy loading i cache."""
        try:
            # Najpierw próbuj pobrać z cache
            styles = lazy_loader.get_resource("main_css")
            self.logger.info("CSS styles loaded from cache")
            return styles
        except Exception as e:
            self.logger.warning(f"Could not load CSS from cache: {e}")
            # Załaduj bezpośrednio
            if self.css_loader:
                return self.css_loader()
            return ""

    def _create_translation_loader(self):
        """Tworzy loader dla tłumaczeń."""

        def load_translations():
            translation_manager = TranslationManager()
            trans_dir = os.path.join(self.base_dir, "translations")
            translations = translation_manager.load_translations(trans_dir)
            return translations

        return load_translations

    def _load_translations(self):
        """Ładuje tłumaczenia."""
        try:
            # Próbuj pobrać z cache
            translations = lazy_loader.get_resource("translations")
            self.logger.info("Translations loaded from cache")
            return translations
        except Exception as e:
            self.logger.warning(f"Could not load translations from cache: {e}")
            # Załaduj bezpośrednio
            if self.translation_loader:
                return self.translation_loader()
            return {}

    def _handle_resource_loaded(self, name, data):
        """Obsługuje załadowany zasób."""
        if name == "main_css":
            self.css_loaded.emit(data)
        elif name == "translations":
            self.translations = data
            self.translations_loaded.emit(data)

    def invalidate_cache(self, resource_name=None):
        """
        Invaliduje cache dla określonego zasobu lub wszystkich zasobów.

        Args:
            resource_name: Nazwa zasobu do invalidacji lub None dla wszystkich
        """
        lazy_loader.clear_cache(resource_name)
        self.logger.info(f"Cache invalidated for {resource_name or 'all resources'}")

    def cleanup(self):
        """Czyszczenie zasobów przed zamknięciem aplikacji."""
        self.async_loader.cancel_all()
        self.async_loader.cleanup()
        self.logger.debug("ResourceManager cleaned up")


# Funkcja pomocnicza do dekorowania funkcji z TTL cache
def cached_with_ttl(ttl_seconds=300):
    """
    Dekorator dodający TTL do cache'a funkcji.

    Args:
        ttl_seconds: Czas życia w sekundach dla elementów w cache

    Returns:
        Dekorator funkcji
    """

    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        return wrapper

    return decorator
