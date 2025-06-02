# code_map.md

## Mapa projektu i wstępna analiza (ETAP 1)

CFAB_UI_manager/
├── main_app.py 🔴 WYSOKI PRIORYTET - Główny plik uruchomieniowy, obsługa logiki startowej, potencjalne zakomentowane logi i nieużywane importy, zależności: utils/, architecture/, UI/, config.json
├── config.json 🟡 ŚREDNI PRIORYTET - Konfiguracja aplikacji, wymaga walidacji i ewentualnej optymalizacji struktury, zależności: main_app.py, utils/config_cache.py
├── hardware.json 🟡 ŚREDNI PRIORYTET - Konfiguracja sprzętu, wymaga walidacji i testów, zależności: UI/hardware_profiler.py
├── requirements.txt 🟢 NISKI PRIORYTET - Lista zależności, do aktualizacji po zmianach w kodzie
├── architecture/
│ ├── **init**.py 🟢 NISKI PRIORYTET - Inicjalizacja pakietu
│ ├── action_types.py 🟢 NISKI PRIORYTET - Definicje typów akcji, zależności: mvvm.py
│ ├── config_management.py 🟡 ŚREDNI PRIORYTET - Zarządzanie konfiguracją, wymaga optymalizacji, zależności: main_app.py, utils/
│ ├── dependency_injection.py 🟡 ŚREDNI PRIORYTET - Mechanizm DI, do przeglądu pod kątem cyklicznych zależności
│ ├── mvvm.py 🟡 ŚREDNI PRIORYTET - Wzorzec MVVM, wymaga dokumentacji i testów
│ └── state_management.py 🟡 ŚREDNI PRIORYTET - Zarządzanie stanem, do optymalizacji
├── UI/
│ ├── main_window.py 🔴 WYSOKI PRIORYTET - Główne okno aplikacji, obsługa UI, zależności: komponenty, utils, tłumaczenia
│ ├── hardware_profiler.py 🟡 ŚREDNI PRIORYTET - Profilowanie sprzętu, wymaga optymalizacji ostrzeżeń i pamięci
│ ├── about_dialog.py 🟢 NISKI PRIORYTET - Okno "O programie"
│ ├── preferences_dialog.py 🟡 ŚREDNI PRIORYTET - Okno preferencji, zależności: config.json
│ ├── progress_controller.py 🟢 NISKI PRIORYTET - Kontrola postępu
│ ├── splash_screen.py 🟢 NISKI PRIORYTET - Ekran powitalny
│ ├── components/
│ │ ├── base_tab_widget.py 🟢 NISKI PRIORYTET - Bazowy widget zakładki
│ │ ├── console_widget.py 🟡 ŚREDNI PRIORYTET - Konsola logów, wymaga optymalizacji wydajności
│ │ ├── menu_bar.py 🟢 NISKI PRIORYTET - Pasek menu
│ │ ├── status_bar_manager.py 🟢 NISKI PRIORYTET - Pasek statusu
│ │ ├── tab_one_widget.py 🟢 NISKI PRIORYTET - Zakładka 1
│ │ ├── tab_two_widget.py 🟢 NISKI PRIORYTET - Zakładka 2
│ │ └── tab_three_widget.py 🟢 NISKI PRIORYTET - Zakładka 3
│ └── style_editor/
│ ├── style_editor_app.py 🟢 NISKI PRIORYTET - Edytor stylów QSS
│ ├── style_editor_window.py 🟢 NISKI PRIORYTET - Okno edytora stylów
│ └── ui_showcase_widget.py 🟢 NISKI PRIORYTET - Podgląd UI
├── utils/
│ ├── application_startup.py 🟢 NISKI PRIORYTET - Logika startowa
│ ├── config_cache.py 🟡 ŚREDNI PRIORYTET - Buforowanie konfiguracji
│ ├── enhanced_splash.py 🟢 NISKI PRIORYTET - Rozszerzony splash
│ ├── exceptions.py 🟡 ŚREDNI PRIORYTET - Definicje wyjątków
│ ├── improved_thread_manager.py 🟡 ŚREDNI PRIORYTET - Zarządzanie wątkami
│ ├── logger.py 🟡 ŚREDNI PRIORYTET - System logowania
│ ├── performance_optimizer.py 🟡 ŚREDNI PRIORYTET - Optymalizacje wydajności
│ ├── resource_manager.py 🟡 ŚREDNI PRIORYTET - Zarządzanie zasobami
│ ├── secure_commands.py 🟢 NISKI PRIORYTET - Bezpieczne komendy
│ ├── system_info.py 🟢 NISKI PRIORYTET - Informacje o systemie
│ ├── translation_manager.py 🟡 ŚREDNI PRIORYTET - System tłumaczeń
│ ├── validators.py 🟢 NISKI PRIORYTET - Walidatory
├── translations/
│ ├── pl.json 🟡 ŚREDNI PRIORYTET - Tłumaczenia PL, wymaga walidacji
│ ├── en.json 🟡 ŚREDNI PRIORYTET - Tłumaczenia EN, wymaga walidacji
│ └── texts.md 🟢 NISKI PRIORYTET - Opisy tekstów
├── tests/
│ ├── test_config_manager.py 🟡 ŚREDNI PRIORYTET - Testy konfiguracji
│ ├── test_dependency_injection.py 🟡 ŚREDNI PRIORYTET - Testy DI
│ └── unit/
│ ├── test_mvvm.py 🟡 ŚREDNI PRIORYTET - Testy MVVM
│ └── test_state_management.py 🟡 ŚREDNI PRIORYTET - Testy zarządzania stanem
├── benchmarks/
│ ├── performance_benchmark.py 🟢 NISKI PRIORYTET - Benchmark wydajności
│ ├── test_cupy_benchmark.py 🟢 NISKI PRIORYTET - Testy wydajności GPU
│ └── benchmark_results.json 🟢 NISKI PRIORYTET - Wyniki benchmarków
├── resources/
│ ├── styles.qss 🟢 NISKI PRIORYTET - Style UI
│ └── img/
│ ├── icon.png 🟢 NISKI PRIORYTET - Ikona
│ └── splash.jpg 🟢 NISKI PRIORYTET - Splash
├── scripts/
│ ├── cleanup.py 🟡 ŚREDNI PRIORYTET - Skrypt czyszczący
│ ├── setup_dev.py 🟢 NISKI PRIORYTET - Skrypt deweloperski
│ ├── reset_hardware_profile.bat 🟢 NISKI PRIORYTET - Reset profilu sprzętu (Windows)
│ ├── reset_hardware_profile.sh 🟢 NISKI PRIORYTET - Reset profilu sprzętu (Linux)
│ └── README.md 🟢 NISKI PRIORYTET - Opis skryptów

## Plan analizy do etapu 2

1. Najpierw analizować pliki 🔴 (main_app.py, UI/main_window.py)
2. Następnie pliki 🟡 (główne moduły architektury, testy, tłumaczenia, config, logger, DI, profilowanie, czyszczenie, itp.)
3. Na końcu pliki 🟢 (drobne komponenty, style, dokumentacja, benchmarki, obrazy)

### Grupowanie plików:

- Pliki główne i ich zależności (np. main_app.py + config + logger + DI)
- Komponenty UI razem
- Testy razem
- Pliki tłumaczeń razem

### Szacowany zakres zmian:

- Usunięcie zakomentowanych logów, czyszczenie importów, optymalizacja wydajności, walidacja tłumaczeń, poprawa testów, refaktoryzacja DI i MVVM, optymalizacja zarządzania wątkami, poprawa dokumentacji, spójność stylu kodu.

---

Każdy plik opisany powyżej zostanie szczegółowo przeanalizowany w etapie 2 zgodnie z priorytetami i zależnościami.
