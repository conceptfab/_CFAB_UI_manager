from PyQt6.QtWidgets import QCheckBox, QLabel, QSpinBox, QVBoxLayout, QWidget

from utils.translation_manager import TranslationManager


class TabTwoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TabTwoContent")
        layout = QVBoxLayout(self)

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

        layout.addWidget(self.label)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.spinbox_label)
        layout.addWidget(self.spinbox)
        layout.addStretch()

        self.setLayout(layout)
        TranslationManager.register_widget(self)

    def update_translations(self):
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
