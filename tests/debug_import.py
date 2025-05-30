"""
Debugowanie importu modułu system_info.
"""

import os
import sys

# Dodanie ścieżki do katalogu głównego projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("====== Test importu utils.system_info ======")
print(f"sys.path: {sys.path}")

try:
    import utils

    print(f"Zawartość pakietu utils: {dir(utils)}")

    from utils import system_info

    print(f"Zaimportowano moduł system_info: {dir(system_info)}")

    from utils.system_info import get_stable_uuid

    uuid_value = get_stable_uuid()
    print(f"UUID wygenerowane przez get_stable_uuid(): {uuid_value}")

    print("Wszystkie importy zakończone sukcesem!")
except Exception as e:
    print(f"Błąd importu: {e}")

print("==========================================")
