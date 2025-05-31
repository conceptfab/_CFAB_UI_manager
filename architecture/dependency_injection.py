# Dependency Injection Container
# Simple DI container for loose coupling and better testability

import functools
import inspect
import logging
import warnings
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceNotFoundError(Exception):
    """Wyjątek rzucany, gdy serwis nie zostanie znaleziony w kontenerze."""

    pass


class ServiceAlreadyRegisteredError(Exception):
    """Wyjątek rzucany, gdy próba rejestracji serwisu o nazwie, która już istnieje."""

    pass


class ServiceContainer:
    """
    Kontener wstrzykiwania zależności do zarządzania serwisami aplikacji.
    Implementuje wzorzec singleton.
    """

    _instance = None

    @classmethod
    def get_instance(cls):
        """Pobiera globalną instancję kontenera."""
        if cls._instance is None:
            cls._instance = ServiceContainer()
        return cls._instance

    def __init__(self):
        # Słownik na rejestracje serwisów: name -> ServiceRegistration
        self._services: Dict[str, Any] = {}
        # Cache dla instancji singletonów: name -> instance
        self._singleton_cache: Dict[str, Any] = {}

    def register_service(
        self,
        name: str,
        service_class: Union[Type[T], Callable[[], T]],
        singleton: bool = True,
        provider: Optional[Callable[[], T]] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Rejestruje serwis w kontenerze.

        Args:
            name: Nazwa serwisu
            service_class: Klasa serwisu lub funkcja fabrykująca
            singleton: Czy serwis ma być singletonem (True) czy transient (False)
            provider: Opcjonalna funkcja dostarczająca instancję serwisu
            overwrite: Czy nadpisać istniejący serwis o tej samej nazwie

        Raises:
            ServiceAlreadyRegisteredError: Gdy serwis o podanej nazwie już istnieje i overwrite=False
        """
        # Sprawdź, czy serwis już istnieje
        if name in self._services and not overwrite:
            raise ServiceAlreadyRegisteredError(
                f"Service '{name}' is already registered"
            )

        # Jeśli provider nie jest przekazany, użyj klasy jako domyślnego providera
        actual_provider = provider if provider is not None else service_class

        # Zapisz rejestrację serwisu
        self._services[name] = {"provider": actual_provider, "singleton": singleton}

        # Wyczyść cache dla tego serwisu, jeśli nadpisujemy
        if overwrite and name in self._singleton_cache:
            del self._singleton_cache[name]

        logger.debug(f"Registered service: {name} (singleton={singleton})")

    def register_instance(
        self, name: str, instance: Any, overwrite: bool = False
    ) -> None:
        """
        Rejestruje gotową instancję jako serwis (zawsze singleton).

        Args:
            name: Nazwa serwisu
            instance: Instancja do zarejestrowania
            overwrite: Czy nadpisać istniejący serwis o tej samej nazwie

        Raises:
            ServiceAlreadyRegisteredError: Gdy serwis o podanej nazwie już istnieje i overwrite=False
        """
        # Sprawdź, czy serwis już istnieje
        if name in self._services and not overwrite:
            raise ServiceAlreadyRegisteredError(
                f"Service '{name}' is already registered"
            )

        # Zarejestruj instancję jako provider zwracający gotową instancję
        self._services[name] = {
            "provider": lambda: instance,
            "singleton": True,  # Zawsze singleton dla instancji
        }

        # Zapisz instancję w cache
        self._singleton_cache[name] = instance

        logger.debug(f"Registered instance: {name}")

    def resolve(self, name: str) -> Any:
        """
        Rozwiązuje serwis, zwracając jego instancję.

        Args:
            name: Nazwa serwisu do rozwiązania

        Returns:
            Instancję zarejestrowanego serwisu

        Raises:
            ServiceNotFoundError: Gdy serwis o podanej nazwie nie istnieje
        """
        # Sprawdź, czy serwis istnieje
        if name not in self._services:
            raise ServiceNotFoundError(f"Service '{name}' is not registered")

        service_info = self._services[name]
        is_singleton = service_info["singleton"]
        provider = service_info["provider"]

        # Dla singletona, sprawdź cache
        if is_singleton:
            if name in self._singleton_cache:
                return self._singleton_cache[name]
            else:
                # Utwórz instancję i dodaj do cache
                instance = provider() if callable(provider) else provider
                self._singleton_cache[name] = instance
                return instance
        else:
            # Dla transient, zawsze twórz nową instancję
            return provider() if callable(provider) else provider

    def unregister_service(self, name: str, raise_if_not_found: bool = False) -> None:
        """
        Wyrejestrowuje serwis z kontenera.

        Args:
            name: Nazwa serwisu do wyrejestrowania
            raise_if_not_found: Czy rzucić wyjątek, gdy serwis nie istnieje

        Raises:
            ServiceNotFoundError: Gdy serwis nie istnieje i raise_if_not_found=True
        """
        if name not in self._services:
            if raise_if_not_found:
                raise ServiceNotFoundError(f"Service '{name}' is not registered")
            return

        # Usuń serwis z rejestracji i cache
        del self._services[name]
        if name in self._singleton_cache:
            del self._singleton_cache[name]

        logger.debug(f"Unregistered service: {name}")

    def clear(self) -> None:
        """
        Czyści wszystkie zarejestrowane serwisy.
        """
        self._services.clear()
        self._singleton_cache.clear()
        logger.debug("Container cleared")


# Funkcje pomocnicze dla dekoratorów


def register_service(
    cls_or_name=None,
    *,
    singleton: bool = True,
    provider: Optional[Callable] = None,
    overwrite: bool = False,
):
    """
    Dekorator do rejestracji klasy jako serwisu.

    Przykłady:
        @register_service  # Rejestruje klasę pod jej nazwą
        class MyService:
            pass

        @register_service("custom_name")  # Rejestruje pod podaną nazwą
        class MyService:
            pass

        @register_service(singleton=False)  # Jako transient (nowa instancja za każdym razem)
        class MyTransientService:
            pass

        @register_service(provider=lambda: CustomObject())  # Z własnym providerem
        class MyProvidedService:
            pass

    Args:
        cls_or_name: Klasa do dekorowania lub nazwa serwisu
        singleton: Czy serwis ma być singletonem
        provider: Opcjonalna funkcja tworząca instancje serwisu
        overwrite: Czy nadpisać istniejący serwis o tej samej nazwie
    """
    container = ServiceContainer.get_instance()

    def decorator(cls):
        # Jeśli cls_or_name to string, użyj go jako nazwy
        # W przeciwnym razie użyj nazwy klasy
        name = cls_or_name if isinstance(cls_or_name, str) else cls.__name__
        container.register_service(
            name, cls, singleton=singleton, provider=provider, overwrite=overwrite
        )
        return cls

    # Sprawdź, czy dekorator został wywołany bez nawiasów
    if (
        cls_or_name is not None
        and not isinstance(cls_or_name, str)
        and callable(cls_or_name)
    ):
        # Dekorator użyty jako @register_service
        return decorator(cls_or_name)
    else:
        # Dekorator użyty jako @register_service(...) lub @register_service("name")
        return decorator


def inject(*args, **service_map):
    """
    Dekorator do wstrzykiwania zależności do funkcji lub metody.

    Może być użyty na kilka sposobów:

    1. @inject - domyślne wstrzykiwanie na podstawie nazw parametrów
    2. @inject("service_a") - wstrzykiwanie serwisu o podanej nazwie do pierwszego parametru
    3. @inject(param_name="service_name") - mapowanie nazw serwisów na parametry

    Args:
        *args: Opcjonalne nazwy serwisów do wstrzyknięcia pozycyjnie
        **service_map: Mapowanie parametrów na nazwy serwisów

    Returns:
        Dekorowana funkcja z wstrzykniętymi zależnościami
    """
    container = ServiceContainer.get_instance()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*call_args, **call_kwargs):
            # Kopiujemy argumenty wywołania, aby ich nie modyfikować bezpośrednio
            kwargs = dict(call_kwargs)

            # Pobieramy informacje o parametrach funkcji
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())

            # Obliczamy, ile parametrów już otrzymało wartości przez args
            positional_count = min(len(call_args), len(param_names))
            positional_params = param_names[:positional_count]

            # Dla każdego serwisu podanego pozycyjnie w @inject("service_a", "service_b", ...)
            for i, service_name in enumerate(args):
                if isinstance(service_name, str):
                    # Znajdź parametr, do którego ma być wstrzyknięty ten serwis
                    if i + positional_count < len(param_names):
                        param_name = param_names[i + positional_count]

                        # Wstrzykujemy tylko, jeśli parametr nie został już przekazany
                        if param_name not in kwargs:
                            try:
                                kwargs[param_name] = container.resolve(service_name)
                            except ServiceNotFoundError as e:
                                logger.warning(
                                    f"Warning: For service '{service_name}' (injected by position): {str(e)}"
                                )
                                # Nie ustawiamy parametru, pozwalamy funkcji użyć wartości domyślnej

            # Dla każdego mapowania param_name="service_name" w @inject(param=service)
            for param_name, service_name in service_map.items():
                # Wstrzykujemy tylko, jeśli parametr nie został już przekazany
                if param_name not in kwargs and param_name in param_names:
                    try:
                        kwargs[param_name] = container.resolve(service_name)
                    except ServiceNotFoundError as e:
                        logger.warning(
                            f"Warning: For parameter '{param_name}': {str(e)}"
                        )
                        # Nie ustawiamy parametru, pozwalamy funkcji użyć wartości domyślnej

            # Dla każdego parametru, który nie otrzymał wartości, spróbuj wstrzyknąć serwis o tej samej nazwie
            if (
                not args and not service_map
            ):  # Tylko dla domyślnego @inject bez argumentów
                for param_name in param_names:
                    if param_name not in kwargs and param_name not in positional_params:
                        try:
                            kwargs[param_name] = container.resolve(param_name)
                        except ServiceNotFoundError:
                            # Nie ma serwisu o takiej nazwie, ignorujemy i pozwalamy funkcji użyć wartości domyślnej
                            pass

            # Wywołujemy funkcję z oryginalnymi argumentami pozycyjnymi i uzupełnionymi named argumentami
            return func(*call_args, **kwargs)

        return wrapper

    # Sprawdź, czy dekorator został wywołany bezpośrednio na funkcji
    if len(args) == 1 and callable(args[0]) and not service_map:
        decorated_func = args[0]
        args = ()  # Reset args do pustej krotki
        return decorator(decorated_func)
    else:
        return decorator


# Globalna instancja kontenera
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """
    Pobiera globalną instancję kontenera.

    Returns:
        Globalny kontener DI
    """
    return ServiceContainer.get_instance()


def configure_dependencies():
    """
    Konfiguruje kontener zależności dla aplikacji.
    Ta funkcja powinna być wywołana po zaimportowaniu wszystkich modułów,
    aby uniknąć problemów z importami cyklicznymi.

    Returns:
        bool: True jeśli konfiguracja się powiodła, False w przeciwnym wypadku
    """
    try:
        from utils.config_cache import ConfigurationCache
        from utils.improved_thread_manager import ImprovedThreadManager
        from utils.performance_optimizer import PerformanceMonitor
        from utils.translation_manager import TranslationManager

        container = ServiceContainer.get_instance()

        # Rejestrujemy podstawowe serwisy jako singletony
        container.register_instance("TranslationManager", TranslationManager())
        container.register_instance("ImprovedThreadManager", ImprovedThreadManager())
        container.register_instance("PerformanceMonitor", PerformanceMonitor())
        container.register_instance("ConfigurationCache", ConfigurationCache())

        logger.info("Dependencies configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure dependencies: {e}")
        return False
