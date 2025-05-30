# Menedżer UI CFAB - Struktura Projektu

Ten dokument przedstawia zorganizowaną strukturę projektu Menedżera UI CFAB.

## Struktura Katalogów

```
├── .cache/                # Katalog cache (tymczasowe dane)
│
├── .git/                  # Repozytorium Git
│
├── .gitignore             # Pliki i foldery ignorowane przez Git
│
├── .vscode/               # Konfiguracja Visual Studio Code
│
├── architecture/           # Główna architektura aplikacji
│   ├── __init__.py         # Eksport modułów architektury
│   ├── config_management.py    # Transakcyjne zarządzanie konfiguracją
│   ├── dependency_injection.py # Kontener wstrzykiwania zależności
│   ├── mvvm.py             # Implementacja wzorca Model-View-ViewModel
│   └── state_management.py # Scentralizowane zarządzanie stanem (podobne do Redux)
│
├── benchmarks/             # Testy wydajnościowe
│   ├── benchmark_results.json  # Najnowsze wyniki testów wydajności
│   └── performance_benchmark.py # Narzędzia do testowania wydajności
│
├── docs/                   # Dokumentacja projektu
│   ├── CLEANUP_SUMMARY.md  # Podsumowanie czyszczenia kodu
│   ├── PERFORMANCE_OPTIMIZATION_COMPLETION_REPORT.md # Raport z optymalizacji wydajności
│   ├── PROJECT_MAP.md      # Mapa projektu w formie diagramów
│   ├── PROJECT_STRUCTURE.md # Ten plik - struktura projektu
│   ├── SECURITY_IMPROVEMENTS.md # Ulepszenia bezpieczeństwa
│   ├── SYSTEM_INFO_MODULE.md # Dokumentacja modułu system_info
│   ├── poprawki.md         # Lista poprawek i zmian
│   └── raport.md           # Raport z postępu prac
│
├── resources/              # Zasoby statyczne
│   ├── styles.qss          # Arkusz stylów Qt
│   └── img/                # Obrazy i ikony
│       ├── icon.png        # Ikona aplikacji
│       └── splash.jpg      # Obraz ekranu powitalnego
│
├── scripts/                # Skrypty narzędziowe
│   ├── cleanup.py          # Skrypt czyszczący przestarzałe pliki
│   ├── README.md           # Instrukcje dla skryptów
│   └── setup_dev.py        # Konfiguracja środowiska deweloperskiego
│
├── tests/                  # Zestaw testów
│   ├── debug_import.py           # Skrypt debugowania importów
│   ├── performance_benchmark.py  # Testy wydajnościowe
│   ├── quick_test.py             # Szybkie testy
│   ├── simple_config_test.py     # Testy konfiguracji
│   ├── test_architecture.py      # Testy architektury
│   ├── test_final_integration.py # Testy końcowej integracji
│   ├── test_integration.py       # Testy integracyjne
│   ├── test_main_imports.py      # Testy głównych importów
│   ├── test_performance_optimization.py # Testy optymalizacji wydajności
│   ├── test_security_improvements.py # Testy usprawnień bezpieczeństwa
│   ├── test_system_info.py       # Testy modułu system_info
│   └── test_translation_fix.py   # Testy poprawek tłumaczeń
│
├── translations/           # Internacjonalizacja
│   ├── en.json            # Tłumaczenia angielskie
│   ├── pl.json            # Tłumaczenia polskie
│   └── texts.md           # Wytyczne do tłumaczeń
│
├── UI/                     # Komponenty interfejsu użytkownika
│   ├── main_window.py     # Główne okno aplikacji
│   ├── about_dialog.py    # Okno dialogowe "O programie"
│   ├── hardware_profiler.py  # Interfejs profilowania sprzętu
│   ├── preferences_dialog.py # Okno dialogowe ustawień
│   ├── progress_controller.py # Wskaźniki postępu
│   ├── splash_screen.py   # Ekran powitalny przy uruchomieniu
│   ├── __pycache__/       # Skompilowane pliki Pythona dla UI
│   │   ├── about_dialog.cpython-313.pyc
│   │   ├── hardware_profiler.cpython-313.pyc
│   │   ├── main_window.cpython-313.pyc
│   │   ├── preferences_dialog.cpython-313.pyc
│   │   └── splash_screen.cpython-313.pyc
│   ├── components/        # Komponenty wielokrotnego użytku
│   │   ├── console_widget.py  # Widżet konsoli
│   │   ├── menu_bar.py        # Pasek menu
│   │   ├── status_bar_manager.py # Menedżer paska stanu
│   │   ├── tab_one_widget.py    # Widżet pierwszej zakładki
│   │   ├── tab_two_widget.py    # Widżet drugiej zakładki
│   │   ├── tab_three_widget.py  # Widżet trzeciej zakładki
│   │   └── __pycache__/       # Skompilowane pliki Pythona dla komponentów UI
│   └── style_editor/      # Edytor motywów/stylów
│       ├── style_editor_app.py     # Aplikacja edytora stylu
│       ├── style_editor_window.py  # Okno edytora stylu
│       └── ui_showcase_widget.py   # Widżet pokazowy UI
│
└── utils/                  # Moduły narzędziowe
    ├── __init__.py        # Plik inicjalizacyjny pakietu
    ├── config_cache.py    # Buforowanie konfiguracji
    ├── enhanced_splash.py # Rozszerzone narzędzia ekranu powitalnego
    ├── exceptions.py      # Niestandardowe klasy wyjątków
    ├── improved_thread_manager.py # Zaawansowane zarządzanie wątkami
    ├── logger.py          # Konfiguracja logowania
    ├── performance_optimizer.py  # Monitorowanie wydajności
    ├── secure_commands.py # Bezpieczne wykonywanie poleceń
    ├── system_info.py     # Informacje o systemie i sprzęcie
    ├── thread_manager.py  # Podstawowe zarządzanie wątkami (przestarzałe)
    ├── translation_manager.py   # Zarządzanie tłumaczeniami
    ├── translator.py      # Narzędzia do tłumaczeń
    ├── validators.py      # Walidacja danych wejściowych
    └── __pycache__/       # Skompilowane pliki Pythona
        ├── __init__.cpython-313.pyc
        ├── config_cache.cpython-313.pyc
        ├── exceptions.cpython-313.pyc
        ├── logger.cpython-313.pyc
        ├── system_info.cpython-313.pyc
        └── ... (pozostałe pliki .pyc)
```

├── venv/ # Wirtualne środowisko Pythona
│ └── cpython3.13-5b045e286e36-compat-af96b9431081/ # Pliki interpretera
│
├── **pycache**/ # Skompilowane pliki Pythona głównego katalogu
│ └── main_app.cpython-313.pyc # Skompilowany główny moduł aplikacji
│
├── main_app.py # Główny skrypt uruchomieniowy aplikacji
├── config.json # Plik konfiguracyjny aplikacji
├── hardware.json # Dane profilowania sprzętu
├── readme.md # Dokumentacja podstawowa projektu
├── requirements.txt # Lista zależności Pythona
├── TODO.md # Lista zadań do wykonania
└── uuid_debug.txt # Plik debugowania UUID

## Kluczowe Pliki

- `main_app.py` - Główny punkt wejścia aplikacji
- `config.json` - Konfiguracja aplikacji
- `hardware.json` - Wyniki wykrywania sprzętu
- `TODO.md` - Plan rozwoju i zadania
- `readme.md` - Przegląd projektu i instrukcje konfiguracji
- `requirements.txt` - Zależności projektu wymagane do instalacji
- `uuid_debug.txt` - Plik do debugowania generowania UUID

## Przegląd Architektury

Projekt wykorzystuje nowoczesne wzorce architektury oprogramowania:

1. **Wzorzec MVVM** - Oddzielenie logiki biznesowej od interfejsu użytkownika
2. **Wstrzykiwanie Zależności** - Luźne powiązanie komponentów i testowalność
3. **Scentralizowane Zarządzanie Stanem** - Obsługa stanu podobna do Redux
4. **Transakcyjne Zarządzanie Konfiguracją** - Bezpieczne zarządzanie konfiguracją
5. **Bezpieczeństwo jako Priorytet** - Walidacja danych wejściowych i bezpieczne wykonywanie
6. **Optymalizacja Wydajności** - Strategie wielowątkowości i buforowania

## Wytyczne Rozwoju

- Wszystkie nowe funkcje powinny wykorzystywać szkielet architektury
- Wymagane są testy dla nowych funkcjonalności
- Należy przestrzegać istniejącego stylu i wzorców kodu
- Aktualizuj dokumentację dla znaczących zmian
- Używaj kontenera wstrzykiwania zależności do zarządzania usługami
