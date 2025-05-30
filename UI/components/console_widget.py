import logging
import sys
import weakref
from io import StringIO

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.translation_manager import TranslationManager


class SafeStdoutRedirector:
    """
    Bezpieczniejsze przechwytywanie stdout który nie powoduje problemów z innymi komponentami
    """

    def __init__(self, console_widget):
        self.console_widget = weakref.ref(console_widget)
        self.original_stdout = sys.stdout

    def write(self, text):
        """Przechwytuje wyjście z print() i przekierowuje do konsoli"""
        self.original_stdout.write(text)  # Zachowujemy oryginalne wyjście
        widget = self.console_widget()
        if widget and text.strip():  # Sprawdź czy widget jeszcze istnieje
            widget.append_log(text.strip())

    def flush(self):
        """Wymagane dla sys.stdout"""
        self.original_stdout.flush()

    def restore(self):
        """Przywraca oryginalne stdout"""
        sys.stdout = self.original_stdout


class ConsoleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConsoleWidget")
        self.init_ui()

        # Konfiguracja loggera - bezpieczniej
        self.handler = ConsoleHandler(self)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.handler.setFormatter(formatter)

        # Dodaj handler do root loggera
        root_logger = logging.getLogger()
        root_logger.addHandler(self.handler)

        # Ustaw poziom logowania z konfiguracji
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        # Pobierz poziom logowania z konfiguracji
        config = TranslationManager.get_config()
        log_level = level_map.get(config.get("log_level", "INFO"), logging.INFO)
        root_logger.setLevel(log_level)

        # Dodaj też do specific logger
        app_logger = logging.getLogger("AppLogger")
        app_logger.addHandler(self.handler)
        app_logger.setLevel(log_level)

        # Bezpieczniejsze przechwytywanie stdout (włączone domyślnie)
        self.stdout_redirector = None
        self.redirect_stdout = True  # Włączamy domyślnie

        if self.redirect_stdout:
            self.stdout_redirector = SafeStdoutRedirector(self)
            sys.stdout = self.stdout_redirector

        # Rejestracja w TranslationManager
        TranslationManager.register_widget(self)
        self.update_translations()

        logging.getLogger("AppLogger").info("Console widget initialized")

    def closeEvent(self, event):
        """Przywraca oryginalne stdout przy zamknięciu"""
        if self.stdout_redirector:
            self.stdout_redirector.restore()

        # Usuń handler z loggera
        app_logger = logging.getLogger("AppLogger")
        app_logger.removeHandler(self.handler)

        super().closeEvent(event)

    def init_ui(self):
        translator = TranslationManager.get_translator()
        layout = QVBoxLayout(self)

        # Konsola
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("ConsoleTextEdit")
        self.console.setPlaceholderText(
            translator.translate("app.tabs.console.placeholder")
        )
        layout.addWidget(self.console)

        # Przyciski
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton(translator.translate("app.tabs.console.clear"))
        self.clear_btn.clicked.connect(self.clear_console)

        self.save_btn = QPushButton(translator.translate("app.tabs.console.save_logs"))
        self.save_btn.clicked.connect(self.save_logs)

        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def update_translations(self):
        translator = TranslationManager.get_translator()
        self.console.setPlaceholderText(
            translator.translate("app.tabs.console.placeholder")
        )
        self.clear_btn.setText(translator.translate("app.tabs.console.clear"))
        self.save_btn.setText(translator.translate("app.tabs.console.save_logs"))

    def append_log(self, message):
        self.console.append(message)
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )

    def clear_console(self):
        self.console.clear()

    def save_logs(self):
        translator = TranslationManager.get_translator()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            translator.translate("app.tabs.console.save_logs_title"),
            "",
            translator.translate("app.tabs.console.file_filters"),
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.console.toPlainText())
            except Exception as e:
                QMessageBox.critical(
                    self,
                    translator.translate("app.tabs.console.error"),
                    translator.translate("app.tabs.console.save_error").format(str(e)),
                )


class ConsoleHandler(logging.Handler):
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget

    def emit(self, record):
        msg = self.format(record)
        self.console_widget.append_log(msg)
