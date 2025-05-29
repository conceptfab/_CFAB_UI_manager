from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from utils.translation_manager import TranslationManager


class TabOneWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TabOneContent")
        layout = QVBoxLayout(self)

        self.label = QLabel()
        self.label.setObjectName("TabOneLabel")
        self.button = QPushButton()
        self.button.setObjectName("TabOneButton")
        self.line_edit = QLineEdit()
        self.line_edit.setObjectName("TabOneLineEdit")

        self.button.clicked.connect(self.on_button_click)

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button)
        layout.addStretch()

        self.setLayout(layout)
        self.update_translations()

    def update_translations(self):
        translator = TranslationManager.get_translator()
        self.label.setText(translator.translate("app.tabs.content.tab1.content"))
        self.button.setText(translator.translate("app.tabs.content.tab1.button"))
        self.line_edit.setPlaceholderText(
            translator.translate("app.tabs.content.tab1.placeholder")
        )

    def on_button_click(self):
        text = self.line_edit.text()
        translator = TranslationManager.get_translator()
        if text:
            self.label.setText(
                translator.translate("app.tabs.content.tab1.text_entered", text)
            )
        else:
            self.label.setText(
                translator.translate("app.tabs.content.tab1.nothing_entered")
            )
