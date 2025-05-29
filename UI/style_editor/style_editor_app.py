import sys
from PyQt6.QtWidgets import QApplication
from UI.style_editor.style_editor_window import StyleEditorWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor_win = StyleEditorWindow()
    editor_win.show()
    sys.exit(app.exec())