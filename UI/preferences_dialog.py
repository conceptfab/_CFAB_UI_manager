from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from utils.translation_manager import TranslationManager


class PreferencesDialog(QDialog):
    def __init__(self, preferences: dict, parent=None):
        super().__init__(parent)
        self.preferences = preferences
        translator = TranslationManager.get_translator()
        self.setWindowTitle(translator.translate("app.dialogs.preferences.title"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Grupa: Ogólne
        general_group = QGroupBox(
            translator.translate("app.dialogs.preferences.general")
        )
        general_layout = QFormLayout(general_group)

        self.splash_checkbox = QCheckBox()
        self.splash_checkbox.setChecked(preferences.get("show_splash", True))
        general_layout.addRow(self.splash_checkbox)

        self.remember_window_checkbox = QCheckBox()
        self.remember_window_checkbox.setChecked(
            preferences.get("remember_window_size", True)
        )
        general_layout.addRow(self.remember_window_checkbox)

        # Dodajemy wybór języka
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Polski", "English"])
        current_language = preferences.get("language", "pl")
        lang_text = "Polski" if current_language == "pl" else "English"
        self.language_combo.setCurrentText(lang_text)
        general_layout.addRow(
            translator.translate("app.dialogs.preferences.language"),
            self.language_combo,
        )

        layout.addWidget(general_group)

        # Grupa: Logowanie
        logging_group = QGroupBox(
            translator.translate("app.dialogs.preferences.logging")
        )
        logging_layout = QFormLayout(logging_group)

        self.log_to_file_checkbox = QCheckBox()
        self.log_to_file_checkbox.setChecked(preferences.get("log_to_file", False))
        logging_layout.addRow(self.log_to_file_checkbox)

        self.log_ui_console_checkbox = QCheckBox()
        self.log_ui_console_checkbox.setChecked(
            preferences.get("log_ui_to_console", False)
        )
        logging_layout.addRow(self.log_ui_console_checkbox)

        self.log_level_combo = QComboBox()
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.log_level_combo.addItems(log_levels)
        current_level = preferences.get("log_level", "INFO")
        self.log_level_combo.setCurrentText(current_level)
        logging_layout.addRow(
            translator.translate("app.dialogs.preferences.log_level"),
            self.log_level_combo,
        )

        layout.addWidget(logging_group)

        # Przyciski
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton(
            translator.translate("app.dialogs.preferences.save")
        )
        self.cancel_btn = QPushButton(
            translator.translate("app.dialogs.preferences.cancel")
        )
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Rejestracja w TranslationManager
        TranslationManager.register_widget(self)
        self.update_translations()

    def update_translations(self):
        translator = TranslationManager.get_translator()
        self.setWindowTitle(translator.translate("app.dialogs.preferences.title"))

        # Grupa: Ogólne
        general_group = self.findChild(QGroupBox)
        general_group.setTitle(translator.translate("app.dialogs.preferences.general"))

        self.splash_checkbox.setText(
            translator.translate("app.dialogs.preferences.show_splash")
        )
        self.remember_window_checkbox.setText(
            translator.translate("app.dialogs.preferences.remember_window")
        )

        # Grupa: Logowanie
        logging_group = self.findChildren(QGroupBox)[1]
        logging_group.setTitle(translator.translate("app.dialogs.preferences.logging"))

        self.log_to_file_checkbox.setText(
            translator.translate("app.dialogs.preferences.log_to_file")
        )
        self.log_ui_console_checkbox.setText(
            translator.translate("app.dialogs.preferences.log_ui")
        )

        # Przyciski
        self.save_btn.setText(translator.translate("app.dialogs.preferences.save"))
        self.cancel_btn.setText(translator.translate("app.dialogs.preferences.cancel"))

    def get_preferences(self):
        language = "pl" if self.language_combo.currentText() == "Polski" else "en"
        return {
            "show_splash": self.splash_checkbox.isChecked(),
            "remember_window_size": self.remember_window_checkbox.isChecked(),
            "log_to_file": self.log_to_file_checkbox.isChecked(),
            "log_ui_to_console": self.log_ui_console_checkbox.isChecked(),
            "log_level": self.log_level_combo.currentText(),
            "language": language,
        }
