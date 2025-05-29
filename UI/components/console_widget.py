import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget


class ConsoleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

        # Dodaj handler do loggera
        self.handler = ConsoleHandler(self)
        # Dodaj formatter do handlera
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.handler.setFormatter(formatter)
        logging.getLogger("AppLogger").addHandler(self.handler)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Konsola
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        # Przyciski
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Wyczyść")
        self.clear_btn.clicked.connect(self.clear_console)

        self.save_btn = QPushButton("Zapisz logi")
        self.save_btn.clicked.connect(self.save_logs)

        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def append_log(self, message):
        self.console.append(message)
        # Przewiń na dół
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )

    def clear_console(self):
        self.console.clear()

    def save_logs(self):
        from PyQt6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self, "Zapisz logi", "", "Pliki tekstowe (*.txt);;Wszystkie pliki (*.*)"
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.console.toPlainText())
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać logów: {e}")


class ConsoleHandler(logging.Handler):
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget

    def emit(self, record):
        msg = self.format(record)
        self.console_widget.append_log(msg)
