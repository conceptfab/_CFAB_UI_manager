from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QFileDialog, QMessageBox,
                             QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, QSaveFile, QIODevice # Dodano QIODevice
from ui_showcase_widget import UIShowcaseWidget
import os

class StyleEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edytor Stylów PyQt6")
        self.setGeometry(150, 150, 1200, 800)

        self.current_style_path = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Zastosuj Styl")
        self.apply_button.clicked.connect(self.apply_style)
        self.load_button = QPushButton("Wczytaj QSS")
        self.load_button.clicked.connect(self.load_style_from_file)
        self.save_button = QPushButton("Zapisz QSS")
        self.save_button.clicked.connect(self.save_style_to_file)
        self.save_as_button = QPushButton("Zapisz QSS jako...")
        self.save_as_button.clicked.connect(lambda: self.save_style_to_file(save_as=True))

        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.save_as_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        main_layout.addLayout(button_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.qss_text_edit = QTextEdit()
        self.qss_text_edit.setPlaceholderText("Wpisz tutaj swój QSS lub wczytaj z pliku...")
        self.qss_text_edit.setAcceptRichText(False)
        self.qss_text_edit.setStyleSheet("font-family: 'Courier New', monospace; font-size: 10pt;")
        splitter.addWidget(self.qss_text_edit)

        self.showcase_scroll_area = QScrollArea()
        self.showcase_scroll_area.setWidgetResizable(True)
        self.showcase_widget_container = QWidget()
        self.showcase_widget_container.setObjectName("ShowcaseContainer")
        
        showcase_layout = QVBoxLayout(self.showcase_widget_container)
        self.ui_showcase = UIShowcaseWidget()
        showcase_layout.addWidget(self.ui_showcase)
        
        self.showcase_scroll_area.setWidget(self.showcase_widget_container)
        splitter.addWidget(self.showcase_scroll_area)

        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)
        
        # Ścieżka do styles.qss względem style_editor_window.py
        # style_editor/ -> .. -> aplikacja_pyqt/ -> resources/styles.qss
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_style_path = os.path.join(script_dir, "..", "resources", "styles.qss")

        if os.path.exists(default_style_path):
            self.load_style_from_file(default_style_path)
            print(f"Załadowano domyślny styl: {default_style_path}")
        else:
            print(f"Domyślny plik stylów nie znaleziony: {default_style_path}")
            self.apply_style()

    def apply_style(self):
        style_sheet = self.qss_text_edit.toPlainText()
        self.showcase_widget_container.setStyleSheet(style_sheet)

    def load_style_from_file(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, "Wczytaj plik QSS", self.current_style_path or "", "Pliki QSS (*.qss);;Wszystkie pliki (*)"
            )
        if path:
            try:
                with open(path, "r", encoding='utf-8') as f:
                    self.qss_text_edit.setPlainText(f.read())
                self.current_style_path = path
                self.apply_style()
                self.setWindowTitle(f"Edytor Stylów PyQt6 - {os.path.basename(path)}")
                QMessageBox.information(self, "Sukces", f"Wczytano styl z: {path}")
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się wczytać pliku: {e}")
                print(f"Błąd wczytywania pliku: {e}")


    def save_style_to_file(self, save_as=False):
        path = self.current_style_path
        if save_as or not path:
            # Domyślna ścieżka zapisu, jeśli `current_style_path` nie jest ustawiony
            default_save_dir = os.path.dirname(self.current_style_path) if self.current_style_path else ""
            default_filename = os.path.join(default_save_dir, "nowy_styl.qss")

            path, _ = QFileDialog.getSaveFileName(
                self, "Zapisz plik QSS", self.current_style_path or default_filename, "Pliki QSS (*.qss);;Wszystkie pliki (*)"
            )
        
        if path:
            try:
                save_file = QSaveFile(path)
                # Używamy QIODevice.OpenModeFlag.WriteOnly zamiast QSaveFile.OpenModeFlag
                if save_file.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Text):
                    text_to_save = self.qss_text_edit.toPlainText()
                    # QSaveFile.write() oczekuje bajtów
                    if save_file.write(text_to_save.encode('utf-8')) == -1:
                         raise IOError(f"Błąd zapisu do QSaveFile (write zwrócił -1): {save_file.errorString()}")
                    
                    if not save_file.commit():
                        raise IOError(f"Błąd commit QSaveFile: {save_file.errorString()}")
                    
                    self.current_style_path = path
                    self.setWindowTitle(f"Edytor Stylów PyQt6 - {os.path.basename(path)}")
                    QMessageBox.information(self, "Sukces", f"Zapisano styl w: {path}")
                else:
                    raise IOError(f"Nie można otworzyć QSaveFile do zapisu: {save_file.errorString()}")
            except Exception as e:
                QMessageBox.warning(self, "Błąd", f"Nie udało się zapisać pliku: {e}")
                print(f"Błąd zapisu pliku: {e}")