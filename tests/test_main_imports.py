"""
Test importów dla głównej aplikacji.
"""

import os
import sys

# Dodanie ścieżki do katalogu głównego projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("====== Test importów dla main_app.py ======")

try:
    # Import modułu system_info
    from utils.system_info import get_stable_uuid

    print(f"Zaimportowano get_stable_uuid(): {get_stable_uuid()}")

    # Próba importu klas i funkcji z main_app.py
    from main_app import (
        create_new_hardware_profile,
        log_uuid_debug,
        verify_hardware_profile,
    )

    print("Zaimportowano funkcje z main_app.py")

    # Test funkcji z main_app.py
    print("\nTestowanie funkcji create_new_hardware_profile()...")
    profile = create_new_hardware_profile()
    print(f"Utworzony profil: {profile['uuid']}")

    print("\nWszystkie importy i funkcje działają poprawnie!")
except Exception as e:
    print(f"Błąd: {e}")

print("==========================================")
