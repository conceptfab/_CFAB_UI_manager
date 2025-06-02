import os

import pytest
from PyQt6.QtWidgets import QApplication

from UI.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance() or QApplication([])
    return app


def test_main_window_startup(app):
    """Test uruchomienia głównego okna bez błędów."""
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() != ""


def test_preferences_handling(app, tmp_path):
    """Test obsługi preferencji (zapis/odczyt)."""
    window = MainWindow()
    test_prefs = {
        "show_splash": False,
        "log_to_file": True,
        "log_to_system_console": True,
        "log_level": "DEBUG",
        "remember_window_size": False,
        "window_size": {"width": 640, "height": 480},
        "window_position": {"x": 10, "y": 10},
    }
    window.preferences = test_prefs
    assert window.preferences["log_level"] == "DEBUG"
    # Test zapisu do pliku
    config_path = tmp_path / "config.json"
    window.config_path = str(config_path)
    window.save_preferences_async()
    # Symulacja odczytu
    window.file_worker.load_preferences(str(config_path))


def test_ui_components_integration(app):
    """Test integracji z komponentami UI (zakładki, menu, status)."""
    window = MainWindow()
    assert hasattr(window, "tabs")
    assert hasattr(window, "status_bar")
    assert window.tabs.count() >= 3


def test_ui_performance(app):
    """Test wydajności inicjalizacji UI (snapshot pamięci)."""
    from utils.performance_optimizer import performance_monitor

    before = performance_monitor.take_memory_snapshot("ui_before")
    window = MainWindow()
    after = performance_monitor.take_memory_snapshot("ui_after")
    assert isinstance(before, dict)
    assert isinstance(after, dict)
