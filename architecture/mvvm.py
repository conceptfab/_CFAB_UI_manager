# MVVM Base Classes
# Base classes for implementing Model-View-ViewModel pattern

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class BaseModel(QObject):
    """
    Base class for models in MVVM pattern
    """

    # Signal emitted when model data changes
    data_changed = pyqtSignal(str, object)  # property_name, new_value

    def __init__(self):
        super().__init__()
        self._data: Dict[str, Any] = {}

    def get_property(self, name: str) -> Any:
        """
        Get a property value

        Args:
            name: Property name

        Returns:
            Property value or None if not found
        """
        return self._data.get(name)

    def set_property(self, name: str, value: Any) -> None:
        """
        Set a property value and emit change signal

        Args:
            name: Property name
            value: New value
        """
        old_value = self._data.get(name)
        if old_value != value:
            self._data[name] = value
            self.data_changed.emit(name, value)
            logger.debug(f"Model property '{name}' changed: {old_value} -> {value}")

    def get_all_properties(self) -> Dict[str, Any]:
        """
        Get all properties as a dictionary

        Returns:
            Dictionary of all properties
        """
        return self._data.copy()

    def clear(self) -> None:
        """
        Clear all properties
        """
        self._data.clear()
        self.data_changed.emit("*", None)  # Signal that all data changed


class BaseViewModel(QObject):
    """
    Base class for view models in MVVM pattern
    """

    # Signals for UI updates
    property_changed = pyqtSignal(str, object)  # property_name, new_value
    command_executed = pyqtSignal(str, bool)  # command_name, success

    def __init__(self, model: Optional[BaseModel] = None):
        super().__init__()
        self._model = model
        self._commands: Dict[str, Any] = {}

        if self._model:
            self._model.data_changed.connect(self._on_model_changed)

    def set_model(self, model: BaseModel) -> None:
        """
        Set the model for this view model

        Args:
            model: The model to bind to
        """
        if self._model:
            self._model.data_changed.disconnect(self._on_model_changed)

        self._model = model
        if self._model:
            self._model.data_changed.connect(self._on_model_changed)

        logger.debug(f"ViewModel bound to model: {type(model).__name__}")

    def get_model(self) -> Optional[BaseModel]:
        """
        Get the current model

        Returns:
            The current model or None
        """
        return self._model

    def _on_model_changed(self, property_name: str, new_value: Any) -> None:
        """
        Handle model changes

        Args:
            property_name: Name of the changed property
            new_value: New value of the property
        """
        # Transform model data for view if needed
        view_value = self.transform_for_view(property_name, new_value)
        self.property_changed.emit(property_name, view_value)

    def transform_for_view(self, property_name: str, model_value: Any) -> Any:
        """
        Transform model value for view representation
        Override in subclasses for custom transformations

        Args:
            property_name: Name of the property
            model_value: Value from the model

        Returns:
            Transformed value for the view
        """
        return model_value

    def execute_command(self, command_name: str, *args, **kwargs) -> bool:
        """
        Execute a command

        Args:
            command_name: Name of the command to execute
            *args, **kwargs: Command arguments

        Returns:
            True if command executed successfully
        """
        if command_name in self._commands:
            try:
                result = self._commands[command_name](*args, **kwargs)
                self.command_executed.emit(command_name, True)
                logger.debug(f"Command '{command_name}' executed successfully")
                return True
            except Exception as e:
                logger.error(f"Command '{command_name}' failed: {e}")
                self.command_executed.emit(command_name, False)
                return False
        else:
            logger.warning(f"Command '{command_name}' not found")
            return False

    def register_command(self, name: str, command: Any) -> None:
        """
        Register a command

        Args:
            name: Command name
            command: Command function or callable
        """
        self._commands[name] = command
        logger.debug(f"Command '{name}' registered")


class BaseView(ABC):
    """
    Base class for views in MVVM pattern
    """

    def __init__(self, view_model: Optional[BaseViewModel] = None):
        self._view_model = view_model

        if self._view_model:
            self._bind_view_model()

    def set_view_model(self, view_model: BaseViewModel) -> None:
        """
        Set the view model for this view

        Args:
            view_model: The view model to bind to
        """
        if self._view_model:
            self._unbind_view_model()

        self._view_model = view_model
        if self._view_model:
            self._bind_view_model()

        logger.debug(f"View bound to view model: {type(view_model).__name__}")

    def get_view_model(self) -> Optional[BaseViewModel]:
        """
        Get the current view model

        Returns:
            The current view model or None
        """
        return self._view_model

    def _bind_view_model(self) -> None:
        """
        Bind to view model signals
        """
        if self._view_model:
            self._view_model.property_changed.connect(self.on_property_changed)
            self._view_model.command_executed.connect(self.on_command_executed)

    def _unbind_view_model(self) -> None:
        """
        Unbind from view model signals
        """
        if self._view_model:
            self._view_model.property_changed.disconnect(self.on_property_changed)
            self._view_model.command_executed.disconnect(self.on_command_executed)

    @abstractmethod
    def on_property_changed(self, property_name: str, new_value: Any) -> None:
        """
        Handle property changes from view model

        Args:
            property_name: Name of the changed property
            new_value: New value of the property
        """
        pass

    @abstractmethod
    def on_command_executed(self, command_name: str, success: bool) -> None:
        """
        Handle command execution results

        Args:
            command_name: Name of the executed command
            success: Whether the command succeeded
        """
        pass


class MVVMFactory:
    """
    Factory for creating MVVM components with dependency injection
    """

    def __init__(self, container):
        self.container = container

    def create_model(self, model_type: type) -> BaseModel:
        """
        Create a model instance

        Args:
            model_type: Type of model to create

        Returns:
            Created model instance
        """
        try:
            return self.container.resolve(model_type)
        except ValueError:
            # Fallback to direct instantiation
            return model_type()

    def create_view_model(
        self, view_model_type: type, model: Optional[BaseModel] = None
    ) -> BaseViewModel:
        """
        Create a view model instance

        Args:
            view_model_type: Type of view model to create
            model: Optional model to bind

        Returns:
            Created view model instance
        """
        try:
            view_model = self.container.resolve(view_model_type)
            if model:
                view_model.set_model(model)
            return view_model
        except ValueError:
            # Fallback to direct instantiation
            return view_model_type(model)
