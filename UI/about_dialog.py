from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("O Programie")
        self.setFixedSize(400, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Logo/ikona aplikacji (opcjonalnie)
        # logo_label = QLabel()
        # logo_pixmap = QPixmap("resources/img/icon.png").scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio)
        # logo_label.setPixmap(logo_pixmap)
        # logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(logo_label)

        # Nazwa aplikacji
        title_label = QLabel("Moja Zaawansowana Aplikacja PyQt6")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Wersja
        version_label = QLabel("Wersja 1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # Opis
        description_label = QLabel(
            "Stworzona z użyciem PyQt6\n\nAplikacja demonstracyjna z zaawansowanymi funkcjami interfejsu użytkownika."
        )
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        layout.addStretch()

        # Przycisk OK
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
