# Teksty interfejsu użytkownika

## Tłumaczenia (translations/)

Wszystkie teksty w plikach tłumaczeń są obsługiwane przez system tłumaczeń.

### pl.json, en.json

- Tytuł aplikacji: "ConceptFab NeuroSorter"
- Menu:
  - Plik/File
  - Edycja/Edit
  - Pomoc/Help
  - Nowy/New
  - Otwórz/Open
  - Zapisz/Save
  - Wyjście/Exit
  - Preferencje/Preferences
  - O programie/About
  - Kopiuj/Copy
  - Profil sprzętowy/Hardware Profiler
  - Konfiguracja profilu sprzętowego/Hardware profile configuration
- Zakładki:
  - Zakładka 1/Tab 1
  - Zakładka 2/Tab 2
  - Zakładka 3/Tab 3
  - Konsola/Console
- Status:
  - Gotowy/Ready
  - Ładowanie.../Loading...
  - Zapisywanie.../Saving...
  - Błąd: {0}/Error: {0}
- Dialogi:
  - Wyjście z aplikacji/Exit Application
  - Czy na pewno chcesz wyjść?/Are you sure you want to exit?
  - Tak/Yes
  - Nie/No
  - Preferencje/Preferences
  - Ogólne/General
  - Logowanie/Logging
  - Pokaż ekran powitalny/Show splash screen
  - Zapamiętaj rozmiar okna/Remember window size
  - Zapisz logi do pliku/Save logs to file
  - Loguj komunikaty UI do konsoli/Log UI messages to console
  - Poziom logowania/Log level
  - Język/Language
  - Zapisz/Save
  - Anuluj/Cancel
  - O programie/About
  - Wersja 1.0/Version 1.0

## UI/main_window.py

✅ Wszystkie teksty są obsługiwane przez system tłumaczeń:

- Tytuł okna (app.title)
- Menu (app.menu.\*)
- Nazwy zakładek (app.tabs.\*)
- Zawartość zakładek (app.tabs.content.\*)
- Pasek statusu (app.status.\*)
- Dialog wyjścia (app.dialogs.exit.\*)

## UI/about_dialog.py

❌ Większość tekstów jest hardkodowana:

- "Moja Zaawansowana Aplikacja PyQt6"
- "Wersja 1.0"
- "Ta aplikacja została stworzona przy użyciu PyQt6.\nJest to aplikacja demo z zaawansowanymi funkcjami UI."
- "OK"

✅ Tylko niektóre teksty są obsługiwane przez tłumaczenia:

- app.dialogs.about.title (tytuł okna)
- app.dialogs.about.version (wersja)
- app.dialogs.about.description (opis)
- app.dialogs.about.ok (przycisk OK)

## UI/hardware_profiler.py

❌ Większość tekstów jest hardkodowana:

- "Hardware Profiler"
- "CPU: Intel Core i7-9700K"
- "RAM: 32GB DDR4"
- "GPU: NVIDIA GeForce RTX 2080"
- "Aktualna konfiguracja sprzętowa"
- "Dostępne optymalizacje"
- "Skanuj sprzęt"

✅ Tylko niektóre teksty są obsługiwane przez tłumaczenia:

- app.dialogs.hardware_profiler.title
- app.dialogs.hardware_profiler.cpu
- app.dialogs.hardware_profiler.ram
- app.dialogs.hardware_profiler.gpu

## UI/components/console_widget.py

❌ Większość tekstów jest hardkodowana:

- "Wyczyść" (przycisk)
- "Zapisz logi" (przycisk)
- "Zapisz logi" (tytuł okna dialogowego)
- "Pliki tekstowe (_.txt);;Wszystkie pliki (_.\*)" (filtry plików)
- "Błąd" (tytuł okna błędu)
- "Nie udało się zapisać logów: {e}" (treść błędu)

✅ Tylko placeholder konsoli jest obsługiwany przez tłumaczenia:

- app.tabs.console.placeholder

## UI/components/tab_one_widget.py

✅ Wszystkie teksty są obsługiwane przez system tłumaczeń:

- app.tabs.content.tab1.content
- app.tabs.content.tab1.button
- app.tabs.content.tab1.placeholder
- app.tabs.content.tab1.text_entered
- app.tabs.content.tab1.nothing_entered

## UI/components/tab_two_widget.py

✅ Wszystkie teksty są obsługiwane przez system tłumaczeń:

- app.tabs.content.tab2.content
- app.tabs.content.tab2.checkbox
- app.tabs.content.tab2.select_value
- app.tabs.content.tab2.checkbox_checked
- app.tabs.content.tab2.checkbox_unchecked
- app.tabs.content.tab2.new_value

## UI/components/tab_three_widget.py

✅ Wszystkie teksty są obsługiwane przez system tłumaczeń:

- app.tabs.content.tab3.content
- app.tabs.content.tab3.placeholder
- app.tabs.content.tab3.show_text
- app.tabs.content.tab3.text_content
- app.tabs.content.tab3.empty_field

## UI/preferences_dialog.py

✅ Wszystkie teksty są obsługiwane przez system tłumaczeń:

- app.dialogs.preferences.title
- app.dialogs.preferences.general
- app.dialogs.preferences.show_splash
- app.dialogs.preferences.remember_window
- app.dialogs.preferences.logging
- app.dialogs.preferences.log_to_file
- app.dialogs.preferences.log_ui
- app.dialogs.preferences.save
- app.dialogs.preferences.cancel

