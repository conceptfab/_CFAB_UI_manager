from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout

class PreferencesDialog(QDialog):
    def __init__(self, show_splash: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencje")
        self.setMinimumWidth(300)
        self.result = None

        layout = QVBoxLayout(self)
        self.splash_checkbox = QCheckBox("Pokazuj ekran powitalny (splash screen)")
        self.splash_checkbox.setChecked(show_splash)
        layout.addWidget(self.splash_checkbox)

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
            "show_splash": self.splash_checkbox.isChecked()
        } 