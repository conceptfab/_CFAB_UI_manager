from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit

class TabOneWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TabOneContent") # Dla ewentualnego stylowania
        layout = QVBoxLayout(self)

        self.label = QLabel("To jest zawartość pierwszej zakładki.")
        self.label.setObjectName("TabOneLabel")
        self.button = QPushButton("Przycisk w zakładce 1")
        self.button.setObjectName("TabOneButton")
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Wpisz coś w zakładce 1...")
        self.line_edit.setObjectName("TabOneLineEdit")


        self.button.clicked.connect(self.on_button_click)

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button)
        layout.addStretch() # Dodaje elastyczną przestrzeń na dole

        self.setLayout(layout)

    def on_button_click(self):
        text = self.line_edit.text()
        if text:
            self.label.setText(f"W zakładce 1 wpisano: {text}")
        else:
            self.label.setText("W zakładce 1 nic nie wpisano.")