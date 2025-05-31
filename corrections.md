# Plan Poprawek Projektu Aplikacji

## Streszczenie

Niniejszy dokument przedstawia kompleksowy, etapowy plan poprawek dla projektu \_CFAB_UI_manager, oparty na szczegółowej analizie kodu. Plan obejmuje usunięcie redundancji kodu, wprowadzenie optymalizacji, naprawę błędów i usprawnienia strukturalne przy jednoczesnym zachowaniu istniejącej funkcjonalności.

## Struktura Projektu - Pliki Wymagające Poprawek

```
_CFAB_UI_manager/
├── main_app.py                  🟡 ŚREDNI - Refaktoryzacja, uproszczenie logiki, hardkodowane ścieżki
├── architecture/
│   ├── __init__.py
│   ├── config_management.py
│   ├── dependency_injection.py
│   ├── mvvm.py
│   ├── state_management.py
├── benchmarks/
│   ├── performance_benchmark.py
├── scripts/
│   ├── cleanup.py
│   ├── setup_dev.py
├── UI/
│   ├── about_dialog.py
│   ├── hardware_profiler.py
│   ├── main_window.py
│   ├── preferences_dialog.py
│   ├── progress_controller.py
│   ├── splash_screen.py
│   ├── components/
│   │   ├── base_tab_widget.py
│   │   ├── console_widget.py
│   │   ├── menu_bar.py
│   │   ├── status_bar_manager.py
│   │   ├── tab_one_widget.py
│   │   ├── tab_three_widget.py
│   │   ├── tab_two_widget.py
│   ├── style_editor/
│   │   ├── style_editor_app.py
│   │   ├── style_editor_window.py
│   │   ├── ui_showcase_widget.py
├── utils/
│   ├── __init__.py
│   ├── application_startup.py
│   ├── config_cache.py
│   ├── enhanced_splash.py
│   ├── exceptions.py
│   ├── improved_thread_manager.py
│   ├── logger.py                  🟡 ŚREDNI - Uproszczenie, możliwe duplikacje, hardkodowane teksty
│   ├── performance_optimizer.py
│   ├── resource_manager.py
│   ├── secure_commands.py
│   ├── system_info.py
│   ├── translation_manager.py
│   ├── validators.py
```

## Plan Etapowy Poprawek

### Etap 1: Refaktoryzacja Głównej Aplikacji (`main_app.py`)

**Priorytet: ŚREDNI**
**Szacowany Czas: 3-4 godziny**
**Poziom Ryzyka: ŚREDNI**

#### Pliki do Modyfikacji:

- `main_app.py` - Główny plik aplikacji
- `utils/application_startup.py` - (Zależność) Może wymagać dostosowania interfejsu
- `UI/main_window.py` - (Zależność) Sposób przekazywania konfiguracji i loggera
- `config.json` - (Zależność) Weryfikacja spójności kluczy konfiguracyjnych

#### Poprawki Etapu 1:

##### 1.1 Uproszczenie Logiki Inicjalizacji w `main_app.py`

**Plik:** `main_app.py`
**Opis zmian:**
Obecna inicjalizacja w `if __name__ == "__main__":` jest długa i zawiera logikę, która mogłaby być lepiej enkapsulowana w klasie `Application` lub `ApplicationStartup`. Należy przenieść część logiki związaną z tworzeniem ścieżek, ładowaniem ikon, inicjalizacją `MainWindow` oraz `SplashScreen` do odpowiednich metod klasy `Application`. Dodatkowo, hardkodowane ścieżki do zasobów (`icon.png`, `splash.jpg`) powinny być zarządzane przez `ResourceManager` lub konfigurację.

**Znalezione Problemy:**

- Hardkodowane ścieżki do zasobów (np. `icon_path`, `splash_path`).
- Bezpośrednie manipulowanie `sys.argv` w bloku `if __name__ == "__main__":`.
- Logika tworzenia `MainWindow` i `SplashScreen` mogłaby być częścią metody `Application.run()` lub podobnej.
- Symulacja postępu ładowania w `SplashScreen` jest statyczna i może nie odzwierciedlać rzeczywistego postępu.

**Proponowane Zmiany:**

1.  Przenieść logikę tworzenia ścieżek do zasobów do `ResourceManager` lub pobierać je z konfiguracji.
2.  Stworzyć metodę `Application.run()` która enkapsuluje logikę startową po `app.initialize()`.
3.  Uczynić `startup_tasks` dla `SplashScreen` bardziej dynamicznymi lub konfigurowalnymi.
4.  Rozważyć użycie `app.config` do przechowywania ścieżek do zasobów zamiast `os.path.join` w `main_app.py`.

**Kod finalny (fragment - koncepcja):**

```python
# main_app.py

class Application(QApplication):
    # ... (istniejący kod) ...

    def run(self):
        """Uruchamia główną pętlę aplikacji i inicjalizuje UI."""
        if not self.initialize():
            sys.exit(1)

        icon_path = self.resource_manager.get_image_path("icon.png") # Przykład
        self.setWindowIcon(QIcon(icon_path))

        self.main_win = MainWindow(
            app_logger=self.app_logger if hasattr(self, "app_logger") else None
        )
        self.main_win.setWindowIcon(QIcon(icon_path))
        self.main_win.preferences = self.config

        if self.config.get("show_splash", True):
            splash_path = self.resource_manager.get_image_path("splash.jpg") # Przykład
            startup_tasks = [
                "Loading configuration", # TODO: Powiązać z rzeczywistymi zdarzeniami
                # ... inne zadania ...
            ]
            splash, progress_tracker = create_optimized_splash(
                image_path=splash_path, startup_tasks=startup_tasks, window_size=(642, 250)
            )
            # ... (logika splash screen) ...
            splash.startup_completed.connect(self.main_win.show)
        else:
            self.main_win.show()

        # ... (reszta logiki, np. performance monitor) ...
        return self.exec()

if __name__ == "__main__":
    app = Application(sys.argv)
    exit_code = app.run()
    sys.exit(exit_code)
```

**Checklista zależności:**

- [ ] `utils/resource_manager.py`: Dodanie metody `get_image_path(image_name)` lub podobnej.
- [ ] `UI/main_window.py`: Weryfikacja przekazywania `app_logger` i `preferences`.
- [ ] `utils/application_startup.py`: Sprawdzenie, czy zmiany w `Application` nie wpływają na logikę `ApplicationStartup`.
- [ ] `config.json`: Rozważenie dodania ścieżek do zasobów.

**Plan testów:**

1.  Uruchomienie aplikacji - sprawdzenie, czy startuje poprawnie.
2.  Weryfikacja wyświetlania ikony aplikacji.
3.  Weryfikacja działania SplashScreen (jeśli włączony).
4.  Sprawdzenie, czy `MainWindow` otrzymuje konfigurację i logger.
5.  Test zamknięcia aplikacji i poprawnego czyszczenia zasobów.

**Status tracking:**

- [ ] Analiza ukończona
- [ ] Implementacja zmian
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Code review
- [ ] Zakończone

##### 1.2 Użycie stałych dla kluczy konfiguracyjnych

**Plik:** `main_app.py` (i inne pliki korzystające z `app.config`)
**Opis zmian:**
W kodzie wielokrotnie pojawiają się bezpośrednie odwołania do kluczy słownika `config` jako stringi (np. `"show_splash"`, `"log_level"`). Może to prowadzić do błędów przy literówkach i utrudnia refaktoryzację. Zaleca się zdefiniowanie stałych dla tych kluczy.

**Znalezione Problemy:**

- Użycie stringów jako kluczy konfiguracyjnych (np. `app.config.get("show_splash", True)`).

**Proponowane Zmiany:**

1.  Stworzyć moduł (np. `config_keys.py`) lub sekcję w istniejącym module konfiguracyjnym, gdzie zdefiniowane będą stałe dla kluczy.
    ```python
    # config_keys.py (przykład)
    KEY_SHOW_SPLASH = "show_splash"
    KEY_LOG_LEVEL = "log_level"
    # ... inne klucze
    ```
2.  Zastąpić stringi w kodzie odwołaniami do tych stałych.
    ```python
    # main_app.py (przykład użycia)
    # from config_keys import KEY_SHOW_SPLASH
    # if app.config.get(KEY_SHOW_SPLASH, True):
    ```

**Kod finalny (fragment - koncepcja):**

```python
# W odpowiednim miejscu, np. w utils/config_management.py lub nowym pliku config_constants.py
class ConfigKeys:
    SHOW_SPLASH = "show_splash"
    LOG_TO_FILE = "log_to_file"
    LOG_UI_TO_CONSOLE = "log_ui_to_console"
    LOG_LEVEL = "log_level"
    LOG_DIR = "log_dir"
    # ... inne klucze

# W main_app.py
# from utils.config_management import ConfigKeys # Załóżmy, że tam są klucze

# ...
        self._config = {
            ConfigKeys.SHOW_SPLASH: True,
            ConfigKeys.LOG_TO_FILE: False,
            ConfigKeys.LOG_UI_TO_CONSOLE: False,
            ConfigKeys.LOG_LEVEL: "INFO",
        }
# ...
    if app.config.get(ConfigKeys.SHOW_SPLASH, True):
        # ...
```

**Checklista zależności:**

- [ ] Wszystkie pliki odczytujące konfigurację (np. `utils/logger.py`, `utils/application_startup.py`).

**Plan testów:**

1.  Uruchomienie aplikacji i sprawdzenie, czy konfiguracja jest poprawnie odczytywana i stosowana.
2.  Zmiana wartości w `config.json` i weryfikacja, czy aplikacja reaguje zgodnie z oczekiwaniami.

**Status tracking:**

- [ ] Analiza ukończona
- [ ] Implementacja zmian
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Code review
- [ ] Zakończone

---

### Etap 2: Refaktoryzacja Modułu Logowania (`utils/logger.py`)

**Priorytet: ŚREDNI**
**Szacowany Czas: 2-3 godziny**
**Poziom Ryzyka: NISKI**

#### Pliki do Modyfikacji:

- `utils/logger.py` - Główny plik modułu logowania
- Pliki korzystające z `AppLogger` (np. `main_app.py`, `utils/application_startup.py`) - weryfikacja interfejsu

#### Poprawki Etapu 2:

##### 2.1 Uproszczenie i Potencjalne Usunięcie Duplikacji w `AppLogger.cleanup()`

**Plik:** `utils/logger.py`
**Opis zmian:**
W klasie `AppLogger` znajdują się dwie metody `cleanup()`. Jedna z nich jest prawdopodobnie nadmiarowa lub powinna być połączona.

**Znalezione Problemy:**

- Dwie metody `cleanup()` w klasie `AppLogger`. Jedna na końcu klasy, druga wcześniej.

**Proponowane Zmiany:**

1.  Zweryfikować, która metoda `cleanup()` jest rzeczywiście używana i czy obie są potrzebne.
2.  Jeśli jedna jest nadmiarowa, usunąć ją. Jeśli obie mają różne cele, zmienić nazwę jednej z nich dla jasności. Wydaje się, że ostatnia metoda `cleanup` jest tą właściwą, a wcześniejsza (pusta) jest pozostałością.

**Kod finalny (fragment - po usunięciu jednej z metod):**

```python
# utils/logger.py

class AppLogger:
    # ... (istniejący kod) ...

    # Usunięto pierwszą, pustą metodę cleanup()

    def setup_logger(self):
        # ... (istniejący kod) ...

    def set_console_widget_handler(self, handler_method, formatter=None):
        # ... (istniejący kod) ...

    def debug(self, message):
        self.async_logger.log(logging.DEBUG, message)

    def info(self, message):
        self.async_logger.log(logging.INFO, message)

    def warning(self, message):
        self.async_logger.log(logging.WARNING, message)

    def error(self, message):
        self.async_logger.log(logging.ERROR, message)

    # Pozostaje tylko ta metoda cleanup
    def cleanup(self):
        """
        Zatrzymuje asynchroniczny logger i czyści zasoby.
        """
        if self.async_logger: # Dodano sprawdzenie, czy async_logger istnieje
            self.async_logger.stop()
            # Dodatkowe logowanie na koniec, jeśli logger jeszcze działa
            # Należy upewnić się, że getLogger nie tworzy nowego loggera, jeśli stary jest już zamknięty
            # Można rozważyć logowanie bezpośrednio przez self.async_logger.logger przed jego zatrzymaniem
            # lub użycie standardowego logging, jeśli AppLogger jest już "martwy"
            # logging.getLogger("AppLogger").info("AppLogger terminated correctly.") # To może być problematyczne
            print("AppLogger terminated correctly.") # Bezpieczniejsza opcja po zatrzymaniu wątku loggera
```

**Checklista zależności:**

- [ ] Miejsca wywołania `app_logger.cleanup()` (np. w `main_app.py` przy `app.aboutToQuit.connect(app.cleanup)` - upewnić się, że `app.cleanup` wywołuje właściwą metodę `AppLogger.cleanup`).

**Plan testów:**

1.  Uruchomienie i zamknięcie aplikacji, obserwacja logów (jeśli są włączone) lub konsoli w poszukiwaniu komunikatów o poprawnym zakończeniu pracy loggera.
2.  Sprawdzenie, czy nie ma błędów związanych z zamykaniem loggera.

**Status tracking:**

- [ ] Analiza ukończona
- [ ] Implementacja zmian
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Code review
- [ ] Zakończone

##### 2.2 Hardkodowane Komunikaty Logów w `AsyncLogger`

**Plik:** `utils/logger.py`
**Opis zmian:**
Klasa `AsyncLogger` zawiera hardkodowane komunikaty logów w języku polskim (np. "AsyncLogger: Próba przetworzenia logu dla UI..."). Te komunikaty, jeśli mają być widoczne dla użytkownika lub w logach systemowych, powinny być zarządzane przez system tłumaczeń lub być w języku angielskim jako standard.

**Znalezione Problemy:**

- Hardkodowane komunikaty w języku polskim w `AsyncLogger._process_logs()`:
  - `f"AsyncLogger: Próba przetworzenia logu dla UI. Handler: {self._console_widget_handler}"`
  - `f"AsyncLogger: Wysyłanie sformatowanego logu do UI: {formatted_message[:100]}..."`
  - `f"AsyncLogger: Błąd w handlerze konsoli UI: {e}"`
  - `f"AsyncLogger: Typ handlera: {type(self._console_widget_handler)}, Handler: {self._console_widget_handler}"`
  - `"AsyncLogger: Brak handlera konsoli UI."`
  - `f"AsyncLogger: Krytyczny błąd w pętli przetwarzania logów: {e}"`

**Proponowane Zmiany:**

1.  Zmienić te komunikaty na język angielski, jako że są to logi wewnętrzne modułu.
2.  Jeśli którykolwiek z tych komunikatów miałby potencjalnie trafić do użytkownika (co jest mało prawdopodobne dla logów DEBUG/CRITICAL z `AsyncLogger`), należałoby rozważyć ich obsługę przez system tłumaczeń. Na ten moment, zmiana na angielski wydaje się wystarczająca.

**Kod finalny (fragment - koncepcja):**

```python
# utils/logger.py

class AsyncLogger:
    # ... (istniejący kod) ...
    def _process_logs(self):
        while True:
            try:
                level, message_or_record = self.queue.get()
                if level is None:
                    break

                # ... (reszta logiki) ...

                self.logger.log(
                    logging.DEBUG,
                    f"AsyncLogger: Attempting to process log for UI. Handler: {self._console_widget_handler}",
                )

                if self._console_widget_handler:
                    try:
                        formatted_message = self._formatter.format(record)
                        self.logger.log(
                            logging.DEBUG,
                            f"AsyncLogger: Sending formatted log to UI: {formatted_message[:100]}...",
                        )
                        self._console_widget_handler(formatted_message)
                    except Exception as e:
                        self.logger.log(
                            logging.CRITICAL,
                            f"AsyncLogger: Error in UI console handler: {e}",
                            exc_info=True,
                        )
                        self.logger.log(
                            logging.DEBUG,
                            f"AsyncLogger: Handler type: {type(self._console_widget_handler)}, Handler: {self._console_widget_handler}",
                        )
                else:
                    self.logger.log(
                        logging.DEBUG, "AsyncLogger: No UI console handler set."
                    )

                self.queue.task_done()
            except Exception as e:
                self.logger.log(
                    logging.CRITICAL,
                    f"AsyncLogger: Critical error in log processing loop: {e}",
                    exc_info=True,
                )
                time.sleep(0.1)
    # ... (reszta klasy) ...
```

**Checklista zależności:**

- Brak bezpośrednich zależności, zmiana dotyczy wewnętrznych komunikatów loggera.

**Plan testów:**

1.  Uruchomienie aplikacji z poziomem logowania DEBUG.
2.  Sprawdzenie logów (plik lub konsola systemowa) w poszukiwaniu nowych, angielskich komunikatów z `AsyncLogger`.
3.  Weryfikacja, czy logowanie do konsoli UI (jeśli zaimplementowane i używane) nadal działa poprawnie.

**Status tracking:**

- [ ] Analiza ukończona
- [ ] Implementacja zmian
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Code review
- [ ] Zakończone

---

### Etap 3: Analiza Okna Informacyjnego (`UI/about_dialog.py`)

**Priorytet: NISKI**
**Szacowany Czas: 1 godzina**
**Poziom Ryzyka: NISKI**

#### Pliki do Modyfikacji:

- `UI/about_dialog.py` - Główny plik okna dialogowego
- `translations/en.json`, `translations/pl.json` - Pliki tłumaczeń (weryfikacja kluczy)

#### Poprawki Etapu 3:

##### 3.1 Weryfikacja Kluczy Tłumaczeń i Potencjalne Informacje Dynamiczne

**Plik:** `UI/about_dialog.py`
**Opis zmian:**
Obecnie `AboutDialog` poprawnie używa `TranslationManager` do wyświetlania tekstów. Należy jednak zweryfikować, czy wszystkie używane klucze tłumaczeń (`app.dialogs.about.title`, `app.dialogs.about.version`, `app.dialogs.about.description`, `app.dialogs.about.ok`) istnieją w plikach `en.json` i `pl.json` oraz czy ich wartości są odpowiednie. Dodatkowo, informacja o wersji jest pobierana przez klucz `app.dialogs.about.version`. Warto rozważyć, czy wersja aplikacji nie powinna być pobierana dynamicznie, np. z pliku konfiguracyjnego, zmiennej globalnej ustawianej podczas budowania aplikacji lub bezpośrednio z metadanych pakietu (jeśli aplikacja jest pakietowana).

**Znalezione Problemy:**

- Teksty są pobierane przez `TranslationManager`, co jest dobrą praktyką.
- Wersja aplikacji jest prawdopodobnie statycznym tekstem w plikach tłumaczeń.

**Proponowane Zmiany:**

1.  **Weryfikacja kluczy tłumaczeń:** Sprawdzić istnienie i poprawność wartości dla kluczy:
    - `app.dialogs.about.title`
    - `app.dialogs.about.version`
    - `app.dialogs.about.description`
    - `app.dialogs.about.ok`
      w plikach `translations/en.json` i `translations/pl.json`.
2.  **Dynamiczne ładowanie wersji (Opcjonalnie/Zalecane):**
    - Rozważyć przechowywanie numeru wersji w centralnym miejscu (np. `config.json` lub dedykowany plik `version.py`).
    - Zmodyfikować `AboutDialog`, aby odczytywał wersję z tego centralnego miejsca.
    - Klucz `app.dialogs.about.version` w plikach tłumaczeń mógłby wtedy zawierać tylko etykietę, np. "Wersja: {version_number}" lub "Version: {version_number}", a sama wartość wersji byłaby wstawiana dynamicznie.
    - Alternatywnie, jeśli wersja ma pozostać w plikach tłumaczeń, upewnić się, że proces aktualizacji wersji aplikacji obejmuje również aktualizację tych plików.

**Kod finalny (fragment - koncepcja dynamicznego ładowania wersji):**

```python
# UI/about_dialog.py
# Załóżmy, że wersja jest dostępna np. poprzez app.config lub dedykowany moduł
# from main_app import APP_VERSION # Przykładowo, jeśli wersja jest globalna
# lub
# app_instance = QApplication.instance()
# app_version = app_instance.config.get("application_version", "N/A")

class AboutDialog(QDialog):
    def __init__(self, parent=None, app_version="N/A"):
        super().__init__(parent)
        # ... (istniejący kod) ...

        # Wersja
        version_text_template = TranslationManager.translate("app.dialogs.about.version_template") # np. "Wersja: {}"
        self.version_label = QLabel(version_text_template.format(app_version))
        layout.addWidget(self.version_label)

        # ... (istniejący kod) ...

    def update_translations(self, app_version="N/A"):
        # ... (istniejący kod) ...
        version_text_template = TranslationManager.translate("app.dialogs.about.version_template")
        self.version_label.setText(version_text_template.format(app_version))
        # ... (istniejący kod) ...

# W miejscu tworzenia dialogu:
# app_version = get_current_app_version() # Funkcja do pobrania wersji
# dialog = AboutDialog(self, app_version=app_version)
# dialog.exec()
```

**Checklista zależności:**

- [ ] `translations/en.json`: Weryfikacja/dodanie klucza `app.dialogs.about.version_template` (jeśli wybrano opcję dynamicznej wersji).
- [ ] `translations/pl.json`: Weryfikacja/dodanie klucza `app.dialogs.about.version_template` (jeśli wybrano opcję dynamicznej wersji).
- [ ] Miejsce przechowywania wersji aplikacji (np. `config.json`, dedykowany plik/moduł).
- [ ] Logika przekazywania aktualnej wersji do `AboutDialog`.

**Plan testów:**

1.  Otwarcie okna "O programie" - sprawdzenie poprawności wyświetlanych tekstów (tytuł, opis, przycisk OK) w obu językach.
2.  Weryfikacja wyświetlania numeru wersji (czy jest aktualny i poprawnie sformatowany).
3.  Jeśli zaimplementowano dynamiczne ładowanie wersji: zmiana numeru wersji w źródle i ponowne uruchomienie aplikacji, aby sprawdzić, czy okno "O programie" pokazuje nową wersję.

**Status tracking:**

- [ ] Analiza ukończona
- [ ] Implementacja zmian (opcjonalnie dla dynamicznej wersji)
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Code review
- [ ] Zakończone

---
