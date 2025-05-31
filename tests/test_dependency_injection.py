#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testy jednostkowe dla modułu dependency_injection.

Ten moduł zawiera testy sprawdzające funkcjonalność klasy ServiceContainer
i dekoratorów inject oraz register_service.
"""

import unittest
from typing import Dict, List, Optional

from architecture.dependency_injection import (
    ServiceAlreadyRegisteredError,
    ServiceContainer,
    ServiceNotFoundError,
    inject,
    register_service,
)


class TestServiceContainer(unittest.TestCase):
    """Testy jednostkowe dla klasy ServiceContainer."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        # Utwórz czysty kontener przed każdym testem
        self.container = ServiceContainer()

    def test_register_and_resolve_service(self):
        """Test rejestracji i rozwiązywania serwisu."""

        # Prosta klasa testowa
        class TestService:
            def get_data(self):
                return "test_data"

        # Rejestrujemy serwis
        self.container.register_service("test_service", TestService)

        # Próbujemy rozwiązać serwis
        service = self.container.resolve("test_service")

        # Sprawdzamy, czy serwis jest poprawną instancją
        self.assertIsInstance(service, TestService)
        self.assertEqual(service.get_data(), "test_data")

    def test_register_instance(self):
        """Test rejestracji i rozwiązywania instancji."""

        # Prosta klasa testowa
        class TestService:
            def __init__(self, value: str):
                self.value = value

            def get_value(self):
                return self.value

        # Tworzymy instancję
        instance = TestService("predefined_value")

        # Rejestrujemy instancję
        self.container.register_instance("test_instance", instance)

        # Próbujemy rozwiązać instancję
        resolved = self.container.resolve("test_instance")

        # Sprawdzamy, czy to ta sama instancja
        self.assertIs(resolved, instance)
        self.assertEqual(resolved.get_value(), "predefined_value")

    def test_singleton_behavior(self):
        """Test zachowania singletona - wielokrotne resolve zwraca tę samą instancję."""

        # Prosta klasa testowa z licznikiem instancji
        class CounterService:
            instance_count = 0

            def __init__(self):
                CounterService.instance_count += 1
                self.id = CounterService.instance_count

        # Rejestrujemy serwis (domyślnie singleton=True)
        self.container.register_service("counter", CounterService)

        # Pobieramy kilka instancji
        counter1 = self.container.resolve("counter")
        counter2 = self.container.resolve("counter")
        counter3 = self.container.resolve("counter")

        # Sprawdzamy, czy wszystkie są tą samą instancją
        self.assertIs(counter1, counter2)
        self.assertIs(counter2, counter3)
        self.assertEqual(counter1.id, 1)
        self.assertEqual(
            CounterService.instance_count, 1
        )  # Tylko jedna instancja powinna zostać utworzona

    def test_transient_behavior(self):
        """Test zachowania transient - każde resolve tworzy nową instancję."""

        # Rejestrujemy serwis z włączonym transient (singleton=False)
        class CounterService:
            instance_count = 0

            def __init__(self):
                CounterService.instance_count += 1
                self.id = CounterService.instance_count

        # Rejestrujemy serwis jako transient (singleton=False)
        self.container.register_service(
            "counter_transient", CounterService, singleton=False
        )

        # Pobieramy kilka instancji
        counter1 = self.container.resolve("counter_transient")
        counter2 = self.container.resolve("counter_transient")

        # Sprawdzamy, czy to różne instancje
        self.assertIsNot(counter1, counter2)
        self.assertEqual(counter1.id, 1)
        self.assertEqual(counter2.id, 2)
        self.assertEqual(
            CounterService.instance_count, 2
        )  # Powinny zostać utworzone dwie instancje

    def test_service_provider(self):
        """Test rejestracji z własnym providerem."""

        # Własny provider
        def custom_provider():
            return {"key": "custom_value"}

        # Rejestrujemy serwis z własnym providerem
        self.container.register_service("dict_service", custom_provider)

        # Pobieramy instancję
        result = self.container.resolve("dict_service")

        # Sprawdzamy, czy provider został użyty
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], "custom_value")

    def test_service_not_found(self):
        """Test rzucania wyjątku, gdy serwis nie istnieje."""
        with self.assertRaises(ServiceNotFoundError):
            self.container.resolve("non_existent_service")

    def test_service_already_registered(self):
        """Test rzucania wyjątku, gdy serwis jest już zarejestrowany."""
        # Rejestrujemy serwis
        self.container.register_service("duplicate", str)

        # Próbujemy zarejestrować ponownie
        with self.assertRaises(ServiceAlreadyRegisteredError):
            self.container.register_service("duplicate", int)

    def test_overwrite_service(self):
        """Test nadpisywania istniejącego serwisu."""
        # Rejestrujemy serwis
        self.container.register_service("test", str)
        self.assertEqual(self.container.resolve("test"), "")

        # Nadpisujemy serwis
        self.container.register_service("test", int, overwrite=True)
        self.assertEqual(self.container.resolve("test"), 0)

    def test_unregister_service(self):
        """Test wyrejestrowywania serwisu."""
        # Rejestrujemy serwis
        self.container.register_service("temp", str)

        # Sprawdzamy, czy serwis istnieje
        self.assertTrue(self.container.resolve("temp") == "")

        # Wyrejestrowujemy serwis
        self.container.unregister_service("temp")

        # Sprawdzamy, czy serwis został wyrejestrowany
        with self.assertRaises(ServiceNotFoundError):
            self.container.resolve("temp")

    def test_unregister_non_existent(self):
        """Test wyrejestrowywania nieistniejącego serwisu."""
        # Próbujemy wyrejestrować nieistniejący serwis - nie powinno rzucać wyjątku
        self.container.unregister_service("non_existent")

        # Sprawdzamy, czy próba wyrejestrowania z raise_if_not_found=True rzuca wyjątek
        with self.assertRaises(ServiceNotFoundError):
            self.container.unregister_service("non_existent", raise_if_not_found=True)

    def test_clear(self):
        """Test czyszczenia kontenera."""
        # Rejestrujemy kilka serwisów
        self.container.register_service("service1", str)
        self.container.register_service("service2", int)
        self.container.register_instance("service3", "instance")

        # Czyścimy kontener
        self.container.clear()

        # Sprawdzamy, czy serwisy zostały usunięte
        with self.assertRaises(ServiceNotFoundError):
            self.container.resolve("service1")
        with self.assertRaises(ServiceNotFoundError):
            self.container.resolve("service2")
        with self.assertRaises(ServiceNotFoundError):
            self.container.resolve("service3")


class TestDecorators(unittest.TestCase):
    """Testy jednostkowe dla dekoratorów."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        # Czyszczenie globalnego kontenera
        ServiceContainer.get_instance().clear()

    def test_register_service_decorator(self):
        """Test dekoratora register_service."""

        # Dekorowana klasa
        @register_service
        class TestService:
            def get_data(self):
                return "decorated_data"

        # Próbujemy rozwiązać serwis
        service = ServiceContainer.get_instance().resolve("TestService")

        # Sprawdzamy, czy serwis jest poprawną instancją
        self.assertIsInstance(service, TestService)
        self.assertEqual(service.get_data(), "decorated_data")

    def test_register_service_with_name(self):
        """Test dekoratora register_service z własną nazwą."""

        # Dekorowana klasa z własną nazwą
        @register_service("custom_name")
        class TestService:
            def get_data(self):
                return "custom_named_service"

        # Próbujemy rozwiązać serwis po niestandardowej nazwie
        service = ServiceContainer.get_instance().resolve("custom_name")

        # Sprawdzamy, czy serwis jest poprawną instancją
        self.assertIsInstance(service, TestService)
        self.assertEqual(service.get_data(), "custom_named_service")

    def test_register_service_with_provider(self):
        """Test dekoratora register_service z własnym providerem."""

        # Dekorowana klasa z własnym providerem
        @register_service(provider=lambda: {"source": "custom_provider"})
        class TestService:
            pass

        # Próbujemy rozwiązać serwis
        service = ServiceContainer.get_instance().resolve("TestService")

        # Sprawdzamy, czy provider został użyty
        self.assertIsInstance(service, dict)
        self.assertEqual(service["source"], "custom_provider")

    def test_inject_decorator(self):
        """Test dekoratora inject."""

        # Rejestrujemy serwis
        @register_service("dependency")
        class Dependency:
            def get_value(self):
                return "injected_value"

        # Klasa wykorzystująca wstrzykiwanie
        class Consumer:
            @inject
            def __init__(self, dependency: Dependency = None):
                self.dependency = dependency

            def use_dependency(self):
                return self.dependency.get_value()

        # Tworzymy instancję konsumenta
        consumer = Consumer()

        # Sprawdzamy, czy zależność została wstrzyknięta
        self.assertIsInstance(consumer.dependency, Dependency)
        self.assertEqual(consumer.use_dependency(), "injected_value")

    def test_inject_by_name(self):
        """Test dekoratora inject z jawnym określeniem serwisu."""

        # Rejestrujemy serwis
        @register_service("named_dependency")
        class Dependency:
            def get_value(self):
                return "named_injection"

        # Klasa wykorzystująca wstrzykiwanie przez nazwę
        class Consumer:
            @inject("named_dependency")
            def __init__(self, dep):
                self.dependency = dep

            def use_dependency(self):
                return self.dependency.get_value()

        # Tworzymy instancję konsumenta
        consumer = Consumer()

        # Sprawdzamy, czy zależność została wstrzyknięta
        self.assertIsInstance(consumer.dependency, Dependency)
        self.assertEqual(consumer.use_dependency(), "named_injection")

    def test_inject_by_mapping(self):
        """Test dekoratora inject z mapowaniem serwisów na parametry."""

        # Rejestrujemy serwisy
        @register_service("service_a")
        class ServiceA:
            def get_value(self):
                return "a_value"

        @register_service("service_b")
        class ServiceB:
            def get_value(self):
                return "b_value"

        # Klasa wykorzystująca wstrzykiwanie przez mapowanie
        class Consumer:
            @inject(first="service_a", second="service_b")
            def __init__(self, first=None, second=None):
                self.service_a = first
                self.service_b = second

        # Tworzymy instancję konsumenta
        consumer = Consumer()

        # Sprawdzamy, czy zależności zostały wstrzyknięte
        self.assertEqual(consumer.service_a.get_value(), "a_value")
        self.assertEqual(consumer.service_b.get_value(), "b_value")

    def test_explicit_argument_not_overwritten(self):
        """Test, że jawnie przekazane argumenty nie są nadpisywane przez inject."""

        # Rejestrujemy serwis
        @register_service("default_service")
        class Service:
            def get_value(self):
                return "default"

        # Własna instancja
        explicit_instance = Service()
        explicit_instance.get_value = lambda: "explicit"

        # Klasa z dekorowaną metodą
        class Consumer:
            @inject
            def process(self, default_service=None):
                return default_service.get_value()

        # Tworzymy instancję konsumenta
        consumer = Consumer()

        # Wywołujemy metodę z domyślnym wstrzykiwaniem
        default_result = consumer.process()
        self.assertEqual(default_result, "default")

        # Wywołujemy metodę z jawnie przekazanym argumentem
        explicit_result = consumer.process(explicit_instance)
        self.assertEqual(explicit_result, "explicit")

    def test_service_not_found_warning(self):
        """Test ostrzeżenia, gdy serwis do wstrzyknięcia nie istnieje."""

        # Klasa z wstrzykiwaniem nieistniejącego serwisu
        class Consumer:
            @inject
            def process(self, non_existent_service=None):
                return non_existent_service

        # Tworzymy instancję i wywołujemy metodę - nie powinno rzucać wyjątku
        consumer = Consumer()
        result = consumer.process()

        # Powinniśmy dostać None, bo serwis nie istnieje
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
