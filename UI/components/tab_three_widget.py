from PyQt6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from utils.translation_manager import TranslationManager


class TabThreeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TabThreeContent")
        layout = QVBoxLayout(self)

        self.label = QLabel(
            TranslationManager.translate("app.tabs.content.tab3.content")
        )
        self.label.setObjectName("TabThreeLabel")

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("TabThreeTextEdit")
        self.text_edit.setPlaceholderText(
            TranslationManager.translate("app.tabs.content.tab3.placeholder")
        )

        self.button = QPushButton(
            TranslationManager.translate("app.tabs.content.tab3.show_text")
        )
        self.button.setObjectName("TabThreeButton")
        self.button.clicked.connect(self.on_button_click)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button)
        layout.addStretch()

        self.setLayout(layout)
        TranslationManager.register_widget(self)

    def update_translations(self):
        self.label.setText(
            TranslationManager.translate("app.tabs.content.tab3.content")
        )
        self.text_edit.setPlaceholderText(
            TranslationManager.translate("app.tabs.content.tab3.placeholder")
        )
        self.button.setText(
            TranslationManager.translate("app.tabs.content.tab3.show_text")
        )

    def on_button_click(self):
        text_content = self.text_edit.toPlainText()
        if text_content:
            self.label.setText(
                TranslationManager.translate(
                    "app.tabs.content.tab3.text_content", text_content[:100]
                )
            )
        else:
            self.label.setText(
                TranslationManager.translate("app.tabs.content.tab3.empty_field")
            )
