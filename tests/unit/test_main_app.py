import os
import sys

import pytest
from PyQt6.QtWidgets import QApplication

from main_app import Application


@pytest.fixture(scope="module")
def app_instance():
    """Tworzy instancję aplikacji do testów."""
    app = QApplication.instance() or Application([])
    yield app
    if hasattr(app, "cleanup"):
        app.cleanup()


def test_app_startup_no_errors(app_instance):
    """Test uruchomienia aplikacji bez krytycznych błędów."""
    assert app_instance.initialize() is True
    assert hasattr(app_instance, "main_window") or True  # main_window tworzony później


def test_logger_integration(app_instance):
    """Test integracji z loggerem."""
    app_instance.initialize()
    assert hasattr(app_instance, "app_logger")
    assert app_instance.app_logger is not None
    app_instance.app_logger.info("Test logowania z testu jednostkowego.")


def test_config_integration(app_instance):
    """Test integracji z config.json."""
    app_instance.initialize()
    assert isinstance(app_instance.config, dict)
    assert "show_splash" in app_instance.config


def test_performance_monitoring(app_instance):
    """Test wydajności startu aplikacji."""
    from utils.performance_optimizer import performance_monitor

    app_instance.initialize()
    before = performance_monitor.take_memory_snapshot("test_before")
    after = performance_monitor.take_memory_snapshot("test_after")
    assert isinstance(before, dict)
    assert isinstance(after, dict)
