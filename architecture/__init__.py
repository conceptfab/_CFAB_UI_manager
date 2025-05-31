# Architecture module for MVVM pattern and dependency injection

from .config_management import ConfigManager
from .dependency_injection import (
    ServiceContainer,
    configure_dependencies,
    get_container,
    inject,
)
from .mvvm import BaseModel, BaseView, BaseViewModel, MVVMFactory
from .state_management import (
    Action,
    ActionDispatcher,
    Store,
    add_error,
    get_store,
    reset_store,
    set_current_tab,
    set_hardware_profile,
    set_language,
    set_loading,
)

__all__ = [
    # Dependency Injection
    "DependencyContainer",
    "configure_dependencies",
    "get_container",
    "inject",
    # MVVM
    "BaseModel",
    "BaseView",
    "BaseViewModel",
    "MVVMFactory",
    # State Management
    "Action",
    "ActionDispatcher",
    "Store",
    "get_store",
    "reset_store",
    "set_current_tab",
    "set_language",
    "set_hardware_profile",
    "set_loading",
    "add_error",
    # Configuration Management
    "AdvancedConfigManager",
    "ConfigTransaction",
    "ConfigBackup",
    "create_config_manager",
]
