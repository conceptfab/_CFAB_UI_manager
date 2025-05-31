from PyQt6.QtWidgets import QVBoxLayout, QWidget

from utils.translation_manager import TranslationManager


class BaseTabWidget(QWidget):
    def __init__(self, object_name="BaseTabContent"):
        super().__init__()
        self.setObjectName(object_name)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        TranslationManager.register_widget(self)

    def update_translations(self):
        # This method should be implemented by subclasses to update their specific translatable texts.
        # Example: self.label.setText(TranslationManager.translate("some.key"))
        pass

    def _add_widgets_to_layout(self, widgets):
        for widget in widgets:
            self.layout.addWidget(widget)
        self.layout.addStretch()
