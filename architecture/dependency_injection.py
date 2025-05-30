# Dependency Injection Container
# Simple DI container for loose coupling and better testability

import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DependencyContainer:
    """
    Simple dependency injection container for managing application dependencies
    """

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """
        Register a singleton instance

        Args:
            service_type: The type/interface of the service
            instance: The actual instance to register
        """
        self._singletons[service_type] = instance
        logger.debug(f"Registered singleton: {service_type.__name__}")

    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory function that creates instances

        Args:
            service_type: The type/interface of the service
            factory: Factory function that creates instances
        """
        self._factories[service_type] = factory
        logger.debug(f"Registered factory: {service_type.__name__}")

    def register_transient(
        self, service_type: Type[T], implementation: Type[T]
    ) -> None:
        """
        Register a transient service (new instance each time)

        Args:
            service_type: The type/interface of the service
            implementation: The concrete implementation class
        """
        self._services[service_type] = implementation
        logger.debug(f"Registered transient: {service_type.__name__}")

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance

        Args:
            service_type: The type of service to resolve

        Returns:
            The resolved service instance

        Raises:
            ValueError: If the service type is not registered
        """
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]

        # Check factories
        if service_type in self._factories:
            return self._factories[service_type]()

        # Check transient services
        if service_type in self._services:
            implementation = self._services[service_type]
            return self._create_instance(implementation)

        # Auto-resolve if possible
        if hasattr(service_type, "__init__"):
            try:
                return self._create_instance(service_type)
            except Exception as e:
                logger.error(f"Failed to auto-resolve {service_type.__name__}: {e}")

        raise ValueError(f"Service type {service_type.__name__} is not registered")

    def _create_instance(self, implementation: Type[T]) -> T:
        """
        Create an instance with dependency injection

        Args:
            implementation: The class to instantiate

        Returns:
            The created instance with injected dependencies
        """
        # Get constructor signature
        sig = inspect.signature(implementation.__init__)

        # Prepare arguments for constructor
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Try to resolve dependency
            param_type = param.annotation
            if param_type != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.resolve(param_type)
                except ValueError:
                    # If dependency can't be resolved and has default, use default
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        logger.warning(
                            f"Could not resolve dependency {param_type} for {implementation.__name__}"
                        )

        return implementation(**kwargs)

    def clear(self) -> None:
        """
        Clear all registered services
        """
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Container cleared")


# Global container instance
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """
    Get the global dependency container

    Returns:
        The global DI container
    """
    return _container


def inject(service_type: Type[T]) -> T:
    """
    Inject a service dependency

    Args:
        service_type: The type of service to inject

    Returns:
        The resolved service instance
    """
    return _container.resolve(service_type)


def configure_dependencies():
    """
    Configure the dependency container with application services.
    This should be called after all modules are imported to avoid circular imports.
    """
    try:
        from utils.config_cache import ConfigurationCache
        from utils.improved_thread_manager import ImprovedThreadManager
        from utils.performance_optimizer import PerformanceMonitor
        from utils.translation_manager import TranslationManager

        container = get_container()

        # Register core services as singletons
        container.register_singleton(TranslationManager, TranslationManager())
        container.register_singleton(ImprovedThreadManager, ImprovedThreadManager())
        container.register_singleton(PerformanceMonitor, PerformanceMonitor())
        container.register_singleton(ConfigurationCache, ConfigurationCache())

        logger.info("Dependencies configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure dependencies: {e}")
        return False
