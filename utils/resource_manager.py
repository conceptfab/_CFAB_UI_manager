"""
Scentralizowany manager zasobów dla aplikacji.
Zarządza ładowaniem CSS, tłumaczeń i innych zasobów.
"""

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from utils.performance_optimizer import (
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
    progress_updated = pyqtSignal(str, int)  # resource_name, progress_percentage
    all_completed = pyqtSignal()

    def __init__(
        self, base_dir, logger_instance, max_workers=2
    ):  # Dodano logger_instance
        """
        Inicjalizacja ResourceManager.

        Args:
            base_dir: Ścieżka bazowa do głównego katalogu aplikacji
            logger_instance: Instancja loggera aplikacji # Dodano opis
            max_workers: Maksymalna liczba wątków dla asynchronicznego ładowania
        """
        print("[DEBUG] ResourceManager.__init__() started.")
        super().__init__()
        self.base_dir = base_dir
        self.logger = logger_instance  # Przypisanie loggera do atrybutu instancji
        self.css_loader = None
        self.translation_loader = None
        self.translations = {}
        self._setup_loaders()

        # Async loading components
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.loading_tasks: Dict[str, Any] = {}
        self.completed_tasks = 0
        self.total_tasks = 0
        self._lock = threading.Lock()

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
        print("[DEBUG] ResourceManager.load_all_resources() started.")
        if self.logger:
            self.logger.info("Rozpoczynam ładowanie wszystkich zasobów...")
        else:
            print("[ERROR] ResourceManager.load_all_resources(): self.logger is None!")

        # Załaduj CSS asynchronicznie
        print(
            "[DEBUG] ResourceManager.load_all_resources(): Attempting to load main_css."
        )
        self.load_resource_async("main_css", self._load_css_optimized)
        print(
            "[DEBUG] ResourceManager.load_all_resources(): Call to load_resource_async for main_css completed."
        )

        # Załaduj tłumaczenia asynchronicznie
        # print("[DEBUG] ResourceManager.load_all_resources(): Attempting to load translations.")
        # self.load_resource_async(
        # "translations",
        # self.translation_manager.load_translations, # Assuming this method exists
        # self.config.get("language", "en")
        # )
        # print("[DEBUG] ResourceManager.load_all_resources(): Call to load_resource_async for translations completed.")

        # Dodaj inne zasoby w razie potrzeby
        # self.load_resource_async("some_other_resource", self._load_other_resource_method)

        # Opcjonalnie, uruchom timer do sprawdzania ukończenia, jeśli nie używasz innego mechanizmu
        # self._check_completion_timer = QTimer()
        # self._check_completion_timer.timeout.connect(self.check_all_loaded)
        # self._check_completion_timer.start(100) # Check every 100ms
        print("[DEBUG] ResourceManager.load_all_resources() exiting.")

    @performance_monitor.measure_execution_time("css_loading")
    def _load_css_optimized(self):
        """
        Loads CSS content using the optimized CSS loader.
        Now an internal method, not directly exposed.
        """
        print("[DEBUG] ResourceManager._load_css_optimized() started.")
        if self.logger:
            self.logger.info("Starting optimized CSS loading...")
        try:
            css_loader = create_css_loader(
                os.path.join(self.base_dir, "resources", "styles.qss"),
                logger=self.logger,  # Pass logger if create_css_loader accepts it
            )
            css_content = css_loader()  # Call the loader to get content
            if self.logger:
                self.logger.info(
                    f"Optimized CSS loaded successfully. Length: {len(css_content) if css_content else 0}"
                )
            print(
                f"[DEBUG] ResourceManager._load_css_optimized() finished. CSS length: {len(css_content) if css_content else 0}."
            )
            return css_content
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load CSS content: {e}", exc_info=True)
            print(f"[DEBUG] ResourceManager._load_css_optimized() EXCEPTION: {e}")
            return None  # Return None or empty string on failure

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
            logger.info("Translations loaded from cache")
            return translations
        except Exception as e:
            logger.warning(f"Could not load translations from cache: {e}")
            # Załaduj bezpośrednio
            if self.translation_loader:
                return self.translation_loader()
            return {}

    def _handle_resource_loaded(self, name, data):
        """Obsługuje załadowany zasób."""
        print(
            f"[DEBUG] ResourceManager._handle_resource_loaded() for {name}. Data is {'None' if data is None else 'Present'}"
        )
        if self.logger:
            self.logger.debug(
                f"Handling loaded resource: {name}, data length: {len(data) if isinstance(data, str) else 'N/A'}"
            )
            if name == "main_css":
                self.logger.info(
                    f"CSS data to be emitted (first 100 chars): {data[:100] if isinstance(data, str) else 'N/A'}"
                )
        else:
            print(
                f"[ERROR] ResourceManager._handle_resource_loaded(): self.logger is None for resource {name}!"
            )

        if name == "main_css":
            self.css_loaded.emit(data)
        elif name == "translations":
            self.translations = data
            self.translations_loaded.emit(data)
        # Emit resources_loaded when all initial resources are handled if needed
        # For now, individual signals are used.
        # Consider adding a counter or a more sophisticated mechanism if a single
        # resources_loaded signal is required after ALL async operations.

    def _handle_async_resource_success(self, resource_name: str, resource_data: Any):
        """Obsługuje pomyślne załadowanie zasobu asynchronicznego."""
        self.progress_updated.emit(resource_name, 100)
        self._handle_resource_loaded(resource_name, resource_data)

        with self._lock:
            self.completed_tasks += 1
            self.loading_tasks.pop(resource_name, None)
            if self.completed_tasks >= self.total_tasks:
                self.all_completed.emit()
        if self.logger:
            self.logger.info(f"Successfully loaded async resource: {resource_name}")
        else:
            print(
                f"[ERROR] ResourceManager._handle_async_resource_success(): self.logger is None for resource {resource_name}!"
            )

    def _handle_async_resource_failure(self, resource_name: str, error_msg: str):
        """Obsługuje błąd podczas ładowania zasobu asynchronicznego."""
        if self.logger:
            self.logger.error(
                f"Failed to load async resource {resource_name}: {error_msg}"
            )
        else:
            print(
                f"[ERROR] ResourceManager._handle_async_resource_failure(): self.logger is None for resource {resource_name}!"
            )
        self.loading_failed.emit(resource_name, error_msg)

        with self._lock:
            self.completed_tasks += 1  # Count as completed even if failed
            self.loading_tasks.pop(resource_name, None)
            if self.completed_tasks >= self.total_tasks:
                self.all_completed.emit()  # Emit all_completed even if some tasks failed

    def load_resource_async(
        self, resource_name: str, loader_func: Callable, *args, **kwargs
    ) -> None:
        """Load a resource asynchronously."""
        with self._lock:
            if resource_name in self.loading_tasks:
                if self.logger:
                    self.logger.warning(
                        f"Resource {resource_name} is already being loaded"
                    )
                else:
                    print(
                        f"[ERROR] ResourceManager.load_resource_async(): self.logger is None for already loading resource {resource_name}!"
                    )
                print(
                    f"[DEBUG] ResourceManager.load_resource_async(): {resource_name} already loading."
                )
                return
            self.total_tasks += 1

        logger.info(f"Starting async load for: {resource_name}")
        print(
            f"[DEBUG] ResourceManager.load_resource_async() called for: {resource_name}"
        )

        def _load_wrapper():
            if self.logger:
                self.logger.debug(f"Async load wrapper started for: {resource_name}")
            else:
                print(
                    f"[ERROR] ResourceManager._load_wrapper(): self.logger is None at start for resource {resource_name}!"
                )
            print(
                f"[DEBUG] ResourceManager._load_wrapper() started for: {resource_name}"
            )
            try:
                self.progress_updated.emit(resource_name, 0)
                if self.logger:
                    self.logger.debug(f"Calling loader_func for {resource_name}")
                else:
                    print(
                        f"[ERROR] ResourceManager._load_wrapper(): self.logger is None before calling loader_func for {resource_name}!"
                    )
                print(
                    f"[DEBUG] ResourceManager._load_wrapper(): Calling load_function for {resource_name}"
                )
                resource = loader_func(*args, **kwargs)
                if self.logger:
                    self.logger.debug(
                        f"loader_func for {resource_name} completed. Resource type: {type(resource)}, Length (if str): {len(resource) if isinstance(resource, str) else 'N/A'}"
                    )
                else:
                    print(
                        f"[ERROR] ResourceManager._load_wrapper(): self.logger is None after calling loader_func for {resource_name}!"
                    )
                print(
                    f"[DEBUG] ResourceManager._load_wrapper(): load_function for {resource_name} completed."
                )
                self._handle_async_resource_success(resource_name, resource)
            except Exception as e:
                error_msg = str(e)
                if self.logger:
                    self.logger.error(
                        f"Exception in _load_wrapper for {resource_name}: {error_msg}",
                        exc_info=True,
                    )
                else:
                    print(
                        f"[ERROR] ResourceManager._load_wrapper(): self.logger is None during exception for {resource_name}!"
                    )
                print(
                    f"[DEBUG] ResourceManager._load_wrapper(): EXCEPTION loading {resource_name}: {e}"
                )
                # Ensure failure is also handled to complete the task count
                self._handle_async_resource_failure(
                    resource_name, error_msg
                )  # Dodano obsługę błędu tutaj

            if self.logger:
                self.logger.debug(f"Async load wrapper finished for: {resource_name}")
            else:
                print(
                    f"[ERROR] ResourceManager._load_wrapper(): self.logger is None at end for resource {resource_name}!"
                )
            print(
                f"[DEBUG] ResourceManager._load_wrapper() finished for: {resource_name}"
            )

        future = self.executor.submit(_load_wrapper)
        with self._lock:
            self.loading_tasks[resource_name] = future

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all loading tasks to complete."""
        try:
            futures = list(self.loading_tasks.values())
            if futures:
                for future in futures:
                    future.result(timeout=timeout)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error waiting for resource loading completion: {e}")
            else:
                print(
                    f"[ERROR] ResourceManager.wait_for_completion(): self.logger is None!"
                )
            return False

    def cancel_all_async_tasks(self) -> None:
        """Cancel all pending asynchronous loading tasks."""
        with self._lock:
            for future in self.loading_tasks.values():
                future.cancel()
            self.loading_tasks.clear()
            # Reset counters if tasks are cancelled
            self.total_tasks = 0
            self.completed_tasks = 0
            if self.logger:  # Użycie self.logger
                self.logger.info("Cancelled all async loading tasks")
            else:
                print(
                    "[ERROR] ResourceManager.cancel_all_async_tasks(): self.logger is None!"
                )

    def invalidate_cache(self, resource_name=None):
        """
        Invaliduje cache dla określonego zasobu lub wszystkich zasobów.

        Args:
            resource_name: Nazwa zasobu do invalidacji lub None dla wszystkich
        """
        lazy_loader.clear_cache(resource_name)
        if self.logger:  # Użycie self.logger
            self.logger.info(
                f"Cache invalidated for {resource_name or 'all resources'}"
            )
        else:
            print(f"[ERROR] ResourceManager.invalidate_cache(): self.logger is None!")

    def cleanup(self):
        """Czyszczenie zasobów przed zamknięciem aplikacji."""
        self.cancel_all_async_tasks()
        self.executor.shutdown(wait=False)
        if self.logger:  # Użycie self.logger
            self.logger.debug("ResourceManager cleaned up")
        else:
            print("[ERROR] ResourceManager.cleanup(): self.logger is None!")


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
