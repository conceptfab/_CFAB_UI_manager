from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton

from utils.translation_manager import TranslationManager

from .base_tab_widget import BaseTabWidget


class TabOneWidget(BaseTabWidget):
    def __init__(self):
        super().__init__(object_name="TabOneContent")

        self.label = QLabel(
            TranslationManager.translate("app.tabs.content.tab1.content")
        )
        self.label.setObjectName("TabOneLabel")
        self.button = QPushButton(
            TranslationManager.translate("app.tabs.content.tab1.button")
        )
        self.button.setObjectName("TabOneButton")
        self.line_edit = QLineEdit()
        self.line_edit.setObjectName("TabOneLineEdit")
        self.line_edit.setPlaceholderText(
            TranslationManager.translate("app.tabs.content.tab1.placeholder")
        )

        self.button.clicked.connect(self.on_button_click)

        # Use the layout from BaseTabWidget
        self._add_widgets_to_layout([self.label, self.line_edit, self.button])

    def update_translations(self):
        super().update_translations()  # Call base method if it has common logic
        self.label.setText(
            TranslationManager.translate("app.tabs.content.tab1.content")
        )
        self.button.setText(
            TranslationManager.translate("app.tabs.content.tab1.button")
        )
        self.line_edit.setPlaceholderText(
            TranslationManager.translate("app.tabs.content.tab1.placeholder")
        )

    def on_button_click(self):
        text = self.line_edit.text()
        if text:
            self.label.setText(
                TranslationManager.translate("app.tabs.content.tab1.text_entered", text)
            )
        else:
            self.label.setText(
                TranslationManager.translate("app.tabs.content.tab1.nothing_entered")
            )
