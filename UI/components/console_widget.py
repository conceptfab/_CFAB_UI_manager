import logging
import sys
import weakref
from io import StringIO

from PyQt6.QtGui import QTextCursor
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
    MAX_BLOCK_COUNT = 1000  # Maksymalna liczba bloków tekstu
    MAX_LINE_COUNT_PER_BLOCK = 50  # Maksymalna liczba linii w bloku

    def __init__(self, parent=None, app_logger=None):  # Dodano app_logger
        super().__init__(parent)
        self.setObjectName("ConsoleWidget")
        self._buffer = []  # Bufor na logi
        self._current_block_line_count = 0
        self.app_logger = app_logger  # Zapisz referencję do AppLogger
        self.init_ui()

        # Konfiguracja loggera - użyj przekazanego app_logger lub globalnego
        # Usunięto tworzenie własnego ConsoleHandler i dodawanie go do root loggera
        # Logi będą teraz przekazywane przez AppLogger

        # Bezpieczniejsze przechwytywanie stdout (włączone domyślnie)
        self.stdout_redirector = None
        self.redirect_stdout = True  # Włączamy domyślnie

        if self.redirect_stdout:
            self.stdout_redirector = SafeStdoutRedirector(self)
            sys.stdout = self.stdout_redirector

        # Rejestracja w TranslationManager
        TranslationManager.register_widget(self)
        self.update_translations()

        # Timer do regularnego flush bufora (co 2 sekundy)
        from PyQt6.QtCore import QTimer

        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush_buffer_to_console)
        self._flush_timer.start(2000)  # 2000 ms = 2 sekundy

        logging.getLogger("AppLogger").info(
            TranslationManager.translate("app.tabs.console.status.initialized")
        )

    def closeEvent(self, event):
        """Przywraca oryginalne stdout przy zamknięciu"""
        if self.stdout_redirector:
            self.stdout_redirector.restore()

        # Zatrzymaj timer flush bufora
        if hasattr(self, "_flush_timer") and self._flush_timer:
            self._flush_timer.stop()

        super().closeEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Konsola
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("ConsoleTextEdit")
        self.console.setPlaceholderText(
            TranslationManager.translate("app.tabs.console.placeholder")
        )
        layout.addWidget(self.console)

        # Przyciski
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton(
            TranslationManager.translate("app.tabs.console.clear")
        )
        self.clear_btn.clicked.connect(self.clear_console)

        self.save_btn = QPushButton(
            TranslationManager.translate("app.tabs.console.save_logs")
        )
        self.save_btn.clicked.connect(self.save_logs)

        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def update_translations(self):
        self.console.setPlaceholderText(
            TranslationManager.translate("app.tabs.console.placeholder")
        )
        self.clear_btn.setText(TranslationManager.translate("app.tabs.console.clear"))
        self.save_btn.setText(
            TranslationManager.translate("app.tabs.console.save_logs")
        )

    def append_log(self, message):
        # Optymalizacja: Dodawaj do bufora, aktualizuj QTextEdit rzadziej
        self._buffer.append(message)
        self._current_block_line_count += message.count("\n") + 1

        # Jeśli bufor przekroczył limit lub zawiera logilany blok tekstu, opróżnij go
        if (
            self._current_block_line_count >= self.MAX_LINE_COUNT_PER_BLOCK
            or len(self._buffer)
            > 5  # Zmniejszono próg z 20 na 5, aby częściej odświeżać
        ):
            self._flush_buffer_to_console()
        # Dla ważnych logów (np. zawierających ERROR lub WARNING), flush natychmiast
        elif any(
            important in message.upper() for important in ["ERROR", "WARN", "CRITICAL"]
        ):
            self._flush_buffer_to_console()

    def _flush_buffer_to_console(self):
        if not self._buffer:
            return

        full_text = "\n".join(self._buffer)
        self._buffer.clear()
        self._current_block_line_count = 0

        # Zarządzanie rozmiarem konsoli
        doc = self.console.document()
        if doc.blockCount() > self.MAX_BLOCK_COUNT:
            # Usuń najstarsze bloki, aby nie przekroczyć limitu
            cursor = self.console.textCursor()  # Użyj self.console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            # Usuń około 10% najstarszych bloków
            blocks_to_remove = doc.blockCount() - int(self.MAX_BLOCK_COUNT * 0.9)
            for _ in range(blocks_to_remove):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                if cursor.atEnd():  # Dodatkowe zabezpieczenie
                    break
            # Upewnij się, że kursor jest na końcu po usunięciu
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.console.setTextCursor(cursor)

        self.console.append(full_text)  # Dodaj nowy tekst

        # Optymalizacja przewijania: Przewijaj tylko jeśli użytkownik nie przewinął ręcznie
        scrollbar = self.console.verticalScrollBar()
        # Sprawdź, czy scrollbar jest blisko końca lub na końcu
        is_at_bottom = scrollbar.value() >= (scrollbar.maximum() - 10)  # Mały margines
        if is_at_bottom or scrollbar.maximum() == 0:
            scrollbar.setValue(scrollbar.maximum())

    def clear_console(self):
        self.console.clear()
        self._buffer.clear()
        self._current_block_line_count = 0

    def save_logs(self):
        # Najpierw opróżnij bufor, aby zapisać wszystkie logi
        self._flush_buffer_to_console()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            TranslationManager.translate("app.tabs.console.save_logs_title"),
            "",
            TranslationManager.translate("app.tabs.console.file_filters"),
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.console.toPlainText())
            except Exception as e:
                QMessageBox.critical(
                    self,
                    TranslationManager.translate("app.tabs.console.error"),
                    TranslationManager.translate("app.tabs.console.save_error").format(
                        str(e)
                    ),
                )
