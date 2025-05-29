import logging
import sys
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


class ConsoleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConsoleWidget")
        self.init_ui()

        # Konfiguracja loggera
        self.handler = ConsoleHandler(self)
        formatter = logging.Formatter("%(message)s")
        self.handler.setFormatter(formatter)
        logging.getLogger("AppLogger").addHandler(self.handler)

        # Przechwytywanie stdout i stderr
        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

        # Rejestracja w TranslationManager
        TranslationManager.register_widget(self)
        self.update_translations()

    def write(self, text):
        """Przechwytuje wyjście z print() i przekierowuje do konsoli"""
        self.old_stdout.write(text)  # Zachowujemy oryginalne wyjście
        if text.strip():  # Ignorujemy puste linie
            self.append_log(text.strip())

    def flush(self):
        """Wymagane dla sys.stdout"""
        self.old_stdout.flush()

    def closeEvent(self, event):
        """Przywraca oryginalne stdout i stderr przy zamknięciu"""
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
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
