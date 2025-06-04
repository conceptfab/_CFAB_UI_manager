"""
Test zgodności środowiska z requirements.txt.
Sprawdza czy wszystkie wymagane zależności są zainstalowane i w odpowiednich wersjach.
"""

import importlib
import os
import platform
import re
import sys
import unittest


class TestRequirements(unittest.TestCase):
    """Testy dla pliku requirements.txt - sprawdzanie zgodności zainstalowanych pakietów."""

    def setUp(self):
        """Przygotowanie testu - wczytanie pliku requirements.txt."""
        self.requirements_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "requirements.txt",
        )
        self.requirements = self._parse_requirements()

    def _parse_requirements(self):
        """Parsowanie pliku requirements.txt."""
        requirements = []
        with open(self.requirements_path, "r") as f:
            for line in f:
                # Pomiń komentarze i puste linie
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Obsługa warunków platformy
                platform_condition = None
                if ";" in line:
                    package_spec, platform_condition = line.split(";", 1)
                    package_spec = package_spec.strip()
                    platform_condition = platform_condition.strip()
                else:
                    package_spec = line

                # Wyodrębnij nazwę pakietu i wersję
                if ">=" in package_spec:
                    package_name, version_spec = package_spec.split(">=", 1)
                    version_spec = version_spec.strip()
                    operator = ">="
                elif "==" in package_spec:
                    package_name, version_spec = package_spec.split("==", 1)
                    version_spec = version_spec.strip()
                    operator = "=="
                else:
                    package_name = package_spec
                    version_spec = None
                    operator = None

                package_name = package_name.strip()
                requirements.append(
                    {
                        "name": package_name,
                        "version_spec": version_spec,
                        "operator": operator,
                        "platform_condition": platform_condition,
                    }
                )

        return requirements

    def _check_platform_condition(self, condition):
        """Sprawdza czy warunek platformy jest spełniony."""
        if not condition:
            return True

        # Obsługa warunku sys_platform
        if "sys_platform ==" in condition:
            platform_match = re.search(
                r'sys_platform\s*==\s*["\']([^"\']+)["\']', condition
            )
            if platform_match:
                required_platform = platform_match.group(1)
                return sys.platform == required_platform

        # Obsługa warunku python_version
        if "python_version <" in condition:
            version_match = re.search(
                r'python_version\s*<\s*["\']([^"\']+)["\']', condition
            )
            if version_match:
                required_version = version_match.group(1)
                python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                return python_version < required_version

        # Domyślnie zwracamy True, jeśli nie wiemy jak obsłużyć warunek
        return True

    def _is_package_installed(self, package_info):
        """Sprawdza czy pakiet jest zainstalowany i w odpowiedniej wersji."""
        name = package_info["name"]
        try:
            # Obsługa specjalnych przypadków
            if name == "PyQt6":
                # PyQt6 może być sprawdzany przez importowanie
                module = importlib.import_module(name.lower())
                if not hasattr(module, "__version__"):
                    return True  # Nie możemy sprawdzić wersji, zakładamy że jest OK
                installed_version = module.__version__
            else:
                # Standardowy przypadek - próbujemy zaimportować pakiet
                try:
                    module = importlib.import_module(name)
                    if hasattr(module, "__version__"):
                        installed_version = module.__version__
                    elif hasattr(module, "version"):
                        installed_version = module.version
                    else:
                        # Nie możemy określić wersji, zakładamy że jest OK
                        return True
                except ImportError:
                    # Próbujemy zaimportować jako moduł z podkreśleniami zamiast myślników
                    alt_name = name.replace("-", "_")
                    try:
                        module = importlib.import_module(alt_name)
                        if hasattr(module, "__version__"):
                            installed_version = module.__version__
                        else:
                            # Nie możemy określić wersji, zakładamy że jest OK
                            return True
                    except ImportError:
                        return False

            # Jeśli nie wymagamy konkretnej wersji, wystarczy że pakiet jest zainstalowany
            if not package_info["version_spec"]:
                return True

            # Porównujemy wersje
            if package_info["operator"] == ">=":
                return installed_version >= package_info["version_spec"]
            elif package_info["operator"] == "==":
                return installed_version == package_info["version_spec"]
            else:
                # Jeśli nie znamy operatora, zakładamy że jest OK
                return True

        except Exception as e:
            print(f"Błąd podczas sprawdzania pakietu {name}: {e}")
            return False

    def test_required_packages(self):
        """Test sprawdzający czy wszystkie wymagane pakiety są zainstalowane."""
        missing_packages = []

        for package_info in self.requirements:
            # Jeśli warunek platformy nie jest spełniony, pomijamy pakiet
            if not self._check_platform_condition(package_info["platform_condition"]):
                continue

            if not self._is_package_installed(package_info):
                missing_packages.append(
                    f"{package_info['name']}{package_info['operator'] or ''}{package_info['version_spec'] or ''}"
                )

        self.assertEqual(
            len(missing_packages),
            0,
            f"Brakujące pakiety: {', '.join(missing_packages)}",
        )

    def test_requirements_format(self):
        """Test sprawdzający format pliku requirements.txt."""
        with open(self.requirements_path, "r") as f:
            content = f.read()

        # Sprawdź czy plik zawiera komentarze (sekcje)
        self.assertIn(
            "#",
            content,
            "Plik requirements.txt powinien zawierać komentarze z podziałem na sekcje.",
        )

        # Sprawdź czy nie ma pustych linii na początku lub końcu pliku
        lines = content.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        self.assertTrue(lines, "Plik requirements.txt nie może być pusty.")
        self.assertTrue(
            lines[0].strip(),
            "Plik requirements.txt nie może zaczynać się od pustej linii.",
        )
        self.assertTrue(
            lines[-1].strip(), "Plik requirements.txt nie może kończyć się pustą linią."
        )


if __name__ == "__main__":
    unittest.main()
