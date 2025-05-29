from PyQt6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from utils.translation_manager import TranslationManager


class TabThreeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TabThreeContent")
        layout = QVBoxLayout(self)

        self.label = QLabel()
        self.label.setObjectName("TabThreeLabel")

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("TabThreeTextEdit")

        self.button = QPushButton()
        self.button.setObjectName("TabThreeButton")
        self.button.clicked.connect(self.on_button_click)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button)
        layout.addStretch()

        self.setLayout(layout)
        self.update_translations()

    def update_translations(self):
        translator = TranslationManager.get_translator()
        self.label.setText(translator.translate("app.tabs.content.tab3.content"))
        self.text_edit.setPlaceholderText(
            translator.translate("app.tabs.content.tab3.placeholder")
        )
        self.button.setText(translator.translate("app.tabs.content.tab3.show_text"))

    def on_button_click(self):
        text_content = self.text_edit.toPlainText()
        translator = TranslationManager.get_translator()
        if text_content:
            self.label.setText(
                translator.translate(
                    "app.tabs.content.tab3.text_content", text_content[:100]
                )
            )
        else:
            self.label.setText(
                translator.translate("app.tabs.content.tab3.empty_field")
            )
