# Mapa Projektu CFAB UI Manager

## Legenda

```
┌────────────────────┐      Plik kluczowy (niezbędny do działania aplikacji)
│                    │
└────────────────────┘

┌────────────────────┐      Plik pomocniczy (ważny, ale nie niezbędny)
│                    │
└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘

┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐      Plik testowy lub tymczasowy
┊                    ┊      (nieistotny z punktu widzenia funkcjonowania)
└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘

┌───────────────────┐       Folder zawierający ważne komponenty
│                   │
│    folder/        ├───────▶ Strzałka wskazuje zależność lub relację
│                   │
└───────────────────┘
```

## Struktura Główna Aplikacji

```
┌────────────────────┐
│    main_app.py     │◄───────────────┐
└────────────────────┘                │
          │                           │
          ▼                           │
┌────────────────────┐      ┌─────────────────┐
│  UI/main_window.py │───►  │ config.json     │
└────────────────────┘      └─────────────────┘
          │
          │
    ┌─────┴──────┬─────────────┬─────────────────┬─────────────┐
    │            │             │                 │             │
    ▼            ▼             ▼                 ▼             ▼
┌─────────┐ ┌─────────┐  ┌─────────────┐  ┌─────────────┐ ┌─────────────┐
│Tab One  │ │Tab Two  │  │Tab Three    │  │About Dialog │ │Preferences  │
│Widget   │ │Widget   │  │Widget       │  │             │ │Dialog       │
└─────────┘ └─────────┘  └─────────────┘  └─────────────┘ └─────────────┘
```

## System Identyfikacji Sprzętu

```
┌────────────────────┐      ┌─────────────────────┐
│    main_app.py     │      │UI/hardware_profiler │
└────────────────────┘      └─────────────────────┘
         │                             │
         └─────────────┬───────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │utils/system_info│
              └─────────────────┘
                       │
                       ▼
             ┌──────────────────────┐
             │  get_stable_uuid()   │
             └──────────────────────┘
                       │
         ┌────────────┴────────────┐
         ▼                         ▼
┌─────────────────┐       ┌─────────────────────┐
│   LRU Cache     │       │  Generowanie UUID   │
│ (Szybki dostęp) │       │  (Pierwsze użycie)  │
└─────────────────┘       └─────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │   hardware.json     │
                          └─────────────────────┘
```

## Moduły Utils - Kluczowe Komponenty

```
┌────────────────────────┐
│                        │
│      main_app.py       │
│                        │
└────────────────────────┘
        │     │     │
┌───────┘     │     └───────┐
│             │             │
▼             ▼             ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│utils/system_info│ │utils/exceptions│ │utils/logger   │
└────────────────┘ └────────────────┘ └────────────────┘
        │             │                      │
┌───────┘             │                      │
│                     │                      │
▼                     ▼                      ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│secure_commands │ │thread_manager  │ │translation_    │
│                │ │                │ │manager         │
└────────────────┘ └────────────────┘ └────────────────┘
                                              │
                                              ▼
                                      ┌────────────────┐
                                      │translator      │
                                      │                │
                                      └────────────────┘
```

## System Interfejsu Użytkownika

```
┌────────────────────┐
│                    │
│    main_app.py     │
│                    │
└────────────────────┘
          │
          │
          ▼
┌────────────────────┐      ┌────────────────────┐
│UI/splash_screen.py │─────►│utils/enhanced_splash│
└────────────────────┘      └────────────────────┘
          │
          │
          ▼
┌────────────────────────────────────────────────┐
│                UI/main_window.py               │
└────────────────────────────────────────────────┘
   │           │            │            │
   │           │            │            │
   ▼           ▼            ▼            ▼
┌─────────┐┌─────────┐┌────────────┐┌─────────────┐
│components│UI/      ││components/  ││components/  │
│tab_one   │hardware ││tab_two      ││tab_three    │
│widget    │profiler ││widget       ││widget       │
└─────────┘└─────────┘└────────────┘└─────────────┘
```

## Pliki Zasobów i Konfiguracji

```
┌──────────────────────────────┐
│                              │
│         main_app.py          │
│                              │
└──────────────────────────────┘
  │           │            │
  │           │            │
  ▼           ▼            ▼
┌─────────┐┌─────────┐┌────────────────┐
│config.  ││hardware.││resources/       │
│json     ││json     ││styles.qss      │
└─────────┘└─────────┘└────────────────┘
                          │
                          │
                          ▼
                     ┌────────────────┐
                     │resources/img/  │
                     │splash.jpg      │
                     │icon.png        │
                     └────────────────┘
```

## Pliki Testowe i Tymczasowe

```
┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
┊                                             ┊
┊                  tests/                     ┊
┊                                             ┊
└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
   │           │                  │           │
   │           │                  │           │
   ▼           ▼                  ▼           ▼
┌╌╌╌╌╌╌╌╌┐ ┌╌╌╌╌╌╌╌╌╌╌┐  ┌╌╌╌╌╌╌╌╌╌╌╌┐ ┌╌╌╌╌╌╌╌╌╌╌┐
┊test_    ┊ ┊test_      ┊  ┊test_       ┊ ┊debug_     ┊
┊system_  ┊ ┊integration┊  ┊performance_┊ ┊import.py  ┊
┊info.py  ┊ ┊.py        ┊  ┊optimization┊ ┊           ┊
└╌╌╌╌╌╌╌╌┘ └╌╌╌╌╌╌╌╌╌╌┘  └╌╌╌╌╌╌╌╌╌╌╌┘ └╌╌╌╌╌╌╌╌╌╌┘

┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
┊                                             ┊
┊                benchmarks/                  ┊
┊                                             ┊
└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
          │                       │
          │                       │
          ▼                       ▼
┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐   ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
┊performance_       ┊   ┊benchmark_          ┊
┊benchmark.py       ┊   ┊results.json        ┊
└╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘   └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
```

## Architektura Aplikacji

```
┌────────────────────┐
│                    │
│    main_app.py     │
│                    │
└────────────────────┘
          │
     ┌────┴────┐
     │         │
     ▼         ▼
┌─────────┐ ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐
│architec-│ ┊docs/          ┊
│ture/    │ ┊(Dokumentacja) ┊
└─────────┘ └╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘
     │
     │
┌────┼────┬────────┬────────┐
│    │    │        │        │
▼    ▼    ▼        ▼        ▼
┌─────────┐┌─────┐┌─────┐┌──────┐
│config_  ││mvvm ││state││depen-│
│manage-  ││     ││mana-││dency_│
│ment.py  ││     ││ger  ││injec-│
└─────────┘└─────┘└─────┘│tion  │
                         └──────┘
```

## Pełna Lista Plików Niezbędnych i Pomocniczych

### Pliki Niezbędne (Kluczowe)

```
main_app.py
config.json
hardware.json
UI/main_window.py
UI/splash_screen.py
UI/components/tab_one_widget.py
UI/components/tab_two_widget.py
UI/components/tab_three_widget.py
UI/components/console_widget.py
UI/components/menu_bar.py
UI/components/status_bar_manager.py
UI/hardware_profiler.py
utils/system_info.py
utils/enhanced_splash.py
utils/exceptions.py
utils/improved_thread_manager.py
utils/logger.py
utils/performance_optimizer.py
utils/secure_commands.py
utils/translation_manager.py
utils/translator.py
utils/validators.py
resources/styles.qss
resources/img/icon.png
resources/img/splash.jpg
translations/en.json
translations/pl.json
```

### Pliki Pomocnicze (Ważne, ale nie niezbędne)

```
architecture/config_management.py
architecture/dependency_injection.py
architecture/mvvm.py
architecture/state_management.py
UI/preferences_dialog.py
UI/about_dialog.py
UI/progress_controller.py
utils/thread_manager.py
utils/config_cache.py
```

### Pliki Testowe i Tymczasowe

```
uuid_debug.txt
tests/ (wszystkie pliki)
benchmarks/ (wszystkie pliki)
scripts/ (wszystkie pliki)
docs/ (wszystkie pliki)
__pycache__/ (wszystkie pliki)
UI/__pycache__/ (wszystkie pliki)
UI/components/__pycache__/ (wszystkie pliki)
utils/__pycache__/ (wszystkie pliki)
```
