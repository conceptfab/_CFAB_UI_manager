from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from utils.translation_manager import TranslationManager


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(TranslationManager.translate("app.dialogs.about.title"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Logo/ikona aplikacji (opcjonalnie)
        # logo_label = QLabel()
        # logo_pixmap = QPixmap("resources/img/icon.png").scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio)
        # logo_label.setPixmap(logo_pixmap)
        # logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(logo_label)

        # Nazwa aplikacji
        self.title_label = QLabel(
            TranslationManager.translate("app.dialogs.about.title")
        )
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Wersja
        self.version_label = QLabel(
            TranslationManager.translate("app.dialogs.about.version")
        )
        layout.addWidget(self.version_label)

        # Opis
        self.description_label = QLabel(
            TranslationManager.translate("app.dialogs.about.description")
        )
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        layout.addStretch()

        # Przycisk OK
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton(
            TranslationManager.translate("app.dialogs.about.ok")
        )
        self.ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Rejestracja w TranslationManager
        TranslationManager.register_widget(self)
        self.update_translations()

    def update_translations(self):
        self.setWindowTitle(TranslationManager.translate("app.dialogs.about.title"))
        self.title_label.setText(
            TranslationManager.translate("app.dialogs.about.title")
        )
        self.version_label.setText(
            TranslationManager.translate("app.dialogs.about.version")
        )
        self.description_label.setText(
            TranslationManager.translate("app.dialogs.about.description")
        )
        self.ok_button.setText(TranslationManager.translate("app.dialogs.about.ok"))
