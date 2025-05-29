from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton

class TabThreeWidget(QWidget): # Zmieniona nazwa klasy
    def __init__(self):
        super().__init__()
        self.setObjectName("TabThreeContent")
        layout = QVBoxLayout(self)

        self.label = QLabel("To jest zawartość trzeciej zakładki.")
        self.label.setObjectName("TabThreeLabel")

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("TabThreeTextEdit")
        self.text_edit.setPlaceholderText("Wpisz dłuższy tekst tutaj...")

        self.button = QPushButton("Pokaż tekst z pola")
        self.button.setObjectName("TabThreeButton")
        self.button.clicked.connect(self.on_button_click)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button)
        layout.addStretch()

        self.setLayout(layout)

    def on_button_click(self):
        text_content = self.text_edit.toPlainText()
        if text_content:
            self.label.setText(f"Tekst z pola w zakładce 3:\n{text_content[:100]}...") # Pokaż fragment
        else:
            self.label.setText("Pole tekstowe w zakładce 3 jest puste.")