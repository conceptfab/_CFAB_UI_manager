"""
Test dla modułu system_info.py.
"""

import os
import sys
import time
import unittest

# Dodanie ścieżki do katalogu głównego projektu do sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.system_info import clear_uuid_cache, get_stable_uuid


class TestSystemInfo(unittest.TestCase):
    """Testy dla funkcji w module system_info."""

    def test_uuid_stability(self):
        """Test stabilności generowanego UUID."""
        uuid1 = get_stable_uuid()
        uuid2 = get_stable_uuid()
        self.assertEqual(uuid1, uuid2, "UUID powinno być stabilne między wywołaniami")

    def test_uuid_cache(self):
        """Test mechanizmu cache dla UUID."""
        # Pierwsze wywołanie - mierzy czas
        start = time.time()
        uuid1 = get_stable_uuid()
        time1 = time.time() - start

        # Drugie wywołanie - powinno być szybsze dzięki cache
        start = time.time()
        uuid2 = get_stable_uuid()
        time2 = time.time() - start

        # Sprawdzenie, czy UUID są identyczne
        self.assertEqual(uuid1, uuid2, "UUID powinno być identyczne")

        # Zwykle drugie wywołanie powinno być szybsze, ale możemy
        # nie zauważyć różnicy przy bardzo małych czasach
        # Wydrukuj czasy dla informacji
        print(f"Czas pierwszego wywołania: {time1:.6f}s")
        print(f"Czas drugiego wywołania: {time2:.6f}s")

        # Wyczyszczenie cache
        clear_uuid_cache()

        # Trzecie wywołanie - powinno trwać podobnie do pierwszego
        start = time.time()
        uuid3 = get_stable_uuid()
        time3 = time.time() - start

        # UUID po wyczyszczeniu cache nadal powinno być takie samo
        self.assertEqual(
            uuid1, uuid3, "UUID po wyczyszczeniu cache powinno być takie samo"
        )
        print(f"Czas po wyczyszczeniu cache: {time3:.6f}s")


if __name__ == "__main__":
    unittest.main()
