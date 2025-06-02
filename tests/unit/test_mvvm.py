"""
Tests for the MVVM architecture components
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Dodanie ścieżki głównej projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from architecture.mvvm import BaseModel, BaseViewModel, MVVMFactory


class BaseModelTest(unittest.TestCase):
    """Unit tests for the BaseModel class"""

    def setUp(self):
        self.model = BaseModel()

    def test_get_property_nonexistent(self):
        """Should return None for non-existent properties"""
        self.assertIsNone(self.model.get_property("does_not_exist"))

    def test_set_and_get_property(self):
        """Should set and retrieve property values correctly"""
        self.model.set_property("name", "Test")
        self.assertEqual("Test", self.model.get_property("name"))

    def test_get_all_properties(self):
        """Should return a copy of all properties"""
        self.model.set_property("name", "Test")
        self.model.set_property("age", 30)

        properties = self.model.get_all_properties()
        self.assertEqual({"name": "Test", "age": 30}, properties)

        # Ensure it's a copy by modifying the returned dict
        properties["name"] = "Changed"
        self.assertEqual("Test", self.model.get_property("name"))

    def test_data_changed_signal(self):
        """Should emit data_changed signal when property is changed"""
        mock_handler = MagicMock()
        self.model.data_changed.connect(mock_handler)

        self.model.set_property("name", "Test")
        mock_handler.assert_called_once_with("name", "Test")

    def test_no_signal_when_value_unchanged(self):
        """Should not emit signal when setting the same value"""
        self.model.set_property("name", "Test")

        mock_handler = MagicMock()
        self.model.data_changed.connect(mock_handler)

        self.model.set_property("name", "Test")  # Same value
        mock_handler.assert_not_called()

    def test_clear(self):
        """Should clear all properties"""
        self.model.set_property("name", "Test")
        self.model.set_property("age", 30)

        mock_handler = MagicMock()
        self.model.data_changed.connect(mock_handler)

        self.model.clear()
        self.assertEqual({}, self.model.get_all_properties())
        mock_handler.assert_called_once_with("*", None)


class BaseViewModelTest(unittest.TestCase):
    """Unit tests for the BaseViewModel class"""

    def setUp(self):
        self.model = BaseModel()
        self.view_model = BaseViewModel(self.model)

    def test_set_model(self):
        """Should correctly set and bind to a model"""
        new_model = BaseModel()
        self.view_model.set_model(new_model)
        self.assertEqual(new_model, self.view_model.get_model())

    def test_property_changed_signal(self):
        """Should emit property_changed when model data changes"""
        mock_handler = MagicMock()
        self.view_model.property_changed.connect(mock_handler)

        self.model.set_property("name", "Test")
        mock_handler.assert_called_once_with("name", "Test")

    def test_transform_for_view(self):
        """Should transform model values for the view"""

        # Create a subclass with custom transformation
        class CustomViewModel(BaseViewModel):
            def transform_for_view(self, property_name, model_value):
                if property_name == "name":
                    return f"Mr. {model_value}"
                return model_value

        custom_vm = CustomViewModel(self.model)
        mock_handler = MagicMock()
        custom_vm.property_changed.connect(mock_handler)

        self.model.set_property("name", "Smith")
        mock_handler.assert_called_once_with("name", "Mr. Smith")

    def test_register_and_execute_command(self):
        """Should register and execute commands correctly"""
        mock_command = MagicMock(return_value=True)

        self.view_model.register_command("test_cmd", mock_command)

        # Test successful execution
        success_handler = MagicMock()
        self.view_model.command_executed.connect(success_handler)

        result = self.view_model.execute_command("test_cmd", 1, 2, key="value")

        self.assertTrue(result)
        mock_command.assert_called_once_with(1, 2, key="value")
        success_handler.assert_called_once_with("test_cmd", True)

    def test_execute_nonexistent_command(self):
        """Should return False when executing a non-existent command"""
        result = self.view_model.execute_command("nonexistent")
        self.assertFalse(result)

    def test_command_exception_handling(self):
        """Should handle exceptions in commands gracefully"""

        def failing_command():
            raise ValueError("Test error")

        self.view_model.register_command("failing", failing_command)

        failure_handler = MagicMock()
        self.view_model.command_executed.connect(failure_handler)

        result = self.view_model.execute_command("failing")
        self.assertFalse(result)
        failure_handler.assert_called_once_with("failing", False)


class MVVMFactoryTest(unittest.TestCase):
    """Unit tests for the MVVMFactory class"""

    def setUp(self):
        self.mock_container = MagicMock()
        self.factory = MVVMFactory(self.mock_container)

    def test_create_model_with_container(self):
        """Should create model using container if possible"""
        model_instance = BaseModel()
        self.mock_container.resolve.return_value = model_instance

        result = self.factory.create_model(BaseModel)
        self.assertEqual(model_instance, result)
        self.mock_container.resolve.assert_called_once_with(BaseModel)

    def test_create_model_fallback(self):
        """Should fall back to direct instantiation if container fails"""
        self.mock_container.resolve.side_effect = ValueError()

        result = self.factory.create_model(BaseModel)
        self.assertIsInstance(result, BaseModel)

    def test_create_view_model_with_container(self):
        """Should create view_model using container if possible"""
        model = BaseModel()
        view_model = BaseViewModel()
        self.mock_container.resolve.return_value = view_model

        result = self.factory.create_view_model(BaseViewModel, model)

        self.assertEqual(view_model, result)
        self.mock_container.resolve.assert_called_once_with(BaseViewModel)

    def test_create_view_model_fallback(self):
        """Should fall back to direct instantiation if container fails"""
        model = BaseModel()
        self.mock_container.resolve.side_effect = ValueError()

        result = self.factory.create_view_model(BaseViewModel, model)
        self.assertIsInstance(result, BaseViewModel)
        self.assertEqual(model, result.get_model())


if __name__ == "__main__":
    unittest.main()
