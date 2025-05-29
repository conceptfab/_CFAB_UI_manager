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


class PreferencesDialog(QDialog):
    def __init__(self, preferences: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencje")
        self.setMinimumWidth(400)
        self.preferences = preferences

        layout = QVBoxLayout(self)

        # Grupa: Ogólne
        general_group = QGroupBox("Ogólne")
        general_layout = QFormLayout(general_group)

        self.splash_checkbox = QCheckBox("Pokazuj ekran powitalny (splash screen)")
        self.splash_checkbox.setChecked(preferences.get("show_splash", True))
        general_layout.addRow(self.splash_checkbox)

        self.remember_window_checkbox = QCheckBox("Zapamiętuj wielkość okna")
        self.remember_window_checkbox.setChecked(
            preferences.get("remember_window_size", True)
        )
        general_layout.addRow(self.remember_window_checkbox)

        layout.addWidget(general_group)

        # Grupa: Logowanie
        logging_group = QGroupBox("Logowanie")
        logging_layout = QFormLayout(logging_group)

        self.log_to_file_checkbox = QCheckBox("Zapisuj logi do pliku")
        self.log_to_file_checkbox.setChecked(preferences.get("log_to_file", False))
        logging_layout.addRow(self.log_to_file_checkbox)

        self.log_ui_console_checkbox = QCheckBox("Loguj komunikaty UI do konsoli")
        self.log_ui_console_checkbox.setChecked(
            preferences.get("log_ui_to_console", False)
        )
        logging_layout.addRow(self.log_ui_console_checkbox)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        current_level = preferences.get("log_level", "INFO")
        self.log_level_combo.setCurrentText(current_level)
        logging_layout.addRow("Poziom logowania:", self.log_level_combo)

        layout.addWidget(logging_group)

        # Przyciski
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Zapisz")
        self.cancel_btn = QPushButton("Anuluj")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_preferences(self):
        return {
            "show_splash": self.splash_checkbox.isChecked(),
            "remember_window_size": self.remember_window_checkbox.isChecked(),
            "log_to_file": self.log_to_file_checkbox.isChecked(),
            "log_ui_to_console": self.log_ui_console_checkbox.isChecked(),
            "log_level": self.log_level_combo.currentText(),
        }
