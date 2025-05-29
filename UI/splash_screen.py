from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QProgressBar, QSplashScreen


class SplashScreen(QSplashScreen):
    def __init__(
        self,
        image_path: str,
        display_time: int = 3000,
        window_size: tuple = (642, 250),
        messages: list = None,
        progress_bar: bool = False,
    ):
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(*window_size, Qt.AspectRatioMode.KeepAspectRatio)
        super().__init__(pixmap)
        self.setFixedSize(*window_size)
        self.display_time = display_time
        self.messages = messages or []
        self.current_message_index = 0
        self.progress_bar_enabled = progress_bar

        # Etykieta na wiadomości
        self.message_label = QLabel(self)
        self.message_label.setGeometry(10, window_size[1] - 25, window_size[0] - 20, 30)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet(
            "color: white; font-size: 11px; font-weight: bold;"
        )
        self.message_label.setText(self.messages[0] if self.messages else "")

        # Pasek postępu (opcjonalny)
        self.progress = None
        if progress_bar:
            self.progress = QProgressBar(self)
            self.progress.setGeometry(10, window_size[1] - 30, window_size[0] - 20, 20)
            self.progress.setMaximum(100)
            self.progress.setValue(0)
            self.progress.show()
        else:
            self.progress = None

        # Timer do zmiany wiadomości
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_message)

    def start(self):
        self.show()
        if self.messages:
            self.timer.start(self.display_time // max(1, len(self.messages)))
        else:
            QTimer.singleShot(self.display_time, self.close)

    def update_message(self):
        if self.current_message_index < len(self.messages):
            self.message_label.setText(self.messages[self.current_message_index])
            self.current_message_index += 1
        else:
            self.timer.stop()
            self.close()

    def set_progress(self, value: int):
        if self.progress:
            self.progress.setValue(value)

    def show_progress(self):
        if self.progress:
            self.progress.show()

    def hide_progress(self):
        if self.progress:
            self.progress.hide()
