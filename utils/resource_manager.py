"""
Scentralizowany manager zasobów dla aplikacji.
Zarządza ładowaniem CSS, tłumaczeń i innych zasobów.

Klasy:
    - ResourceManager: Główny manager zasobów aplikacji
    - ResourceContext: Menedżer kontekstu dla automatycznego czyszczenia zasobów
    - ResourceTracker: Klasa do śledzenia i monitorowania użycia zasobów

Funkcje:
    - cached_with_ttl: Dekorator dla cache'a z TTL
    - auto_cleanup_resource: Dekorator dla automatycznego czyszczenia zasobów
"""

import atexit
import gc
import logging
import os
import threading
import time
import weakref
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Set

from PyQt6.QtCore import QObject, pyqtSignal

from utils.performance_optimizer import (
    AsyncResourceLoader,
    create_css_loader,
    lazy_loader,
    performance_monitor,
)
from utils.translation_manager import TranslationManager

logger = logging.getLogger(__name__)


class ResourceTracker:
    """
    Klasa do śledzenia użycia zasobów i monitorowania pamięci.

    Attributes:
        resources (Dict): Słownik otwartych zasobów i ich użytkowników
        resource_stats (Dict): Statystyki użycia zasobów
    """

    def __init__(self):
        self.resources: Dict[str, Dict] = {}
        self.resource_stats: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()

    def register_resource(
        self, name: str, resource_type: str, resource: Any, owner=None
    ) -> None:
        """
        Rejestruje zasób w trackerze.

        Args:
            name: Nazwa zasobu
            resource_type: Typ zasobu (file, connection, css, translation, etc.)
            resource: Obiekt zasobu
            owner: Właściciel zasobu (domyślnie: None)
        """
        with self._lock:
            if name not in self.resources:
                self.resources[name] = {
                    "resource": resource,
                    "type": resource_type,
                    "owners": set(),
                    "created_at": time.time(),
                }

                # Inicjalizuj statystyki dla tego typu zasobu
                if resource_type not in self.resource_stats:
                    self.resource_stats[resource_type] = {
                        "count": 0,
                        "peak_memory": 0,
                        "current_memory": 0,
                    }

                self.resource_stats[resource_type]["count"] += 1

            if owner:
                self.resources[name]["owners"].add(owner)

            logger.debug(f"Resource registered: {name} ({resource_type})")

    def unregister_resource(self, name: str, owner=None) -> None:
        """
        Wyrejestrowuje zasób z trackera.

        Args:
            name: Nazwa zasobu
            owner: Właściciel zasobu (domyślnie: None)
        """
        with self._lock:
            if name in self.resources:
                if owner and "owners" in self.resources[name]:
                    self.resources[name]["owners"].discard(owner)

                    # Jeśli wciąż są inni właściciele, nie usuwaj zasobu
                    if self.resources[name]["owners"]:
                        return

                resource_type = self.resources[name]["type"]
                self.resource_stats[resource_type]["count"] -= 1

                del self.resources[name]
                logger.debug(f"Resource unregistered: {name}")

    def get_resource_info(self, name: str) -> Optional[Dict]:
        """
        Pobiera informacje o zarejestrowanym zasobie.

        Args:
            name: Nazwa zasobu

        Returns:
            Słownik z informacjami o zasobie lub None jeśli nie znaleziono
        """
        with self._lock:
            return self.resources.get(name)

    def get_all_resources(self) -> Dict[str, Dict]:
        """
        Pobiera wszystkie zarejestrowane zasoby.

        Returns:
            Kopia słownika zasobów
        """
        with self._lock:
            return self.resources.copy()

    def cleanup_expired_resources(self, max_age_seconds: int = 3600) -> List[str]:
        """
        Czyści zasoby, które przekroczyły określony wiek.

        Args:
            max_age_seconds: Maksymalny wiek zasobu w sekundach

        Returns:
            Lista nazw wyczyszczonych zasobów
        """
        current_time = time.time()
        cleaned_resources = []

        with self._lock:
            resources_to_remove = []

            for name, info in self.resources.items():
                if "created_at" in info:
                    age = current_time - info["created_at"]
                    if age > max_age_seconds and not info.get("owners", set()):
                        resources_to_remove.append(name)

            for name in resources_to_remove:
                resource_type = self.resources[name]["type"]
                self.resource_stats[resource_type]["count"] -= 1

                del self.resources[name]
                cleaned_resources.append(name)
                logger.debug(
                    f"Expired resource cleaned up: {name} (age > {max_age_seconds}s)"
                )

        return cleaned_resources

    def get_statistics(self) -> Dict[str, Dict]:
        """
        Pobiera statystyki użycia zasobów.

        Returns:
            Słownik statystyk użycia zasobów
        """
        with self._lock:
            return self.resource_stats.copy()

    def start_monitoring(self, interval: int = 60) -> None:
        """
        Uruchamia wątek monitorowania zasobów.

        Args:
            interval: Interwał monitorowania w sekundach
        """
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Resource monitoring thread is already running")
            return

        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True,
            name="ResourceMonitoringThread",
        )
        self._monitoring_thread.start()
        logger.info(f"Resource monitoring started with interval {interval}s")

    def stop_monitoring(self) -> None:
        """Zatrzymuje wątek monitorowania zasobów."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5)
            logger.info("Resource monitoring stopped")

    def _monitoring_loop(self, interval: int) -> None:
        """
        Główna pętla monitorowania.

        Args:
            interval: Interwał monitorowania w sekundach
        """
        while not self._stop_monitoring.is_set():
            # Aktualizuj statystyki pamięci
            self._update_memory_stats()

            # Wyczyść stare zasoby
            cleaned = self.cleanup_expired_resources()
            if cleaned:
                logger.info(f"Auto-cleaned {len(cleaned)} expired resources")

            # Wymuś garbage collection
            gc.collect()

            # Zapisz aktualne statystyki w logu
            self._log_statistics()

            # Czekaj na następny interwał
            self._stop_monitoring.wait(interval)

    def _update_memory_stats(self) -> None:
        """Aktualizuje statystyki pamięci dla zasobów."""
        # Tutaj można dodać dokładniejsze monitorowanie pamięci specyficzne dla typu zasobu
        # Na razie używamy prostego licznika
        with self._lock:
            total_resources = sum(
                stats["count"] for stats in self.resource_stats.values()
            )
            for resource_type, stats in self.resource_stats.items():
                # W bardziej zaawansowanej implementacji można by użyć sys.getsizeof()
                # lub dedykowanych metod dla poszczególnych typów zasobów
                count = stats["count"]
                logger.debug(f"Resource type {resource_type}: {count} instances")

    def _log_statistics(self) -> None:
        """Loguje aktualne statystyki zasobów."""
        with self._lock:
            resource_counts = {
                rtype: stats["count"] for rtype, stats in self.resource_stats.items()
            }
            total_resources = sum(resource_counts.values())
            logger.info(
                f"Resource statistics: {resource_counts} (Total: {total_resources})"
            )


class ResourceContext:
    """
    Menedżer kontekstu dla automatycznego zarządzania zasobami.
    Umożliwia używanie wyrażenia 'with' do automatycznego czyszczenia zasobów.

    Example:
        ```
        with ResourceContext("image_loader") as ctx:
            # Użyj zasobów
            image = ctx.load_image("path/to/image.jpg")
        # Po wyjściu z bloku, zasoby zostaną automatycznie wyczyszczone
        ```
    """

    def __init__(self, name: str, manager=None, cleanup_callback: Callable = None):
        """
        Inicjalizacja kontekstu zasobu.

        Args:
            name: Nazwa kontekstu zasobu
            manager: Opcjonalny manager zasobów
            cleanup_callback: Opcjonalna funkcja czyszcząca
        """
        self.name = name
        self.resources: Set[str] = set()
        self._manager = manager
        self._cleanup_callback = cleanup_callback

    def __enter__(self):
        """Metoda wywoływana przy wejściu w blok 'with'."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Metoda wywoływana przy wyjściu z bloku 'with'.
        Czyści zarejestrowane zasoby.

        Args:
            exc_type: Typ wyjątku
            exc_val: Wartość wyjątku
            exc_tb: Traceback wyjątku
        """
        self.cleanup()

    def register(self, resource_name: str) -> None:
        """
        Rejestruje zasób w kontekście.

        Args:
            resource_name: Nazwa zasobu
        """
        self.resources.add(resource_name)

    def cleanup(self) -> None:
        """Czyści wszystkie zasoby zarejestrowane w kontekście."""
        if self._manager and hasattr(self._manager, "unregister_resource"):
            for resource_name in self.resources:
                self._manager.unregister_resource(resource_name, owner=self.name)

        if self._cleanup_callback:
            self._cleanup_callback(self.resources)

        self.resources.clear()


class ResourceManager(QObject):
    """
    Scentralizowany manager zasobów aplikacji.
    Zarządza ładowaniem CSS, tłumaczeń i innych zasobów, z mechanizmem automatycznego czyszczenia.
    """

    resources_loaded = pyqtSignal()
    css_loaded = pyqtSignal(str)
    translations_loaded = pyqtSignal(dict)
    loading_failed = pyqtSignal(str, str)  # resource_name, error_message
    memory_warning = pyqtSignal(str)  # warning_message

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

        # Tracker zasobów dla monitorowania i zarządzania
        self.tracker = ResourceTracker()

        # Automatyczne czyszczenie przy zamknięciu aplikacji
        atexit.register(self.cleanup)

        self._setup_loaders()

        # Podłącz sygnały
        self.async_loader.resource_loaded.connect(self._handle_resource_loaded)
        self.async_loader.loading_failed.connect(self.loading_failed)

        # Uruchom monitorowanie zasobów
        self.tracker.start_monitoring(interval=300)  # co 5 minut

    def _setup_loaders(self):
        """Konfiguracja loaderów dla różnych typów zasobów."""
        # CSS
        css_path = os.path.join(self.base_dir, "resources", "styles.qss")
        self.css_loader = create_css_loader(css_path)
        lazy_loader.register_loader("main_css", self.css_loader)

        # Zarejestruj CSS loader w trackerze
        self.tracker.register_resource(
            "main_css", "css_loader", self.css_loader, owner="ResourceManager"
        )

        # Translations
        self.translation_loader = self._create_translation_loader()
        lazy_loader.register_loader("translations", self.translation_loader)

        # Zarejestruj translation loader w trackerze
        self.tracker.register_resource(
            "translations",
            "translation_loader",
            self.translation_loader,
            owner="ResourceManager",
        )

    def load_all_resources(self):
        """Jednokrotne załadowanie wszystkich zasobów."""
        self.logger.debug("Rozpoczynam ładowanie wszystkich zasobów...")

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
            self.logger.debug("CSS styles loaded from cache")
            # Zarejestruj załadowany CSS w trackerze
            self.tracker.register_resource(
                "main_css_data", "css", styles, owner="ResourceManager"
            )
            return styles
        except Exception as e:
            self.logger.warning(f"Could not load CSS from cache: {e}")
            # Załaduj bezpośrednio
            if self.css_loader:
                styles = self.css_loader()
                # Zarejestruj załadowany CSS w trackerze
                self.tracker.register_resource(
                    "main_css_data", "css", styles, owner="ResourceManager"
                )
                return styles
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
            self.logger.debug("Translations loaded from cache")
            # Zarejestruj tłumaczenia w trackerze
            self.tracker.register_resource(
                "translations_data",
                "translations",
                translations,
                owner="ResourceManager",
            )
            return translations
        except Exception as e:
            self.logger.warning(f"Could not load translations from cache: {e}")
            # Załaduj bezpośrednio
            if self.translation_loader:
                translations = self.translation_loader()
                # Zarejestruj tłumaczenia w trackerze
                self.tracker.register_resource(
                    "translations_data",
                    "translations",
                    translations,
                    owner="ResourceManager",
                )
                return translations
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

    def create_resource_context(self, context_name: str) -> ResourceContext:
        """
        Tworzy kontekst zasobu dla automatycznego zarządzania zasobami.

        Args:
            context_name: Nazwa kontekstu

        Returns:
            Obiekt ResourceContext
        """
        return ResourceContext(
            context_name,
            manager=self,
            cleanup_callback=lambda resources: self.logger.debug(
                f"Cleaned up resources for context {context_name}: {resources}"
            ),
        )

    def register_resource(
        self, name: str, resource_type: str, resource: Any, owner=None
    ) -> None:
        """
        Rejestruje zasób w managerze.

        Args:
            name: Nazwa zasobu
            resource_type: Typ zasobu
            resource: Obiekt zasobu
            owner: Właściciel zasobu (domyślnie: None)
        """
        self.tracker.register_resource(name, resource_type, resource, owner)

    def unregister_resource(self, name: str, owner=None) -> None:
        """
        Wyrejestrowuje zasób z managera.

        Args:
            name: Nazwa zasobu
            owner: Właściciel zasobu (domyślnie: None)
        """
        self.tracker.unregister_resource(name, owner)

    def get_resource_statistics(self) -> Dict[str, Dict]:
        """
        Pobiera statystyki zużycia zasobów.

        Returns:
            Słownik statystyk zużycia zasobów
        """
        return self.tracker.get_statistics()

    def cleanup(self):
        """Czyszczenie zasobów przed zamknięciem aplikacji."""
        self.tracker.stop_monitoring()

        # Usuń wszystkie zasoby
        resources = self.tracker.get_all_resources()
        for name in list(resources.keys()):
            self.tracker.unregister_resource(name)

        self.async_loader.cancel_all()
        self.async_loader.cleanup()

        # Wywołaj garbage collection aby upewnić się, że zasoby zostaną zwolnione
        gc.collect()

        self.logger.debug("ResourceManager cleaned up")


# Dekorator dla automatycznego czyszczenia zasobów
def auto_cleanup_resource(resource_type: str):
    """
    Dekorator, który automatycznie zarejestruje i wyczyści zasoby utworzone przez funkcję.

    Args:
        resource_type: Typ zasobu

    Returns:
        Dekorowana funkcja
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Sprawdź czy pierwszy argument to ResourceManager lub ma tracker
            manager = None
            if args and (
                isinstance(args[0], ResourceManager)
                or hasattr(args[0], "tracker")
                and isinstance(args[0].tracker, ResourceTracker)
            ):
                manager = args[0]

            # Pobierz wynik funkcji
            result = func(*args, **kwargs)

            # Jeśli mamy dostęp do managera, zarejestruj zasób
            if manager:
                resource_name = f"{func.__name__}_{id(result)}"
                if hasattr(manager, "register_resource"):
                    manager.register_resource(
                        resource_name, resource_type, result, owner=func.__name__
                    )
                elif hasattr(manager, "tracker") and hasattr(
                    manager.tracker, "register_resource"
                ):
                    manager.tracker.register_resource(
                        resource_name, resource_type, result, owner=func.__name__
                    )

            return result

        return wrapper

    return decorator


# Funkcja pomocnicza do dekorowania funkcji z TTL cache
def cached_with_ttl(ttl_seconds=300, max_size=128, cleanup_interval=60):
    """
    Dekorator dodający TTL do cache'a funkcji z automatycznym czyszczeniem.

    Args:
        ttl_seconds: Czas życia w sekundach dla elementów w cache
        max_size: Maksymalny rozmiar cache'a
        cleanup_interval: Interwał automatycznego czyszczenia w sekundach

    Returns:
        Dekorator funkcji
    """

    def decorator(func):
        cache = {}
        last_cleanup = time.time()
        lock = threading.RLock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_cleanup

            with lock:
                # Automatyczne czyszczenie cache'a
                now = time.time()
                if now - last_cleanup > cleanup_interval:
                    keys_to_remove = []
                    for k, (_, timestamp) in cache.items():
                        if now - timestamp > ttl_seconds:
                            keys_to_remove.append(k)

                    for k in keys_to_remove:
                        del cache[k]

                    last_cleanup = now

                # Ograniczenie rozmiaru cache'a
                if len(cache) >= max_size:
                    # Usuń najstarsze elementy
                    oldest_key = min(cache.items(), key=lambda x: x[1][1])[0]
                    del cache[oldest_key]

                # Główna logika cache'a
                key = (args, tuple(sorted(kwargs.items())))
                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < ttl_seconds:
                        return result

                result = func(*args, **kwargs)
                cache[key] = (result, now)
                return result

        # Dodaj metodę do ręcznego czyszczenia cache'a
        def clear_cache():
            with lock:
                cache.clear()

        wrapper.clear_cache = clear_cache
        return wrapper

    return decorator
