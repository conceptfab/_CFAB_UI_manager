from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QSpinBox

class TabTwoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TabTwoContent")
        layout = QVBoxLayout(self)

        self.label = QLabel("To jest zawartość drugiej zakładki.")
        self.label.setObjectName("TabTwoLabel")

        self.checkbox = QCheckBox("Zaznacz mnie w zakładce 2")
        self.checkbox.setObjectName("TabTwoCheckbox")
        self.checkbox.toggled.connect(self.on_checkbox_toggle)

        self.spinbox_label = QLabel("Wybierz wartość:")
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

    def on_checkbox_toggle(self, checked):
        if checked:
            self.label.setText("Zakładka 2: Checkbox jest zaznaczony!")
        else:
            self.label.setText("Zakładka 2: Checkbox nie jest zaznaczony.")

    def on_spinbox_change(self, value):
        self.checkbox.setText(f"Nowa wartość spinbox: {value}")