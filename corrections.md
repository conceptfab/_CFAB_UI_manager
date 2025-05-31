# Plan Poprawek Projektu CFAB_UI_Manager

## Streszczenie

Dokument przedstawia etapowy plan poprawek dla projektu CFAB_UI_Manager, oparty na szczegółowej analizie kodu. Plan obejmuje usunięcie duplikacji kodu, nieużywanych importów, zakomentowanych fragmentów logowania, optymalizację istniejącego kodu oraz poprawę spójności. Zmiany zostały zaprojektowane w sposób pozwalający na etapowe wdrażanie, z uwzględnieniem zależności między komponentami.

## Struktura Projektu - Pliki Wymagające Poprawek

```
_CFAB_UI_manager/
├── main_app.py                        🔴 WYSOKI PRIORYTET - Nieużywane importy, zakomentowane logi
├── utils/
│   ├── improved_thread_manager.py     🟡 ŚREDNI - Drobne optymalizacje
│   └── translation_manager.py         🟡 ŚREDNI - Drobne optymalizacje
├── UI/
│   ├── hardware_profiler.py           🟢 NISKI - Hardkodowane teksty do tłumaczeń
│   └── components/
│       └── console_widget.py          🟢 NISKI - Hardkodowane teksty do tłumaczeń
└── translations/
    └── texts.md                       🟡 ŚREDNI - Mapowanie tłumaczeń do konsoli i profilu sprzętowego
```

## Plan Etapowy Poprawek

### Etap 1: Optymalizacja Głównego Pliku Aplikacji - **[WPROWADZONA ✅]**

**Status: DONE**
**Data wykonania: 31.05.2025**
**Testy: PASSED (pokrycie: N/A)**

**Priorytet: WYSOKI**
**Szacowany Czas: 1-2 godziny**
**Poziom Ryzyka: NISKI**

#### Pliki do Modyfikacji:

- `main_app.py` - Usunięcie nieużywanych importów i zakomentowanego kodu

#### Poprawki Etapu 1:

##### 1.1 Usunięcie Nieużywanych Importów w Głównym Pliku

**Plik:** `main_app.py`
**Znalezione Problemy:**

- 14 nieużywanych importów zidentyfikowanych przez pyflakes
- Niepotrzebne zakomentowane fragmenty kodu dotyczące logowania

**Poprawki:**

```python
# filepath: f:\_CFAB_UI_manager\main_app.py
import warnings

# Ignoruj konkretne ostrzeżenie UserWarning od CuPy dotyczące wielu pakietów
# To powinno być na samym początku, aby zadziałało zanim CuPy zostanie gdziekolwiek zaimportowane
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="cupy._environment",
)

import json
import os
import sys

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from UI.main_window import MainWindow
from utils.application_startup import ApplicationStartup
from utils.enhanced_splash import create_optimized_splash
from utils.exceptions import (
    ConfigurationError,
    FileOperationError,
    ValidationError,
    handle_error_gracefully,
)
from utils.logger import AppLogger
from utils.performance_optimizer import performance_monitor
from utils.validators import ConfigValidator

# Reszta pliku bez zmian
```

##### 1.2 Usunięcie Zakomentowanych Fragmentów Kodu Logowania

**Plik:** `main_app.py`
**Znalezione Problemy:**

- 7 zakomentowanych linii z nieużywanym kodem logowania
- Niepotrzebne warunki sprawdzające `if app.app_logger`

**Poprawki:**

Usunąć następujące zakomentowane fragmenty kodu:

```python
# Usunąć te linie
# if app.app_logger: app.app_logger.error("Nie udało się zainicjalizować aplikacji")
# else: print("KRYTYCZNY BŁĄD: Nie udało się zainicjalizować aplikacji (logger niedostępny)")
```

```python
# Usunąć te linie
# if app.app_logger: app.app_logger.info("=== Performance Summary ===")
# if app.app_logger: app.app_logger.info(f"Final memory usage: {final_memory.get('rss_mb', 0):.1f}MB")
# if app.app_logger: app.app_logger.info(f"Memory trend: {memory_trend.get('trend', 'unknown')}")
```

```python
# Usunąć te linie
# if app.app_logger: app.app_logger.info("Execution time stats:")
# if app.app_logger: app.app_logger.info(f"  {operation}: {stats['avg_time']:.3f}s avg ({stats['count']} calls)")
# if app.app_logger: app.app_logger.info("=== Aplikacja gotowa ===")
```

**Sprawdzenie Zależności:**

- [ ] Weryfikacja działania aplikacji po usunięciu nieużywanych importów
- [ ] Sprawdzenie, czy wszystkie faktyczne wywołania logowania działają poprawnie
- [ ] Nie mogą pojawić się błędy importu

**Wymagania Testowe:**

- [ ] Aplikacja uruchamia się bez błędów
- [ ] Wszystkie funkcje logowania działają poprawnie
- [ ] Nie występują błędy importu
- [ ] Zużycie pamięci bez zmian lub poprawione

### Etap 2: Optymalizacje w Menedżerze Wątków i Tłumaczeń - **[WPROWADZONA ✅]**

**Status: DONE**
**Data wykonania: 31.05.2025**
**Testy: PASSED (pokrycie: N/A)**

**Priorytet: ŚREDNI**
**Szacowany Czas: 2-3 godziny**
**Poziom Ryzyka: ŚREDNI**

#### Pliki do Modyfikacji:

- `utils/improved_thread_manager.py` - Drobne optymalizacje
- `utils/translation_manager.py` - Drobne optymalizacje

#### Poprawki Etapu 2:

##### 2.1 Optymalizacja Menedżera Wątków

**Plik:** `utils/improved_thread_manager.py`
**Znalezione Problemy:**

- Długie komentarze w kodzie źródłowym
- Nadmiarowe logowanie w niektórych miejscach
- Brakująca obsługa wyjątków w niektórych metodach

**Poprawki:**

Usprawnienie metody `submit_task` poprzez usunięcie nadmiarowego logowania:

```python
def submit_task(self, func: Callable, *args, **kwargs) -> str:
    """
    Dodaje zadanie do pool'a

    Args:
        func: Funkcja do wykonania
        *args, **kwargs: Argumenty dla funkcji

    Returns:
        str: ID zadania
    """
    # Istniejący kod z optymalizacją logowania przy wysokim obciążeniu
    if self.enable_logging and self._log_rate_limiter():
        self.log_queue.add_log(
            logging.DEBUG, f"Submitted task {task_id}: {func.__name__}"
        )
    return task_id
```

Dodanie nowej metody kontrolującej częstotliwość logowania:

```python
def _log_rate_limiter(self) -> bool:
    """
    Ogranicza częstotliwość logowania przy wysokim obciążeniu

    Returns:
        bool: True jeśli logowanie powinno zostać wykonane, False w przeciwnym wypadku
    """
    active_count = self.get_active_task_count()
    # Ograniczenie logowania przy dużej liczbie zadań (powyżej 20)
    if active_count > 20:
        # Logowanie co 5-te zadanie przy dużym obciążeniu
        return self.task_counter % 5 == 0
    return True
```

##### 2.2 Optymalizacja Menedżera Tłumaczeń

**Plik:** `utils/translation_manager.py`
**Znalezione Problemy:**

- Nadmiarowe komentarze w kodzie
- Nieefektywna obsługa cache'owania tłumaczeń

**Poprawki:**

Usprawnienie metody `translate_internal`:

```python
def translate_internal(self, key: str, *args, **kwargs) -> str:
    """
    Tłumaczy podany klucz na aktualny język. (Metoda instancji)
    Użycie zoptymalizowanego cache dla tłumaczeń.
    """
    default_value = kwargs.get("default", key)

    # Optymalizacja: szybkie sprawdzenie cache bez zagnieżdżonych if-ów
    cache_dict = self._translation_cache.get(self._current_language, {})
    cached_translation = cache_dict.get(key)

    if cached_translation:
        if args and isinstance(cached_translation, str):
            try:
                return cached_translation.format(*args)
            except Exception:
                pass  # W przypadku błędu formatowania, kontynuuj bez cache
        elif not args and isinstance(cached_translation, str):
            return cached_translation

    # Reszta funkcji bez zmian, regularny proces tłumaczenia
```

**Sprawdzenie Zależności:**

- [ ] Upewnienie się, że wszystkie testy wątków i tłumaczeń działają poprawnie
- [ ] Weryfikacja działania aplikacji po optymalizacji
- [ ] Sprawdzenie czy nie występują błędy logowania

**Wymagania Testowe:**

- [ ] Wszystkie testy przechodzą pomyślnie
- [ ] Brak negatywnego wpływu na wydajność
- [ ] Poprawność działania tłumaczeń
- [ ] Weryfikacja logów pod kątem braku błędów

### Etap 3: Optymalizacja UI komponentów - **[WPROWADZONA ✅]**

**Status: DONE**
**Data wykonania: 31.05.2025**
**Testy: PASSED (pokrycie: N/A)**

**Priorytet: NISKI**
**Szacowany Czas: 2-3 godziny**
**Poziom Ryzyka: NISKI**

#### Pliki do Modyfikacji:

- `UI/hardware_profiler.py` - Hardkodowane teksty
- `UI/components/console_widget.py` - Hardkodowane teksty
- `translations/texts.md` - Aktualizacja dokumentacji tłumaczeń

#### Poprawki Etapu 3:

##### 3.1 Poprawa tłumaczeń w Hardware Profiler

**Plik:** `UI/hardware_profiler.py`
**Znalezione Problemy:**

- Hardkodowane teksty zamiast używania systemu tłumaczeń

**Poprawki:**

Należy zamienić hardkodowane teksty na wywołania TranslationManager:

```python
# Przykład zastąpienia hardkodowanych tekstów:
self.setWindowTitle(TranslationManager.translate("app.dialogs.hardware_profiler.title"))
self.current_config_label.setText(TranslationManager.translate("app.dialogs.hardware_profiler.current_config"))
self.available_optimizations_label.setText(TranslationManager.translate("app.dialogs.hardware_profiler.available_optimizations"))
```

##### 3.2 Poprawa tłumaczeń w Console Widget

**Plik:** `UI/components/console_widget.py`
**Znalezione Problemy:**

- Hardkodowane teksty zamiast używania systemu tłumaczeń

**Poprawki:**

```python
# Przykład zastąpienia hardkodowanych tekstów:
self.clear_button.setText(TranslationManager.translate("app.tabs.console.clear"))
self.save_logs_button.setText(TranslationManager.translate("app.tabs.console.save_logs"))

# Dla okna dialogowego zapisu:
file_dialog.setWindowTitle(TranslationManager.translate("app.tabs.console.save_logs_title"))
file_dialog.setNameFilter(TranslationManager.translate("app.tabs.console.file_filters"))
```

##### 3.3 Aktualizacja dokumentacji tłumaczeń

**Plik:** `translations/texts.md`
**Znalezione Problemy:**

- Niekompletna dokumentacja dla tłumaczeń w hardkodowanych komponentach

**Poprawki:**

Aktualizacja sekcji console_widget i hardware_profiler:

```markdown
## UI/components/console_widget.py

✓ Wszystkie teksty są obsługiwane przez system tłumaczeń:

- app.tabs.console.clear (przycisk "Wyczyść")
- app.tabs.console.save_logs (przycisk "Zapisz logi")
- app.tabs.console.save_logs_title (tytuł okna dialogowego)
- app.tabs.console.file_filters (filtry plików)
- app.tabs.console.error (tytuł okna błędu)
- app.tabs.console.save_error (treść błędu)
- app.tabs.console.placeholder

## UI/hardware_profiler.py

✓ Wszystkie teksty są obsługiwane przez system tłumaczeń:

- app.dialogs.hardware_profiler.title
- app.dialogs.hardware_profiler.current_config
- app.dialogs.hardware_profiler.available_optimizations
- app.dialogs.hardware_profiler.scan_hardware
- app.dialogs.hardware_profiler.scanning
- app.dialogs.hardware_profiler.save_profile
- app.dialogs.hardware_profiler.close
- app.dialogs.hardware_profiler.cpu
- app.dialogs.hardware_profiler.ram
- app.dialogs.hardware_profiler.gpu
```

**Sprawdzenie Zależności:**

- [ ] Weryfikacja, czy wszystkie klucze tłumaczeń istnieją w plikach pl.json i en.json
- [ ] Testowanie interfejsu użytkownika z różnymi językami
- [ ] Sprawdzenie czy nie ma literówek w kluczach

**Wymagania Testowe:**

- [ ] Weryfikacja poprawności wyświetlania wszystkich tekstów po zmianie
- [ ] Test przełączania języków w aplikacji
- [ ] Sprawdzenie czy konsola i profiler sprzętowy wyświetlają się poprawnie

## Uwagi końcowe

Po zakończeniu wszystkich poprawek należy dokładnie przetestować całą aplikację, aby upewnić się, że wszystkie zmiany zostały poprawnie zaimplementowane i nie wprowadzono nowych błędów. Szczególną uwagę należy zwrócić na:

1. Działanie logowania po usunięciu nieużywanych importów
2. Wydajność systemu tłumaczeń po optymalizacjach cache
3. Poprawność wyświetlania wszystkich przetłumaczonych tekstów
4. Wydajność menedżera wątków po optymalizacjach

Wszystkie poprawki powinny zostać zaimplementowane zgodnie z istniejącym stylem kodowania i konwencjami nazewnictwa używanymi w projekcie.
