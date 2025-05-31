from PyQt6.QtWidgets import QLabel, QPushButton, QTextEdit

from utils.translation_manager import TranslationManager

from .base_tab_widget import BaseTabWidget


class TabThreeWidget(BaseTabWidget):
    def __init__(self):
        super().__init__(object_name="TabThreeContent")

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

        # Use the layout from BaseTabWidget
        self._add_widgets_to_layout([self.label, self.text_edit, self.button])

    def update_translations(self):
        super().update_translations()  # Call base method if it has common logic
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
