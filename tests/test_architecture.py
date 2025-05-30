# Tests for Architecture Components
# Comprehensive tests for MVVM, DI, State Management and Configuration

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from architecture import (
    AdvancedConfigManager,
    BaseModel,
    BaseViewModel,
    DependencyContainer,
    Store,
    create_config_manager,
    get_store,
    reset_store,
)


class TestDependencyInjection(unittest.TestCase):
    """Test dependency injection container"""

    def setUp(self):
        self.container = DependencyContainer()

    def test_singleton_registration(self):
        """Test singleton service registration"""
        service = Mock()
        self.container.register_singleton(Mock, service)

        resolved = self.container.resolve(Mock)
        self.assertIs(resolved, service)

    def test_factory_registration(self):
        """Test factory service registration"""
        factory = Mock(return_value=Mock())
        self.container.register_factory(Mock, factory)

        resolved = self.container.resolve(Mock)
        factory.assert_called_once()
        self.assertIsNotNone(resolved)

    def test_transient_registration(self):
        """Test transient service registration"""

        class TestService:
            def __init__(self):
                self.value = "test"

        self.container.register_transient(TestService, TestService)

        resolved1 = self.container.resolve(TestService)
        resolved2 = self.container.resolve(TestService)

        self.assertIsInstance(resolved1, TestService)
        self.assertIsInstance(resolved2, TestService)
        self.assertIsNot(resolved1, resolved2)  # Different instances


class TestMVVM(unittest.TestCase):
    """Test MVVM pattern implementation"""

    def setUp(self):
        self.model = BaseModel()
        self.view_model = BaseViewModel(self.model)

    def test_model_property_change(self):
        """Test model property changes emit signals"""
        with patch.object(self.model, "data_changed") as mock_signal:
            self.model.set_property("test_prop", "test_value")
            mock_signal.emit.assert_called_once_with("test_prop", "test_value")

    def test_view_model_binding(self):
        """Test view model binding to model"""
        with patch.object(self.view_model, "property_changed") as mock_signal:
            self.model.set_property("test_prop", "test_value")
            # Signal should be emitted through view model
            mock_signal.emit.assert_called_once()

    def test_command_execution(self):
        """Test command registration and execution"""
        test_command = Mock(return_value=True)
        self.view_model.register_command("test_command", test_command)

        result = self.view_model.execute_command("test_command", "arg1", key="value")

        test_command.assert_called_once_with("arg1", key="value")
        self.assertTrue(result)


class TestStateManagement(unittest.TestCase):
    """Test centralized state management"""

    def setUp(self):
        reset_store()  # Reset global store for clean tests
        self.store = get_store()

    def tearDown(self):
        reset_store()

    def test_initial_state(self):
        """Test store has correct initial state"""
        state = self.store.get_state()

        self.assertIn("ui", state)
        self.assertIn("hardware", state)
        self.assertIn("application", state)
        self.assertIn("preferences", state)

    def test_action_dispatch(self):
        """Test action dispatching updates state"""
        initial_tab = self.store.get_state()["ui"]["current_tab"]

        self.store.dispatch("SET_CURRENT_TAB", 2)

        new_state = self.store.get_state()
        self.assertEqual(new_state["ui"]["current_tab"], 2)
        self.assertNotEqual(initial_tab, new_state["ui"]["current_tab"])

    def test_state_subscription(self):
        """Test state change notifications"""
        subscriber = Mock()
        self.store.subscribe(subscriber)

        self.store.dispatch("SET_LANGUAGE", "en")

        subscriber.assert_called_once()
        # Verify the subscriber received the updated state
        called_state = subscriber.call_args[0][0]
        self.assertEqual(called_state["ui"]["language"], "en")

    def test_hardware_profile_action(self):
        """Test hardware profile state management"""
        profile_data = {
            "gpu_info": "NVIDIA RTX 4080",
            "cpu_info": "Intel i7-12700K",
            "memory_total": 32 * 1024**3,
        }

        self.store.dispatch("SET_HARDWARE_PROFILE", profile_data)

        state = self.store.get_state()
        self.assertTrue(state["hardware"]["profile_loaded"])
        self.assertEqual(state["hardware"]["gpu_info"], "NVIDIA RTX 4080")


class TestConfigManagement(unittest.TestCase):
    """Test advanced configuration management"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.config_manager = create_config_manager(self.config_file, validate=False)

    def tearDown(self):
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_get_set(self):
        """Test basic configuration get/set operations"""
        self.config_manager.set("test.key", "test_value")
        value = self.config_manager.get("test.key")

        self.assertEqual(value, "test_value")

    def test_config_dot_notation(self):
        """Test dot notation for nested configuration"""
        self.config_manager.set("app.ui.theme", "dark")
        self.config_manager.set("app.ui.language", "en")

        theme = self.config_manager.get("app.ui.theme")
        language = self.config_manager.get("app.ui.language")

        self.assertEqual(theme, "dark")
        self.assertEqual(language, "en")

    def test_config_transaction_commit(self):
        """Test configuration transaction commit"""
        with self.config_manager.transaction() as tx:
            tx.set("tx.key1", "value1")
            tx.set("tx.key2", "value2")

        # Values should be persisted after commit
        self.assertEqual(self.config_manager.get("tx.key1"), "value1")
        self.assertEqual(self.config_manager.get("tx.key2"), "value2")

    def test_config_transaction_rollback(self):
        """Test configuration transaction rollback on exception"""
        try:
            with self.config_manager.transaction() as tx:
                tx.set("rollback.key", "should_not_persist")
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Value should not be persisted after rollback
        self.assertIsNone(self.config_manager.get("rollback.key"))

    def test_config_backup_creation(self):
        """Test configuration backup creation"""
        # Set some initial data
        self.config_manager.set("backup.test", "initial_value")

        # Modify and save (should create backup)
        self.config_manager.set("backup.test", "modified_value")

        # Check backup was created
        backup_info = self.config_manager.get_backup_info()
        self.assertGreater(len(backup_info), 0)

    def test_config_persistence(self):
        """Test configuration persistence across instances"""
        # Set value with first instance
        self.config_manager.set("persist.test", "persistent_value")

        # Create new instance and verify value persisted
        new_manager = create_config_manager(self.config_file)
        value = new_manager.get("persist.test")

        self.assertEqual(value, "persistent_value")


class TestArchitectureIntegration(unittest.TestCase):
    """Test integration between architecture components"""

    def setUp(self):
        reset_store()
        self.container = DependencyContainer()
        self.store = get_store()

    def tearDown(self):
        reset_store()

    def test_mvvm_with_store_integration(self):
        """Test MVVM components working with centralized store"""
        # Create model that subscribes to store
        model = BaseModel()

        def update_from_store(state):
            model.set_property("language", state["ui"]["language"])

        self.store.subscribe(update_from_store)

        # Dispatch action and verify model updates
        self.store.dispatch("SET_LANGUAGE", "fr")

        self.assertEqual(model.get_property("language"), "fr")

    def test_dependency_injection_with_services(self):
        """Test DI container with mock services"""
        # Register mock services
        translation_service = Mock()
        thread_service = Mock()

        self.container.register_singleton(Mock, translation_service)
        self.container.register_singleton(type(thread_service), thread_service)

        # Resolve services
        resolved_translation = self.container.resolve(Mock)
        resolved_thread = self.container.resolve(type(thread_service))

        self.assertIs(resolved_translation, translation_service)
        self.assertIs(resolved_thread, thread_service)


if __name__ == "__main__":
    # Configure logging for tests
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    unittest.main(verbosity=2)
