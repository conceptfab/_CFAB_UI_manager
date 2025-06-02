"""
Application action types enum

This module defines all the action types used in the application state management system.
Using these constants instead of string literals helps prevent typos and provides better IDE support.
"""

from enum import Enum, auto


class ActionType(str, Enum):
    """
    Enum for all application action types
    Inherits from str to maintain compatibility with existing code
    """

    # UI Actions
    SET_CURRENT_TAB = "SET_CURRENT_TAB"
    SET_WINDOW_MAXIMIZED = "SET_WINDOW_MAXIMIZED"
    SET_THEME = "SET_THEME"
    SET_LANGUAGE = "SET_LANGUAGE"

    # Hardware Actions
    SET_HARDWARE_PROFILE = "SET_HARDWARE_PROFILE"
    CLEAR_HARDWARE_PROFILE = "CLEAR_HARDWARE_PROFILE"

    # Application Actions
    SET_INITIALIZED = "SET_INITIALIZED"
    SET_LOADING = "SET_LOADING"
    ADD_ERROR = "ADD_ERROR"
    CLEAR_ERRORS = "CLEAR_ERRORS"

    # Preferences Actions
    UPDATE_PREFERENCES = "UPDATE_PREFERENCES"

    def __str__(self):
        """Return the string value of the enum"""
        return self.value
