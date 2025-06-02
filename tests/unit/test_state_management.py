"""
Tests for the state management module
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from architecture.action_types import ActionType
from architecture.state_management import (
    Action,
    ActionDispatcher,
    Store,
    get_store,
    reset_store,
    set_current_tab,
    set_language,
    with_immutable_state,
)


class ActionTest(unittest.TestCase):
    """Test the Action class"""

    def test_action_creation(self):
        """Should create action with proper fields"""
        action = Action(ActionType.SET_CURRENT_TAB, 2)
        self.assertEqual(ActionType.SET_CURRENT_TAB, action.type)
        self.assertEqual(2, action.payload)
        self.assertIsNotNone(action.timestamp)

    def test_action_repr(self):
        """Should provide a useful string representation"""
        action = Action(ActionType.SET_LANGUAGE, "en")
        repr_str = repr(action)
        self.assertIn("SET_LANGUAGE", repr_str)
        self.assertIn("en", repr_str)


class WithImmutableStateTest(unittest.TestCase):
    """Test the with_immutable_state decorator"""

    def test_state_immutability(self):
        """Should ensure state is not modified in place"""

        # Define a reducer that tries to modify state directly
        @with_immutable_state
        def test_reducer(state, action):
            state["test"] = "modified"
            return state

        # Create original state
        original_state = {"test": "original"}

        # Apply reducer
        action = Action(ActionType.SET_LANGUAGE, "en")
        new_state = test_reducer(original_state, action)

        # Original should be untouched
        self.assertEqual("original", original_state["test"])
        # New state should be modified
        self.assertEqual("modified", new_state["test"])


class ActionDispatcherTest(unittest.TestCase):
    """Test the ActionDispatcher class"""

    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_register_reducer(self):
        """Should register reducer functions"""
        mock_reducer = MagicMock(return_value={})
        mock_reducer.__name__ = "mock_reducer"

        self.dispatcher.register_reducer(mock_reducer)
        self.assertIn(mock_reducer, self.dispatcher._reducers)

    def test_dispatch_with_reducers(self):
        """Should apply reducers when dispatching actions"""

        # Create a simple reducer that modifies state
        def test_reducer(state, action):
            if action.type == ActionType.SET_CURRENT_TAB:
                new_state = state.copy()
                new_state["tab"] = action.payload
                return new_state
            return state

        # Register reducer
        self.dispatcher.register_reducer(test_reducer)

        # Dispatch action
        self.dispatcher._current_state = {"tab": 0}
        self.dispatcher.dispatch(ActionType.SET_CURRENT_TAB, 2)

        # Check state was updated
        self.assertEqual(2, self.dispatcher._current_state["tab"])

    def test_subscriber_notification(self):
        """Should notify subscribers when state changes"""
        # Create a mock subscriber
        mock_subscriber = MagicMock()
        mock_subscriber.__name__ = "mock_subscriber"

        # Register subscriber
        self.dispatcher.subscribe(mock_subscriber)

        # Create a simple reducer
        def test_reducer(state, action):
            if action.type == ActionType.SET_LANGUAGE:
                new_state = state.copy()
                new_state["language"] = action.payload
                return new_state
            return state

        # Register reducer
        self.dispatcher.register_reducer(test_reducer)

        # Dispatch action that changes state
        self.dispatcher._current_state = {"language": "pl"}
        self.dispatcher.dispatch(ActionType.SET_LANGUAGE, "en")

        # Check subscriber was called with new state
        mock_subscriber.assert_called_once()
        call_arg = mock_subscriber.call_args[0][0]
        self.assertEqual("en", call_arg["language"])

    def test_middleware_chain(self):
        """Should apply middleware in a chain"""

        # Create middleware functions
        def middleware1(action, next_fn):
            action.payload = f"{action.payload}_m1"
            return next_fn(action)

        middleware1.__name__ = "middleware1"

        def middleware2(action, next_fn):
            action.payload = f"{action.payload}_m2"
            return next_fn(action)

        middleware2.__name__ = "middleware2"

        # Register middleware
        self.dispatcher.register_middleware(middleware1)
        self.dispatcher.register_middleware(middleware2)

        # Create mock reducer
        mock_reducer = MagicMock(return_value={})
        mock_reducer.__name__ = "mock_reducer"
        self.dispatcher.register_reducer(mock_reducer)

        # Dispatch action
        self.dispatcher.dispatch(ActionType.SET_LANGUAGE, "en")

        # Check middleware chain was applied correctly
        called_action = mock_reducer.call_args[0][1]
        self.assertEqual("en_m1_m2", called_action.payload)


class StoreTest(unittest.TestCase):
    """Test the Store class"""

    def setUp(self):
        reset_store()  # Ensure we start fresh

    def test_store_initialization(self):
        """Should initialize with default state"""
        store = get_store()
        state = store.get_state()

        # Check some expected keys in the state
        self.assertIn("ui", state)
        self.assertIn("hardware", state)
        self.assertIn("application", state)
        self.assertIn("preferences", state)

    def test_ui_reducer(self):
        """Should update UI state correctly"""
        store = Store()

        # Test tab change
        store.dispatch(ActionType.SET_CURRENT_TAB, 2)
        self.assertEqual(2, store.get_state()["ui"]["current_tab"])

        # Test language change
        store.dispatch(ActionType.SET_LANGUAGE, "en")
        self.assertEqual("en", store.get_state()["ui"]["language"])

    def test_convenience_functions(self):
        """Should use convenience functions to update state"""
        reset_store()

        # Use convenience functions
        set_current_tab(3)
        set_language("de")

        # Check state was updated
        state = get_store().get_state()
        self.assertEqual(3, state["ui"]["current_tab"])
        self.assertEqual("de", state["ui"]["language"])


if __name__ == "__main__":
    unittest.main()
