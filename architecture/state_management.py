# Application State Management
# Centralized state management with Flux/Redux-like pattern

import logging
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Union

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class Action:
    """
    Represents an action that can modify application state
    """

    def __init__(self, action_type: str, payload: Any = None):
        self.type = action_type
        self.payload = payload
        self.timestamp = None  # Will be set by dispatcher

    def __repr__(self):
        return f"Action(type='{self.type}', payload={self.payload})"


class ActionDispatcher(QObject):
    """
    Dispatches actions to reducers and notifies subscribers
    """

    # Signal emitted when an action is dispatched
    action_dispatched = pyqtSignal(Action)

    def __init__(self):
        super().__init__()
        self._reducers: List[Callable] = []
        self._middleware: List[Callable] = []
        self._subscribers: List[Callable] = []
        self._current_state: Dict[str, Any] = {}
        self._action_history: List[Action] = []
        self._max_history = 100

    def register_reducer(self, reducer: Callable) -> None:
        """
        Register a reducer function

        Args:
            reducer: Function that takes (state, action) and returns new state
        """
        self._reducers.append(reducer)
        logger.debug(f"Reducer registered: {reducer.__name__}")

    def register_middleware(self, middleware: Callable) -> None:
        """
        Register middleware function

        Args:
            middleware: Function that takes (action, next) and can modify or block actions
        """
        self._middleware.append(middleware)
        logger.debug(f"Middleware registered: {middleware.__name__}")

    def subscribe(self, subscriber: Callable) -> None:
        """
        Subscribe to state changes

        Args:
            subscriber: Function called when state changes
        """
        self._subscribers.append(subscriber)
        logger.debug(f"Subscriber registered: {subscriber.__name__}")

    def unsubscribe(self, subscriber: Callable) -> bool:
        """
        Unsubscribe from state changes

        Args:
            subscriber: Function to remove from subscribers

        Returns:
            True if subscriber was found and removed
        """
        try:
            self._subscribers.remove(subscriber)
            logger.debug(f"Subscriber removed: {subscriber.__name__}")
            return True
        except ValueError:
            return False

    def dispatch(self, action: Union[Action, str], payload: Any = None) -> None:
        """
        Dispatch an action

        Args:
            action: Action object or action type string
            payload: Payload if action is a string
        """
        if isinstance(action, str):
            action = Action(action, payload)

        # Add to history
        self._action_history.append(action)
        if len(self._action_history) > self._max_history:
            self._action_history.pop(0)

        # Apply middleware
        processed_action = self._apply_middleware(action)
        if processed_action is None:
            return  # Action was blocked by middleware

        # Apply reducers
        old_state = deepcopy(self._current_state)
        for reducer in self._reducers:
            try:
                self._current_state = reducer(self._current_state, processed_action)
            except Exception as e:
                logger.error(f"Reducer {reducer.__name__} failed: {e}")

        # Notify subscribers if state changed
        if self._current_state != old_state:
            self._notify_subscribers()

        # Emit signal
        self.action_dispatched.emit(processed_action)

        logger.debug(f"Action dispatched: {processed_action}")

    def _apply_middleware(self, action: Action) -> Optional[Action]:
        """
        Apply middleware to action

        Args:
            action: Action to process

        Returns:
            Processed action or None if blocked
        """
        current_action = action

        for middleware in self._middleware:
            try:
                result = middleware(current_action, lambda a: a)
                if result is None:
                    return None  # Action blocked
                current_action = result
            except Exception as e:
                logger.error(f"Middleware {middleware.__name__} failed: {e}")

        return current_action

    def _notify_subscribers(self) -> None:
        """
        Notify all subscribers of state change
        """
        for subscriber in self._subscribers:
            try:
                subscriber(self._current_state)
            except Exception as e:
                logger.error(f"Subscriber {subscriber.__name__} failed: {e}")

    def get_state(self) -> Dict[str, Any]:
        """
        Get current application state

        Returns:
            Copy of current state
        """
        return deepcopy(self._current_state)

    def get_action_history(self) -> List[Action]:
        """
        Get action history

        Returns:
            List of recent actions
        """
        return self._action_history.copy()


class Store:
    """
    Main application store that manages state
    """

    def __init__(self):
        self._dispatcher = ActionDispatcher()
        self._initial_state = self._create_initial_state()
        self._dispatcher._current_state = deepcopy(self._initial_state)

        # Register built-in reducers
        self._register_built_in_reducers()

        logger.info("Application store initialized")

    def _create_initial_state(self) -> Dict[str, Any]:
        """
        Create the initial application state

        Returns:
            Initial state dictionary
        """
        return {
            "ui": {
                "current_tab": 0,
                "window_maximized": False,
                "theme": "default",
                "language": "pl",
            },
            "hardware": {
                "profile_loaded": False,
                "gpu_info": "",
                "cpu_info": "",
                "memory_total": 0,
            },
            "application": {"initialized": False, "loading": False, "errors": []},
            "preferences": {
                "auto_save": True,
                "check_updates": True,
                "show_notifications": True,
            },
        }

    def _register_built_in_reducers(self) -> None:
        """
        Register built-in reducers for common state changes
        """
        self._dispatcher.register_reducer(self._ui_reducer)
        self._dispatcher.register_reducer(self._hardware_reducer)
        self._dispatcher.register_reducer(self._application_reducer)
        self._dispatcher.register_reducer(self._preferences_reducer)

    def _ui_reducer(self, state: Dict[str, Any], action: Action) -> Dict[str, Any]:
        """
        Reducer for UI-related actions
        """
        new_state = deepcopy(state)

        if action.type == "SET_CURRENT_TAB":
            new_state["ui"]["current_tab"] = action.payload
        elif action.type == "SET_WINDOW_MAXIMIZED":
            new_state["ui"]["window_maximized"] = action.payload
        elif action.type == "SET_THEME":
            new_state["ui"]["theme"] = action.payload
        elif action.type == "SET_LANGUAGE":
            new_state["ui"]["language"] = action.payload

        return new_state

    def _hardware_reducer(
        self, state: Dict[str, Any], action: Action
    ) -> Dict[str, Any]:
        """
        Reducer for hardware-related actions
        """
        new_state = deepcopy(state)

        if action.type == "SET_HARDWARE_PROFILE":
            new_state["hardware"].update(action.payload)
            new_state["hardware"]["profile_loaded"] = True
        elif action.type == "CLEAR_HARDWARE_PROFILE":
            new_state["hardware"] = {
                "profile_loaded": False,
                "gpu_info": "",
                "cpu_info": "",
                "memory_total": 0,
            }

        return new_state

    def _application_reducer(
        self, state: Dict[str, Any], action: Action
    ) -> Dict[str, Any]:
        """
        Reducer for application-related actions
        """
        new_state = deepcopy(state)

        if action.type == "SET_INITIALIZED":
            new_state["application"]["initialized"] = action.payload
        elif action.type == "SET_LOADING":
            new_state["application"]["loading"] = action.payload
        elif action.type == "ADD_ERROR":
            new_state["application"]["errors"].append(action.payload)
        elif action.type == "CLEAR_ERRORS":
            new_state["application"]["errors"] = []

        return new_state

    def _preferences_reducer(
        self, state: Dict[str, Any], action: Action
    ) -> Dict[str, Any]:
        """
        Reducer for preferences-related actions
        """
        new_state = deepcopy(state)

        if action.type == "UPDATE_PREFERENCES":
            new_state["preferences"].update(action.payload)

        return new_state

    def dispatch(self, action: Union[Action, str], payload: Any = None) -> None:
        """
        Dispatch an action to the store

        Args:
            action: Action object or action type string
            payload: Payload if action is a string
        """
        self._dispatcher.dispatch(action, payload)

    def subscribe(self, subscriber: Callable) -> None:
        """
        Subscribe to state changes

        Args:
            subscriber: Function called when state changes
        """
        self._dispatcher.subscribe(subscriber)

    def unsubscribe(self, subscriber: Callable) -> bool:
        """
        Unsubscribe from state changes

        Args:
            subscriber: Function to remove from subscribers

        Returns:
            True if subscriber was found and removed
        """
        return self._dispatcher.unsubscribe(subscriber)

    def get_state(self) -> Dict[str, Any]:
        """
        Get current application state

        Returns:
            Copy of current state
        """
        return self._dispatcher.get_state()

    def register_reducer(self, reducer: Callable) -> None:
        """
        Register a custom reducer

        Args:
            reducer: Function that takes (state, action) and returns new state
        """
        self._dispatcher.register_reducer(reducer)

    def register_middleware(self, middleware: Callable) -> None:
        """
        Register middleware

        Args:
            middleware: Function that takes (action, next) and can modify or block actions
        """
        self._dispatcher.register_middleware(middleware)


# Global store instance
_store = None


def get_store() -> Store:
    """
    Get the global application store

    Returns:
        The global store instance
    """
    global _store
    if _store is None:
        _store = Store()
    return _store


def reset_store() -> None:
    """
    Reset the global store (mainly for testing)
    """
    global _store
    _store = None


# Convenience functions for common actions
def set_current_tab(tab_index: int) -> None:
    """Set the current active tab"""
    get_store().dispatch("SET_CURRENT_TAB", tab_index)


def set_language(language: str) -> None:
    """Set the application language"""
    get_store().dispatch("SET_LANGUAGE", language)


def set_hardware_profile(profile: Dict[str, Any]) -> None:
    """Set the hardware profile"""
    get_store().dispatch("SET_HARDWARE_PROFILE", profile)


def set_loading(loading: bool) -> None:
    """Set the application loading state"""
    get_store().dispatch("SET_LOADING", loading)


def add_error(error: str) -> None:
    """Add an error to the application state"""
    get_store().dispatch("ADD_ERROR", error)
