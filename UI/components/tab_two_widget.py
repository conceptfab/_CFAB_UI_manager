from PyQt6.QtWidgets import QCheckBox, QLabel, QSpinBox

from utils.translation_manager import TranslationManager

from .base_tab_widget import BaseTabWidget


class TabTwoWidget(BaseTabWidget):
    def __init__(self):
        super().__init__(object_name="TabTwoContent")

        self.label = QLabel(
            TranslationManager.translate("app.tabs.content.tab2.content")
        )
        self.label.setObjectName("TabTwoLabel")

        self.checkbox = QCheckBox(
            TranslationManager.translate("app.tabs.content.tab2.checkbox")
        )
        self.checkbox.setObjectName("TabTwoCheckbox")
        self.checkbox.toggled.connect(self.on_checkbox_toggle)

        self.spinbox_label = QLabel(
            TranslationManager.translate("app.tabs.content.tab2.select_value")
        )
        self.spinbox = QSpinBox()
        self.spinbox.setObjectName("TabTwoSpinBox")
        self.spinbox.setRange(1, 10)
        self.spinbox.valueChanged.connect(self.on_spinbox_change)

        # Use the layout from BaseTabWidget
        self._add_widgets_to_layout(
            [self.label, self.checkbox, self.spinbox_label, self.spinbox]
        )

    def update_translations(self):
        super().update_translations()  # Call base method if it has common logic
        self.label.setText(
            TranslationManager.translate("app.tabs.content.tab2.content")
        )
        self.checkbox.setText(
            TranslationManager.translate("app.tabs.content.tab2.checkbox")
        )
        self.spinbox_label.setText(
            TranslationManager.translate("app.tabs.content.tab2.select_value")
        )

    def on_checkbox_toggle(self, checked):
        if checked:
            self.label.setText(
                TranslationManager.translate("app.tabs.content.tab2.checkbox_checked")
            )
        else:
            self.label.setText(
                TranslationManager.translate("app.tabs.content.tab2.checkbox_unchecked")
            )

    def on_spinbox_change(self, value):
        self.checkbox.setText(
            TranslationManager.translate("app.tabs.content.tab2.new_value", str(value))
        )
