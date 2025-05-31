<!-- filepath: c:\_cloud\_CFAB_UI_manager\corrections.md -->

# Plan Poprawek Projektu Aplikacji \_CFAB_UI_manager

## Streszczenie

Niniejszy dokument przedstawia kompleksowy, etapowy plan poprawek dla projektu aplikacji \_CFAB_UI_manager, oparty na szczegółowej analizie kodu. Plan obejmuje usunięcie redundancji kodu, wprowadzenie optymalizacji, naprawę błędów i usprawnienia strukturalne przy jednoczesnym zachowaniu istniejącej funkcjonalności.

## Struktura Projektu - Pliki Wymagające Poprawek

```
_CFAB_UI_manager/
├── main_app.py                       🔴 WYSOKI PRIORYTET - Główny plik, refaktoryzacja, integracja
├── architecture/
│   ├── __init__.py                   🟢 NISKI - Oczekuje na analizę
│   ├── config_management.py          🟢 NISKI - Oczekuje na analizę
│   ├── dependency_injection.py       🟢 NISKI - Oczekuje na analizę
│   ├── mvvm.py                       🟢 NISKI - Oczekuje na analizę
│   └── state_management.py           🟢 NISKI - Oczekuje na analizę
├── benchmarks/
│   └── performance_benchmark.py      🟢 NISKI - Oczekuje na analizę
├── scripts/
│   ├── cleanup.py                    🟢 NISKI - Oczekuje na analizę
│   └── setup_dev.py                  🟢 NISKI - Oczekuje na analizę
├── UI/
│   ├── about_dialog.py               🟢 NISKI - Oczekuje na analizę
│   ├── hardware_profiler.py          🟢 NISKI - Oczekuje na analizę
│   ├── main_window.py                🟡 ŚREDNI - Integracja z nowymi serwisami (logger, config)
│   ├── preferences_dialog.py         🟢 NISKI - Oczekuje na analizę
│   ├── progress_controller.py        🟢 NISKI - Oczekuje na analizę
│   ├── splash_screen.py              🟡 ŚREDNI - Potencjalna refaktoryzacja lub zastąpienie
│   ├── components/
│   │   ├── base_tab_widget.py        🟢 NISKI - Oczekuje na analizę
│   │   ├── console_widget.py         🟢 NISKI - Oczekuje na analizę
│   │   ├── menu_bar.py               🟢 NISKI - Oczekuje na analizę
│   │   ├── status_bar_manager.py     🟢 NISKI - Oczekuje na analizę
│   │   ├── tab_one_widget.py         🟢 NISKI - Oczekuje na analizę
│   │   ├── tab_three_widget.py       🟢 NISKI - Oczekuje na analizę
│   │   └── tab_two_widget.py         🟢 NISKI - Oczekuje na analizę
│   └── style_editor/
│       ├── style_editor_app.py       🟢 NISKI - Oczekuje na analizę
│       ├── style_editor_window.py    🟢 NISKI - Oczekuje na analizę
│       └── ui_showcase_widget.py     🟢 NISKI - Oczekuje na analizę
└── utils/
    ├── __init__.py                   🟢 NISKI - Oczekuje na analizę
    ├── application_startup.py        🔴 WYSOKI PRIORYTET - Sekwencja startowa, integracja postępu
    ├── config_cache.py               🟡 ŚREDNI PRIORYTET - Mechanizm cache, serializacja, lokalizacja
    ├── enhanced_splash.py            🟡 ŚREDNI PRIORYTET - Logika splash screena, integracja postępu
    ├── exceptions.py                 🟡 ŚREDNI PRIORYTET - Standaryzacja wyjątków, spójne logowanie
    ├── improved_thread_manager.py    🔴 WYSOKI PRIORYTET - Zarządzanie wątkami, usunięcie LogQueue
    ├── logger.py                     🔴 WYSOKI PRIORYTET - Centralny system logowania, rekonfiguracja
    ├── performance_optimizer.py      🟡 ŚREDNI - Wsparcie optymalizacji, integracja
    ├── resource_manager.py           🟡 ŚREDNI PRIORYTET - Zarządzanie zasobami, konfiguracja ścieżek
    ├── secure_commands.py            🟢 NISKI - Oczekuje na analizę
    ├── system_info.py                🟢 NISKI - Oczekuje na analizę
    ├── translation_manager.py        🟡 ŚREDNI - Kluczowy dla i18n, integracja z AppLogger
    └── validators.py                 🟡 ŚREDNI - Walidacja konfiguracji i danych
```

## Plan Etapowy Poprawek

### Etap 1: Analiza `main_app.py`

**Priorytet:** WYSOKI
**Szacowany Czas:** 1-2 godziny
**Poziom Ryzyka:** ŚREDNI (zmiany w głównym pliku aplikacji)

#### Pliki do Modyfikacji:

- `main_app.py` - Główny plik aplikacji

#### Poprawki Etapu 1:

##### 1.1 Refaktoryzacja i Uporządkowanie `main_app.py`

**Plik:** `main_app.py`

**Znalezione Problemy:**

1.  **Hardkodowane ścieżki**: Ścieżki do zasobów (ikona, splash screen) są budowane z użyciem `os.path.join` i `os.path.dirname(__file__)`. Lepszym podejściem byłoby użycie dedykowanej klasy lub funkcji do zarządzania zasobami, aby uniknąć powtarzania tego wzorca i ułatwić zarządzanie ścieżkami w przyszłości (np. jeśli struktura folderów ulegnie zmianie).
2.  **Domyślna konfiguracja w `Application.__init__`**: Domyślna konfiguracja jest zdefiniowana bezpośrednio w konstruktorze klasy `Application`. Może to być przeniesione do stałych lub do pliku konfiguracyjnego, jeśli nie jest tam jeszcze w pełni zarządzane.
3.  **Symulacja postępu w splash screen**: Logika symulująca postęp ładowania (`progress_tracker.start_task`, `progress_tracker.complete_task`) jest wykonana sekwencyjnie i natychmiastowo. W rzeczywistej aplikacji postęp powinien być aktualizowany dynamicznie w miarę wykonywania rzeczywistych zadań inicjalizacyjnych. Obecna implementacja nie odzwierciedla faktycznego postępu.
4.  **Potencjalne problemy z `sys.exit(app.exec())`**: Chociaż jest to standardowy sposób uruchamiania aplikacji PyQt, warto upewnić się, że wszystkie operacje czyszczące (np. `app.cleanup`) są poprawnie wywoływane przed zakończeniem procesu, zwłaszcza w przypadku nieoczekiwanych błędów. Sygnał `aboutToQuit` jest dobrym miejscem na to.
5.  **Mieszanie odpowiedzialności**: Klasa `Application` zajmuje się zarówno logiką aplikacji (inicjalizacja, konfiguracja), jak i elementami UI (splash screen). Można by rozważyć wydzielenie logiki UI do osobnych komponentów.
6.  **Komentarze i dokumentacja**: Niektóre fragmenty kodu mogłyby skorzystać na dodatkowych komentarzach wyjaśniających działanie lub cel danego bloku. Docstringi są obecne, co jest dobre.
7.  **Obsługa błędów**: W bloku `if __name__ == \"__main__\":` błąd inicjalizacji `app.initialize()` powoduje `sys.exit(1)`. Warto upewnić się, że użytkownik otrzymuje czytelną informację o błędzie krytycznym. `ApplicationStartup` loguje błąd, ale może być potrzebne dodatkowe powiadomienie UI.
8.  **Zarządzanie `app_logger`**: Instancja `app_logger` jest przekazywana do `MainWindow`. Należy upewnić się, że jest to spójne i że logger jest dostępny tam, gdzie jest potrzebny. Przekazywanie przez konstruktor jest jednym z podejść.

**Proponowane Poprawki:**

1.  **Zarządzanie zasobami**:
    - Stworzyć lub wykorzystać istniejący `ResourceManager` (jeśli `utils.resource_manager.py` za to odpowiada) do pobierania ścieżek do zasobów (ikony, obrazy, style).
    - Przykład: `icon_path = self.resource_manager.get_icon_path(\"icon.png\")`
2.  **Konfiguracja domyślna**:
    - Przenieść domyślne wartości konfiguracji do stałych na poziomie modułu lub do dedykowanej sekcji w `config.json` (jeśli to możliwe i sensowne dla tych konkretnych wartości).
3.  **Splash screen i postęp**:
    - Zintegrować aktualizację postępu z rzeczywistymi operacjami ładowania. Każdy krok inicjalizacji powinien emitować sygnał lub wywoływać metodę aktualizującą `progress_tracker`.
    - Rozważyć asynchroniczne ładowanie zasobów, aby UI pozostało responsywne.
4.  **Czyszczenie przy zamykaniu**:
    - Dokładnie przejrzeć logikę `app.cleanup()` i upewnić się, że wszystkie zasoby (np. timery, wątki, otwarte pliki) są poprawnie zwalniane.
5.  **Separacja odpowiedzialności**:
    - Rozważyć przeniesienie logiki związanej ze splash screenem do osobnej klasy lub modułu, aby odciążyć `main_app.py`.
6.  **Komentarze i dokumentacja**:
    - Dodać komentarze w miejscach, gdzie logika jest złożona lub nieoczywista.
    - Przejrzeć istniejące docstringi pod kątem kompletności i jasności.
7.  **Obsługa błędów krytycznych**:
    - Oprócz logowania, wyświetlić użytkownikowi okno dialogowe z informacją o krytycznym błędzie uniemożliwiającym uruchomienie aplikacji, jeśli `app.initialize()` zwróci `False`.
8.  **Logowanie**:
    - Upewnić się, że `AppLogger` jest poprawnie inicjalizowany i przekazywany/dostępny we wszystkich komponentach, które tego wymagają. Sprawdzić, czy `app.app_logger` jest zawsze dostępne, gdy jest używane.

**Kod po zmianach (fragmenty koncepcyjne):**

```python
# filepath: c:\\_cloud\\_CFAB_UI_manager\\main_app.py
# ... (importy bez zmian) ...

# Potencjalne stałe dla domyślnej konfiguracji, jeśli nie w pliku config.json
# DEFAULT_APP_CONFIG = {
#     "show_splash": True,
#     "log_to_file": False,
#     "log_ui_to_console": False,
#     "log_level": "INFO",
# }

class ConfigLoader(QObject):
    # ... (bez zmian, chyba że analiza utils.validators.ConfigValidator wykaże potrzebę) ...
    pass

class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._config = DEFAULT_APP_CONFIG.copy() # Jeśli używamy stałych
        self._config = {} # Konfiguracja będzie ładowana przez ApplicationStartup
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.startup = None
        self.resource_manager = None # Inicjalizowane w initialize()
        self.app_logger = None

    # ... (reszta metod Application, z uwzględnieniem sugestii) ...

    def initialize(self):
        \"\"\"
        Scentralizowana inicjalizacja aplikacji.
        \"\"\"
        self.startup = ApplicationStartup(self.base_dir)
        # ... (podłączanie sygnałów) ...

        # Uruchom inicjalizację, która teraz powinna zwracać również resource_manager i app_logger
        # lub ustawiać je jako atrybuty startup, skąd można je pobrać.
        success, self.resource_manager, self.app_logger = self.startup.initialize_core_services() # Przykładowa zmiana

        if success:
            # Konfiguracja jest już załadowana przez startup.config_loaded -> self.on_config_loaded
            # self.resource_manager jest już ustawiony
            # self.app_logger jest już ustawiony

            if self.resource_manager:
                self.resource_manager.css_loaded.connect(self.on_css_loaded)
                # Załaduj CSS przez resource_manager, jeśli to jego odpowiedzialność
                # self.resource_manager.load_stylesheet("styles.qss") # Przykładowe wywołanie
        else:
            # Obsługa krytycznego błędu inicjalizacji - np. wyświetlenie QMessageBox
            # CriticalErrorDialog("Nie udało się zainicjalizować aplikacji.", "Błąd krytyczny").exec()
            pass # ApplicationStartup powinien już zalogować błąd

        return success

    def on_startup_completed(self, app_logger_instance): # Może nie być potrzebne jeśli logger jest zwracany z initialize_core_services
        # ... (logika) ...
        pass


def main(): # Zamiast bezpośrednio w if __name__ == "__main__":
    app = Application(sys.argv)

    initial_memory = performance_monitor.take_memory_snapshot("application_start")

    if not app.initialize():
        # Tutaj można dodać wyświetlenie okna błędu krytycznego dla użytkownika
        # np. QMessageBox.critical(None, "Błąd Krytyczny", "Nie można uruchomić aplikacji. Sprawdź logi po szczegóły.")
        AppLogger.critical("Application initialization failed. Exiting.") # Upewnij się, że logger jest dostępny
        sys.exit(1)

    # Użyj resource_manager do pobrania ścieżek
    icon_path = app.resource_manager.get_image_path("icon.png") # Zakładając, że RM ma taką metodę
    app.setWindowIcon(QIcon(icon_path))

    performance_monitor.take_memory_snapshot("before_main_window")

    main_win = MainWindow(app_logger=app.app_logger) # app_logger powinien być już zainicjalizowany
    main_win.setWindowIcon(QIcon(icon_path))
    main_win.preferences = app.config

    performance_monitor.take_memory_snapshot("after_main_window")

    splash_logic = None # Obiekt do zarządzania logiką splash screena
    if app.config.get("show_splash", True):
        # splash_logic = SplashScreenManager(app.resource_manager, main_win.show) # Przykładowa klasa
        # splash_logic.show_splash_with_progress([...]) # Przekazanie zadań do śledzenia
        # Zamiast bezpośredniej symulacji tutaj, logika postępu powinna być w ApplicationStartup
        # lub innym miejscu wykonującym rzeczywiste zadania.
        # Poniższy kod symulacji postępu powinien być zastąpiony rzeczywistą integracją.

        splash_path = app.resource_manager.get_image_path("splash.jpg")
        startup_tasks = [
            "Loading configuration", "Initializing UI components", "Loading translations",
            "Loading CSS styles", "Initializing hardware detection", "Finalizing startup"
        ]
        splash, progress_tracker = create_optimized_splash(
            image_path=splash_path, startup_tasks=startup_tasks, window_size=(642, 250)
        )
        # Podłączanie sygnałów z ApplicationStartup do progress_tracker
        # np. app.startup.task_started.connect(progress_tracker.start_task)
        # np. app.startup.task_completed.connect(progress_tracker.complete_task)
        # np. app.startup.all_tasks_completed.connect(splash.startup_completed)

        # Symulacja dla przykładu, docelowo usunąć i zintegrować z ApplicationStartup
        # ... (istniejąca symulacja postępu, która powinna być zastąpiona) ...
        # To jest tylko placeholder, rzeczywista logika powinna być sterowana przez ApplicationStartup
        # lub podobny mechanizm, który faktycznie wykonuje te zadania.
        # Na przykład, ApplicationStartup mógłby emitować sygnały:
        # self.task_started.emit("Loading configuration")
        # ... wykonuje ładowanie konfiguracji ...
        # self.task_completed.emit("Loading configuration")

        # Poniższa symulacja powinna być usunięta lub zrefaktoryzowana
        # aby odzwierciedlać rzeczywisty postęp sterowany przez ApplicationStartup
        # lub podobny mechanizm.
        # Dla celów demonstracyjnych, zostawiam, ale z komentarzem o konieczności zmiany.
        # POCZĄTEK BLOKU DO REFAKTORYZACJI/USUNIĘCIA (SYMULACJA POSTĘPU)
        progress_tracker.start_task("Loading configuration")
        progress_tracker.complete_task("Loading configuration")
        progress_tracker.start_task("Initializing UI components")
        progress_tracker.complete_task("Initializing UI components")
        progress_tracker.start_task("Loading translations")
        progress_tracker.complete_task("Loading translations")
        progress_tracker.start_task("Loading CSS styles")
        progress_tracker.complete_task("Loading CSS styles")
        progress_tracker.start_task("Initializing hardware detection")
        progress_tracker.complete_task("Initializing hardware detection")
        splash.startup_completed.connect(main_win.show)
        QTimer.singleShot(
            1000,
            lambda: [
                progress_tracker.start_task("Finalizing startup"),
                progress_tracker.complete_task("Finalizing startup"),
            ],
        )
        # KONIEC BLOKU DO REFAKTORYZACJI/USUNIĘCIA (SYMULACJA POSTĘPU)
    else:
        main_win.show()

    # ... (reszta kodu bez zmian: performance monitoring, cleanup) ...

    sys.exit(app.exec())

if __name__ == \"__main__\":
    # Opcjonalnie: podstawowa konfiguracja logowania przed pełną inicjalizacją AppLogger
    # import logging
    # logging.basicConfig(level=logging.INFO) # Dla logów przed inicjalizacją AppLogger

    # Użyj dekoratora handle_error_gracefully lub bloku try-except dla main()
    # aby złapać nieobsłużone wyjątki na najwyższym poziomie
    try:
        main()
    except Exception as e:
        # Logowanie krytycznego błędu, jeśli AppLogger nie jest jeszcze dostępny
        # lub jeśli błąd wystąpił przed jego inicjalizacją.
        print(f"Unhandled critical error in main: {e}") # Do konsoli
        # Można spróbować użyć AppLogger, jeśli jest szansa, że istnieje
        if Application.instance() and hasattr(Application.instance(), 'app_logger') and Application.instance().app_logger:
            Application.instance().app_logger.critical(f"Unhandled critical error: {e}", exc_info=True)
        # Opcjonalnie: wyświetl prosty komunikat błędu użytkownikowi
        # QtWidgets.QMessageBox.critical(None, "Błąd Krytyczny", f"Wystąpił nieobsłużony błąd krytyczny: {e}")
        sys.exit(1)

```

**Checklista zależności:**

- [ ] `utils/application_startup.py`: Może wymagać modyfikacji, aby lepiej integrować się z `progress_tracker` i zwracać/ustawiać `resource_manager` oraz `app_logger`. Metoda `initialize` może potrzebować zmiany sygnatury lub sposobu działania.
- [ ] `utils/resource_manager.py`: Upewnić się, że dostarcza metody do pobierania ścieżek zasobów (np. `get_icon_path`, `get_image_path`, `load_stylesheet`).
- [ ] `utils/logger.py`: Sprawdzić inicjalizację i dostępność `AppLogger`.
- [ ] `UI/main_window.py`: Upewnić się, że poprawnie przyjmuje i używa `app_logger`.
- [ ] `utils/enhanced_splash.py`: Może nie wymagać zmian, jeśli `progress_tracker` jest sterowany zewnętrznie.
- [ ] `config.json`: Rozważyć dodanie domyślnych wartości konfiguracyjnych, jeśli to appropriate.

**Plan testów:**

1.  **Uruchomienie aplikacji**: Sprawdzić, czy aplikacja uruchamia się poprawnie bez błędów.
2.  **Splash screen**:
    - Jeśli włączony, sprawdzić, czy splash screen jest wyświetlany.
    - Sprawdzić, czy postęp na splash screenie (nawet jeśli nadal symulowany na tym etapie) działa zgodnie z oczekiwaniami.
    - Sprawdzić, czy główne okno pojawia się po zakończeniu splash screena.
3.  **Wyłączenie splash screena**: Zmienić `show_splash` na `false` w `config.json` i sprawdzić, czy aplikacja uruchamia się bezpośrednio do głównego okna.
4.  **Ikona aplikacji**: Sprawdzić, czy ikona aplikacji jest poprawnie wyświetlana w oknie głównym i na pasku zadań.
5.  **Logowanie**: Sprawdzić, czy logi są zapisywane zgodnie z konfiguracją (poziom logowania, zapis do pliku/konsoli).
6.  **Obsługa błędów inicjalizacji**:
    - Symulować błąd podczas inicjalizacji (np. brak pliku `config.json` lub jego uszkodzenie).
    - Sprawdzić, czy aplikacja kończy działanie gracefully i czy odpowiedni komunikat jest logowany (i ewentualnie wyświetlany użytkownikowi).
7.  **Czyszczenie zasobów**: Sprawdzić (np. przez logi lub narzędzia deweloperskie), czy zasoby są zwalniane podczas zamykania aplikacji.
8.  **Działanie konfiguracji**: Sprawdzić, czy zmiany w `config.json` (np. `log_level`) są poprawnie odzwierciedlane w działaniu aplikacji.

**Status tracking:**

- [ ] Analiza `main_app.py` zakończona.
- [ ] Propozycje poprawek udokumentowane.
- [ ] Zależności zidentyfikowane.
- [ ] Plan testów przygotowany.
- [ ] Oczekiwanie na implementację i testy.

---

### Etap 2: Analiza `utils\application_startup.py`

**Priorytet:** WYSOKI
**Szacowany Czas:** 2-3 godziny
**Poziom Ryzyka:** WYSOKI (kluczowy komponent startowy, zmiany mogą wpłynąć na całą aplikację)

#### Pliki do Modyfikacji:

- `utils\application_startup.py` - Główny plik odpowiedzialny za sekwencję startową

#### Poprawki Etapu 2:

##### 2.1 Refaktoryzacja i Usprawnienia w `ApplicationStartup`

**Plik:** `utils\application_startup.py`

**Znalezione Problemy:**

1.  **Kolejność inicjalizacji loggera i konfiguracji**: W `setup_logging` jest próba załadowania konfiguracji (`self.load_config()`), jeśli `self.config` nie istnieje. Jednak `load_config` również próbuje użyć loggera. To tworzy potencjalne błędne koło lub niejasną zależność. Główna metoda `initialize` powinna ustalać jasną kolejność: najpierw konfiguracja (lub jej część potrzebna do loggera), potem logger, potem reszta.
2.  **Domyślna konfiguracja loggera**: W `setup_logging`, jeśli główna konfiguracja nie jest dostępna, tworzona jest `default_config_for_logger`. To dobre podejście awaryjne, ale warto upewnić się, że jest spójne i dobrze udokumentowane.
3.  **Użycie globalnego `logger` vs `self.logger`**: W kilku miejscach (np. `load_config`, `verify_hardware`) używany jest `effective_logger = self.logger if self.logger else logger` (gdzie `logger` to `logging.getLogger(__name__)`). To może prowadzić do niekonsekwentnego logowania, jeśli `self.logger` (instancja `AppLogger`) nie jest jeszcze dostępny. Należy dążyć do jak najszybszego zainicjalizowania `self.logger` i używania go spójnie.
4.  **Import `TranslationManager` wewnątrz metody**: `from utils.translation_manager import TranslationManager` jest wewnątrz metody `initialize`. Importy powinny być na górze pliku dla lepszej czytelności i wydajności (choć w tym przypadku wpływ na wydajność jest minimalny).
5.  **Weryfikacja sprzętu (`verify_hardware`)**: Ta metoda jest dość rozbudowana i wykonuje operacje plikowe. Uruchamianie jej w osobnym wątku (`self.thread_manager.run_in_thread(self.verify_hardware)`) jest dobrym pomysłem, aby nie blokować głównego wątku. Należy jednak upewnić się, że ewentualne błędy z tego wątku są poprawnie obsługiwane i że aplikacja może kontynuować (lub nie) w zależności od wyniku tej weryfikacji.
6.  **Logika `_log_uuid_debug`**: Ta metoda zapisuje informacje do pliku `uuid_debug.txt` za każdym razem, gdy jest wywoływana (a jest wywoływana z `verify_hardware`). Zapis do pliku w trybie append (`"a"`) może prowadzić do bardzo dużych plików, jeśli aplikacja jest często uruchamiana lub jeśli `verify_hardware` jest wywoływane wielokrotnie (choć jest flaga `_hardware_verification_attempted`). Należy rozważyć, czy ten plik jest naprawdę potrzebny lub czy logowanie na poziomie DEBUG przez `AppLogger` nie jest wystarczające.
7.  **Sygnał `startup_completed`**: Emituje `self.logger`. W `main_app.py` (w proponowanych zmianach) oczekiwaliśmy, że `initialize` (lub nowa metoda `initialize_core_services`) może zwracać `app_logger` i `resource_manager`. Należy to ujednolicić. Albo `initialize` zwraca te instancje, albo są one dostępne jako atrybuty `ApplicationStartup` po zakończeniu inicjalizacji, a sygnał `startup_completed` informuje tylko o zakończeniu (ewentualnie przekazując status).
8.  **Obsługa błędów w `initialize`**: Główny blok `try-except` w `initialize` łapie `Exception as e`. Jeśli `self.logger` nie jest jeszcze dostępny, błąd jest drukowany do konsoli. To dobre, ale warto rozważyć bardziej ustrukturyzowane podejście do błędów krytycznych przed inicjalizacją loggera.
9.  **Metoda `initialize` zwraca `True`/`False`**: W `main_app.py` sprawdzamy ten wynik. To jest w porządku.
10. **Zależność od `config.json` dla `TranslationManager`**: `TranslationManager.initialize` przyjmuje `config_path`. To jest OK.
11. **Brak jawnego przekazywania zadań do `progress_tracker`**: Jeśli `ApplicationStartup` ma być odpowiedzialny za rzeczywisty postęp inicjalizacji, powinien emitować sygnały `task_started` i `task_completed`, które mogłyby być podłączone do `progress_tracker` w `main_app.py`.

**Proponowane Poprawki:**

1.  **Kolejność inicjalizacji**: Zmienić `initialize` tak, aby:
    - Najpierw ładowało podstawową konfigurację (tylko to, co potrzebne dla loggera).
    - Następnie inicjalizowało `self.logger` (`AppLogger`).
    - Następnie ładowało resztę konfiguracji (jeśli jest podzielona) i inicjalizowało pozostałe komponenty (`ResourceManager`, `TranslationManager`).
2.  **Użycie loggera**: Po zainicjalizowaniu `self.logger`, używać go spójnie we wszystkich metodach klasy.
3.  **Importy**: Przenieść `from utils.translation_manager import TranslationManager` na górę pliku.
4.  **Weryfikacja sprzętu**: Upewnić się, że `startup_failed` jest emitowany, jeśli `verify_hardware` napotka krytyczny błąd, który powinien zatrzymać aplikację. Rozważyć, czy wynik `verify_hardware` powinien wpływać na ogólny sukces `initialize`.
5.  **Logowanie UUID**: Zmienić `_log_uuid_debug`, aby logowała tylko przez `self.logger.debug()`. Usunąć bezpośredni zapis do `uuid_debug.txt` lub uczynić go bardzo warunkowym (np. tylko jeśli specjalna flaga debugowania jest ustawiona w konfiguracji).
6.  **Zwracanie instancji**: Zmodyfikować `initialize` (lub stworzyć nową metodę, np. `get_initialized_services`), aby zwracała instancje `AppLogger` i `ResourceManager` do `main_app.py`, lub zapewnić, że są one bezpiecznie dostępne jako publiczne atrybuty po pomyślnym zakończeniu `initialize`.
7.  \*\*Integracja z `progress_tracker`:
    - Dodać nowe sygnały do `ApplicationStartup`, np. `task_started = pyqtSignal(str)` i `task_completed = pyqtSignal(str)`.
    - W metodzie `initialize`, przed i po każdym głównym kroku (ładowanie konfiguracji, inicjalizacja loggera, resource managera, translation managera, weryfikacja sprzętu), emitować te sygnały z nazwą zadania.
    - W `main_app.py` podłączyć te sygnały do odpowiednich metod `progress_tracker`.
8.  **Struktura `initialize`**: Podzielić metodę `initialize` na mniejsze, prywatne metody dla każdego kroku inicjalizacji (np. `_initialize_logging`, `_load_app_config`, `_initialize_resource_manager`, `_initialize_translation_manager`, `_perform_hardware_verification`), aby poprawić czytelność i łatwość zarządzania.

**Kod po zmianach (fragmenty koncepcyjne):**

```python
# filepath: c:\\_cloud\\_CFAB_UI_manager\\utils\\application_startup.py
# ... (importy na górze, w tym TranslationManager) ...
from utils.translation_manager import TranslationManager

logger = logging.getLogger(__name__) # Globalny logger dla przypadków przed self.logger

class ApplicationStartup(QObject):
    startup_completed = pyqtSignal() # Zmieniono - nie przekazuje już loggera
    startup_failed = pyqtSignal(str) # Przekazuje komunikat błędu
    config_loaded = pyqtSignal(dict)
    task_started = pyqtSignal(str)   # Dla progress_tracker
    task_completed = pyqtSignal(str) # Dla progress_tracker

    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = base_dir
        self.config = None
        self.thread_manager = ThreadManager()
        self.resource_manager = None
        self.app_logger = None # Zmieniona nazwa z self.logger na self.app_logger dla spójności
        self._hardware_verification_attempted = False

    @performance_monitor.measure_execution_time("app_startup")
    def initialize(self):
        try:
            # Krok 1: Wstępne ładowanie konfiguracji (tylko to, co potrzebne dla loggera, jeśli w ogóle)
            # Jeśli AppLogger może działać z domyślnymi wartościami, ten krok może być częścią _initialize_logging
            self.task_started.emit("Loading initial configuration")
            # self._load_initial_config() # Przykładowa metoda
            self.task_completed.emit("Loading initial configuration")

            # Krok 2: Inicjalizacja loggera
            self.task_started.emit("Initializing logger")
            if not self._initialize_logging():
                # Krytyczny błąd, logger nie mógł zostać zainicjalizowany
                # Komunikat powinien być już wysłany przez _initialize_logging
                # self.startup_failed.emit("Logger initialization failed.") # Już obsłużone w _initialize_logging
                return False
            self.task_completed.emit("Initializing logger")

            # Krok 3: Pełne ładowanie konfiguracji
            self.task_started.emit("Loading main configuration")
            if not self._load_main_config():
                # self.startup_failed.emit("Main configuration loading failed.") # Już obsłużone w _load_main_config
                return False
            self.task_completed.emit("Loading main configuration")

            # Krok 4: Inicjalizacja TranslationManager
            self.task_started.emit("Initializing translations")
            if not self._initialize_translation_manager():
                return False
            self.task_completed.emit("Initializing translations")

            # Krok 5: Inicjalizacja ResourceManager
            self.task_started.emit("Initializing resources")
            if not self._initialize_resource_manager():
                return False
            self.task_completed.emit("Initializing resources")

            # Krok 6: Weryfikacja sprzętu (wątek)
            self.task_started.emit("Verifying hardware")
            # Ta operacja jest w wątkach, więc task_completed będzie emitowane przez samą metodę verify_hardware
            # lub przez callback po zakończeniu wątku.
            self.thread_manager.run_in_thread(self._perform_hardware_verification)
            # Nie czekamy tutaj na zakończenie, zakładamy, że aplikacja może kontynuować
            # Jeśli weryfikacja sprzętu jest krytyczna, logika musi być inna.

            self.app_logger.info("Core application startup sequence completed.")
            self.startup_completed.emit()
            return True

        except Exception as e:
            error_msg = f"Critical error during application startup: {e}"
            if self.app_logger:
                self.app_logger.critical(error_msg, exc_info=True)
            else:
                logger.critical(error_msg, exc_info=True) # Użyj globalnego loggera
            self.startup_failed.emit(error_msg)
            return False

    def _initialize_logging(self):
        log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        try:
            # Tutaj można załadować tylko sekcję konfiguracji dotyczącą logowania
            # lub przekazać ścieżkę do AppLogger, aby sam sobie poradził.
            # Dla uproszczenia, załóżmy, że AppLogger może przyjąć config=None
            # i użyć wartości domyślnych, jeśli pełna konfiguracja nie jest jeszcze załadowana.
            temp_config_for_logger = None
            # Jeśli masz już self.config z _load_initial_config(), użyj go:
            # temp_config_for_logger = self.config

            self.app_logger = AppLogger(temp_config_for_logger if temp_config_for_logger else {
                "log_level": "INFO", "log_to_file": False, "log_ui_to_console": True, "log_dir": log_dir
            })
            self.app_logger.info("AppLogger initialized.")
            return True
        except Exception as e:
            logger.critical(f"Failed to initialize AppLogger: {e}", exc_info=True)
            self.startup_failed.emit(f"Logger initialization failed: {e}")
            return False

    def _load_main_config(self):
        config_path = os.path.join(self.base_dir, "config.json")
        self.app_logger.debug(f"Loading main configuration from: {config_path}")
        try:
            if not os.path.exists(config_path):
                raise FileOperationError(f"Configuration file not found: {config_path}", file_path=config_path)

            config = ConfigValidator.validate_config_file(config_path)
            self.config = config
            self.config_loaded.emit(config)
            self.app_logger.info("Main configuration loaded and validated successfully.")
            # Po załadowaniu głównej konfiguracji, jeśli logger był inicjalizowany z domyślnymi,
            # można go zrekonfigurować.
            if hasattr(self.app_logger, 'reconfigure') and self.config.get('logging'):
                self.app_logger.reconfigure(self.config.get('logging'))
            return True
        except (ConfigurationError, ValidationError, FileOperationError, json.JSONDecodeError) as e:
            self.app_logger.error(f"Failed to load or validate main configuration: {e}", exc_info=True)
            self.startup_failed.emit(f"Configuration error: {e}")
            return False
        except Exception as e: # Catch-all for other unexpected errors
            self.app_logger.error(f"Unexpected error loading main configuration: {e}", exc_info=True)
            self.startup_failed.emit(f"Unexpected configuration error: {e}")
            return False

    def _initialize_translation_manager(self):
        try:
            config_path = os.path.join(self.base_dir, "config.json") # lub self.config jeśli już załadowany
            TranslationManager.initialize(config_path=config_path, app_logger=self.app_logger)
            self.app_logger.info("TranslationManager initialized.")
            return True
        except Exception as e:
            self.app_logger.error(f"Failed to initialize TranslationManager: {e}", exc_info=True)
            self.startup_failed.emit(f"TranslationManager initialization failed: {e}")
            return False

    def _initialize_resource_manager(self):
        try:
            self.resource_manager = ResourceManager(self.base_dir, self.app_logger)
            self.resource_manager.load_all_resources() # Może być asynchroniczne, rozważyć sygnały postępu
            self.app_logger.info("ResourceManager initialized and resources loaded.")
            return True
        except Exception as e:
            self.app_logger.error(f"Failed to initialize ResourceManager: {e}", exc_info=True)
            self.startup_failed.emit(f"ResourceManager initialization failed: {e}")
            return False

    # handle_error_gracefully może nie być potrzebny, jeśli błędy są łapane wewnątrz
    def _perform_hardware_verification(self):
        if self._hardware_verification_attempted:
            self.app_logger.info("Hardware verification already attempted. Skipping.")
            self.task_completed.emit("Verifying hardware") # Upewnij się, że to jest emitowane
            return
        self._hardware_verification_attempted = True

        try:
            hardware_path = os.path.join(self.base_dir, "hardware.json")
            current_uuid = get_stable_uuid()
            self.app_logger.info(f"Current system UUID: {current_uuid}")

            # ... (logika weryfikacji sprzętu, podobna do istniejącej, ale używająca self.app_logger) ...
            # Upewnij się, że wszystkie operacje plikowe są w trybie-except
            # Przykład:
            if os.path.exists(hardware_path):
                profile = ConfigValidator.validate_hardware_profile(hardware_path)
                # ... (reszta logiki) ...
            else:
                self.app_logger.warning("Hardware profile not found. Creating new one.")
                # ... (tworzenie nowego profilu) ...

            self.app_logger.info("Hardware verification completed.")
        except Exception as e:
            self.app_logger.error(f"Error during hardware verification: {e}", exc_info=True)
            # Decyzja, czy to jest błąd krytyczny dla startup_failed
            # self.startup_failed.emit(f"Hardware verification failed: {e}")
        finally:
            self.task_completed.emit("Verifying hardware") # Zawsze emituj ukończenie zadania

    def _log_uuid_debug(self, uuid_value): # Ta metoda może być uproszczona lub usunięta
        self.app_logger.debug(f"====== UUID DEBUG INFO ======")
        self.app_logger.debug(f"System: {platform.system()}, Node: {platform.node()}, Machine: {platform.machine()}")
        self.app_logger.debug(f"UUID (cached): {uuid_value}")
        self.app_logger.debug(f"===========================")
        # Usunięto zapis do pliku uuid_debug.txt, AppLogger powinien to obsłużyć

    # ... (_check_system_changes, _create_new_hardware_profile bez większych zmian, używają self.app_logger) ...

    def cleanup(self):
        self.app_logger.info("Cleaning up application resources...")
        if self.resource_manager:
            self.resource_manager.cleanup()
        if self.thread_manager:
            self.thread_manager.cleanup()
        self.app_logger.info("Application cleanup finished.")

```

**Checklista zależności:**

- [ ] `utils/application_startup.py`: Będzie wymagał aktualizacji, aby:
  - Podłączyć nowe sygnały `task_started` i `task_completed` z `ApplicationStartup` do `progress_tracker` na splash screenie.
  - Pobierać instancje `app_logger` i `resource_manager` z atrybutów `ApplicationStartup` po sygnale `startup_completed` (lub jeśli `initialize` je zwraca).
  - Obsługiwać sygnał `startup_failed(str)` z komunikatem błędu.
- [ ] `utils/logger.py` (`AppLogger`):
  - Upewnić się, że może być inicjalizowany z minimalną konfiguracją lub wartościami domyślnymi, jeśli pełna konfiguracja nie jest jeszcze dostępna.
  - Rozważyć dodanie metody `reconfigure(new_config_section)`, jeśli logger ma być aktualizowany po pełnym załadowaniu `config.json`.
- [ ] `utils/resource_manager.py`: Upewnić się, że `load_all_resources()` może być wywoływane i ewentualnie emitować sygnały postępu, jeśli ładowanie jest długotrwałe.
- [ ] `utils/translation_manager.py` (`TranslationManager`): Bez zmian, jeśli `initialize` działa poprawnie.
- [ ] `utils/validators.py` (`ConfigValidator`): Bez zmian, ale jego rola w walidacji konfiguracji i profilu sprzętowego jest kluczowa.
- [ ] `config.json`: Może wymagać podziału na sekcję dla loggera (jeśli potrzebna jest konfiguracja przed pełnym załadowaniem) lub dodania sekcji `logging` dla `AppLogger.reconfigure()`.

**Plan testów:**

1.  **Poprawne uruchomienie**: Aplikacja startuje, splash screen pokazuje kolejne etapy (ładowanie konfiguracji, loggera, zasobów, tłumaczeń, weryfikacja sprzętu), główne okno się pojawia.
2.  **Logowanie**: Wszystkie etapy startu są logowane przez `AppLogger` na odpowiednich poziomach.
3.  **Błąd ładowania konfiguracji**: Symulować brak `config.json` lub jego uszkodzenie.
    - Aplikacja powinna zalogować błąd krytyczny.
    - Sygnał `startup_failed` powinien być emitowany z odpowiednim komunikatem.
    - `main_app.py` powinien obsłużyć ten błąd (np. wyświetlić komunikat i zamknąć aplikację).
4.  **Błąd inicjalizacji loggera**: (Trudniejsze do symulacji bez modyfikacji kodu `AppLogger`) Sprawdzić, czy fallback na globalny logger działa w przypadku krytycznego błędu w `AppLogger`.
5.  **Błąd inicjalizacji ResourceManager/TranslationManager**: Symulować błąd (np. brakujące pliki zasobów/tłumaczeń).
    - Aplikacja powinna zalogować błąd.
    - Sygnał `startup_failed` powinien być emitowany.
6.  **Weryfikacja sprzętu**:
    - Pierwsze uruchomienie: tworzy `hardware.json`.
    - Kolejne uruchomienie: weryfikuje istniejący `hardware.json`.
    - Zmiana UUID/systemu: Sprawdzić, czy profil jest aktualizowany lub tworzony na nowo zgodnie z logiką.
    - Błąd podczas weryfikacji sprzętu (np. brak uprawnień do zapisu `hardware.json`): Sprawdzić logowanie błędu i czy `task_completed` jest emitowane dla tego zadania.
7.  **Postęp na splash screenie**: Sprawdzić, czy etapy wyświetlane na splash screenie odpowiadają emitowanym sygnałom `task_started`/`task_completed`.
8.  **Czyszczenie**: Sprawdzić, czy metoda `cleanup` jest wywoływana i loguje zakończenie czyszczenia.

**Status tracking:**

- [ ] Analiza `utils\application_startup.py` zakończona.
- [ ] Propozycje poprawek udokumentowane.
- [ ] Zależności zidentyfikowane.
- [ ] Plan testów przygotowany.
- [ ] Oczekiwanie na implementację i testy.

---

### Etap 3: Analiza `utils/logger.py` (`AppLogger`)

**Priorytet:** WYSOKI
**Szacowany Czas:** 2-3 godziny
**Poziom Ryzyka:** ŚREDNI (zmiany w logowaniu mogą wpłynąć na debugowanie i monitorowanie aplikacji)

#### Pliki do Modyfikacji:

- `utils/logger.py` - Główny plik implementujący `AppLogger`

#### Poprawki Etapu 3:

##### 3.1 Refaktoryzacja i Usprawnienia w `AppLogger`

**Plik:** `utils/logger.py`

**Znalezione Problemy (na podstawie analizy kodu `utils/logger.py`):**

1.  **Inicjalizacja i Konfiguracja**:
    - Konstruktor `__init__` przyjmuje `config` i `base_dir`. Jeśli `config` nie jest dostarczony, używane są wartości domyślne. To jest dobre, ale należy upewnić się, że domyślne wartości są sensowne i spójne z oczekiwaniami `ApplicationStartup`.
    - Metoda `setup_logging` jest wywoływana w `__init__`. Jest odpowiedzialna za tworzenie handlerów.
    - Brak jawnej metody `reconfigure` wspomnianej w analizie `ApplicationStartup`. Jeśli konfiguracja logowania ma być zmieniana dynamicznie po pełnym załadowaniu `config.json`, taka metoda byłaby przydatna. Obecnie, aby zmienić konfigurację, trzeba by tworzyć nową instancję loggera.
2.  **Handlery**:
    - `FileHandler`: Zapisuje logi do pliku. Nazwa pliku (`app.log`), rotacja (`RotatingFileHandler` z `maxBytes=5*1024*1024`, `backupCount=5`) i formatowanie są zdefiniowane. Ścieżka do logów jest tworzona, jeśli nie istnieje.
    - `StreamHandler` (dla konsoli): Loguje do `sys.stdout`. Jest dodawany warunkowo na podstawie `config.get("log_to_console", True)`.
    - `QtLogHandler` (dla UI): Loguje do widgetu UI (np. `QTextEdit`). Jest dodawany warunkowo na podstawie `config.get("log_ui_to_console", False)` i jeśli `ui_log_signal` jest dostarczony.
3.  **Formatowanie Logów**:
    - Używany jest `CustomFormatter` dziedziczący z `logging.Formatter`. Dodaje on `levelname` i `asctime` do standardowego formatu.
    - Format jest stały: `%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s`.
4.  **Poziomy Logowania**:
    - Poziom logowania jest ustawiany na podstawie `config.get("log_level", "INFO").upper()`. Obsługiwane są standardowe poziomy.
5.  **Obsługa Błędów w Loggerze**:
    - W `setup_logging` jest blok `try-except Exception`, który loguje błąd do standardowego loggera Pythona, jeśli konfiguracja `AppLogger` zawiedzie. To dobre podejście awaryjne.
6.  **`QtLogHandler` i Sygnały**:
    - `QtLogHandler` emituje sygnał `log_signal = pyqtSignal(str)` z sformatowanym rekordem logu. To pozwala na integrację z UI Qt.
7.  **Metody Logujące**:
    - Standardowe metody `debug`, `info`, `warning`, `error`, `critical` są dostępne przez dziedziczenie z `logging.Logger`.
8.  **Internacjonalizacja**:
    - Komunikaty logów są zazwyczaj dynamiczne i pochodzą z różnych części aplikacji. Sam logger nie generuje tekstów, które wymagałyby bezpośredniej internacjonalizacji w jego kodzie, poza ewentualnymi komunikatami o błędach konfiguracji (które są po angielsku).
9.  **Czystość Kodu**:
    - Kod jest generalnie czytelny. Można rozważyć dodanie typowania dla lepszej analizy statycznej.
    - Nazwa `log_ui_to_console` w konfiguracji może być myląca, gdyż sugeruje konsolę, a w rzeczywistości odnosi się do UI. Lepsza byłaby nazwa `log_to_ui` lub `enable_ui_logging`.

**Proponowane Poprawki:**

1.  **Metoda `reconfigure`**:
    - Dodać publiczną metodę `reconfigure(new_config)`, która pozwoli na zmianę ustawień loggera (poziom, handlery, formatowanie) w locie, po pełnym załadowaniu konfiguracji aplikacji. Powinna ona bezpiecznie usunąć istniejące handlery i skonfigurować nowe.
2.  **Nazewnictwo konfiguracji**:
    - Zasugerować zmianę klucza `log_ui_to_console` na `log_to_ui` w `config.json` i w kodzie `AppLogger` dla większej jasności. To wymagałoby aktualizacji domyślnego `config.json` i dokumentacji.
3.  **Domyślna konfiguracja**:
    - Upewnić się, że domyślna konfiguracja używana w `__init__` (gdy `config` is `None`) jest spójna z tym, co `ApplicationStartup` może dostarczyć na wczesnym etapie (np. tylko `log_dir`, `log_level`).
4.  **Typowanie**:
    - Dodać type hints do metod i atrybutów dla lepszej czytelności i wsparcia narzędzi deweloperskich.
5.  **Obsługa `ui_log_signal`**:
    - Obecnie `QtLogHandler` jest tworzony tylko jeśli `ui_log_signal` jest przekazany do `__init__`. Rozważyć, czy `AppLogger` powinien sam tworzyć ten sygnał, czy też zawsze oczekiwać go z zewnątrz. Przekazywanie z zewnątrz jest bardziej elastyczne.
6.  **Formatowanie**:
    - `CustomFormatter` jest prosty. Jeśli potrzebne byłyby bardziej zaawansowane formaty (np. kolorowanie dla konsoli, różne formaty dla różnych handlerów), można by to rozbudować. Na razie wydaje się wystarczający.
7.  **Testowanie**:
    - Upewnić się, że wszystkie ścieżki konfiguracji (różne poziomy logowania, włączanie/wyłączanie handlerów) są przetestowane.

**Kod po zmianach (fragmenty koncepcyjne):**

```python
# filepath: c:\\_cloud\\_CFAB_UI_manager\\utils\\logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from PyQt5.QtCore import QObject, pyqtSignal # Zakładając PyQt5
from typing import Optional, Dict, Any

# ... (CustomFormatter i QtLogHandler bez większych zmian, chyba że dodamy typowanie) ...

class CustomFormatter(logging.Formatter):
    # ... (bez zmian) ...
    pass

class QtLogHandler(logging.Handler, QObject): # Dodano QObject dla poprawnej obsługi sygnałów
    log_signal = pyqtSignal(str)
    # Należy zainicjować QObject, jeśli nie jest dziedziczony przez klasę nadrzędną logging.Handler
    # Jednak logging.Handler nie jest QObject, więc trzeba to zrobić jawnie.
    # Można też zrobić QtLogHandler jako QObject i osobno logging.Handler,
    # ale to komplikuje. Prostsze jest:
    # class QtLogHandler(logging.Handler):
    #     def __init__(self, log_signal_emitter: QObject): # Przekazujemy obiekt emitujący sygnał
    #         super().__init__()
    #         self.log_signal_emitter = log_signal_emitter
    #     def emit(self, record):
    #         msg = self.format(record)
    #         self.log_signal_emitter.log_signal.emit(msg) # Używamy sygnału z przekazanego obiektu

    # Aktualna implementacja z dziedziczeniem po QObject jest bardziej typowa dla Qt:
    def __init__(self): # Usunięto argument log_signal, sygnał jest atrybutem klasy
        logging.Handler.__init__(self)
        QObject.__init__(self) # Jawna inicjalizacja QObject

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.log_signal.emit(msg)


class AppLogger(logging.Logger):
    _instance = None

    # # Opcjonalnie: Singleton, jeśli chcemy mieć jedną instancję globalnie
    # def __new__(cls, *args, **kwargs):
    #     if not cls._instance:
    #         cls._instance = super(AppLogger, cls).__new__(cls)
    #     return cls._instance

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 base_dir: Optional[str] = None,
                 name: str = "AppLogger",
                 ui_log_signal_emitter: Optional[QtLogHandler] = None): # Zmieniono na emitter
        super().__init__(name)
        self.config: Dict[str, Any] = config if config else {}
        self.base_dir: str = base_dir if base_dir else os.getcwd()
        self.log_dir: str = self.config.get("log_dir", os.path.join(self.base_dir, "logs"))
        self.ui_log_signal_emitter: Optional[QtLogHandler] = ui_log_signal_emitter # Przechowujemy emitter

        # Domyślna konfiguracja, jeśli nie podano
        self._default_log_level = "INFO"
        self._default_log_to_file = True
        self._default_log_to_console = True
        self._default_log_to_ui = False # Zmieniona nazwa klucza

        self.setup_logging()

    def setup_logging(self) -> None:
        try:
            # Usuń istniejące handlery, jeśli są (ważne dla reconfigure)
            for handler in self.handlers[:]:
                self.removeHandler(handler)
                handler.close()

            os.makedirs(self.log_dir, exist_ok=True)

            log_level_str = self.config.get("log_level", self._default_log_level).upper()
            log_level = getattr(logging, log_level_str, logging.INFO)
            self.setLevel(log_level)

            formatter = CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')

            # File Handler
            if self.config.get("log_to_file", self._default_log_to_file):
                log_file = os.path.join(self.log_dir, self.config.get("log_file_name", "app.log"))
                file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
                file_handler.setFormatter(formatter)
                self.addHandler(file_handler)

            # Console Handler
            if self.config.get("log_to_console", self._default_log_to_console):
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                self.addHandler(console_handler)

            # UI Handler (Qt)
            # Zmieniono klucz konfiguracji z "log_ui_to_console" na "log_to_ui"
            if self.config.get("log_to_ui", self._default_log_to_ui) and self.ui_log_signal_emitter:
                # Zakładamy, że ui_log_signal_emitter to instancja QtLogHandler
                # lub obiekt posiadający kompatybilny sygnał.
                # Jeśli ui_log_signal_emitter to QtLogHandler, to on sam jest handlerem.
                if isinstance(self.ui_log_signal_emitter, QtLogHandler):
                    ui_handler = self.ui_log_signal_emitter
                    ui_handler.setFormatter(formatter)
                    # Upewnij się, że poziom logowania dla UI handlera jest odpowiedni
                    ui_handler.setLevel(log_level) # Można też ustawić inny, specyficzny dla UI
                    self.addHandler(ui_handler)
                else:
                    # Jeśli ui_log_signal_emitter to inny QObject z sygnałem,
                    # trzeba by stworzyć QtLogHandler i podłączyć go.
                    # Dla uproszczenia, zakładamy, że przekazujemy gotowy QtLogHandler.
                    self.warning("UI logging enabled but ui_log_signal_emitter is not a QtLogHandler instance.")


        except Exception as e:
            # Fallback to basic logging if setup fails
            logging.basicConfig(level=logging.INFO)
            logging.error(f"Failed to setup AppLogger: {e}", exc_info=True)
            # Można też rzucić wyjątek, aby zasygnalizować problem wyżej
            # raise LoggerSetupError(f"Failed to setup AppLogger: {e}") from e

    def reconfigure(self, new_config: Dict[str, Any]) -> None:
        """
        Rekonfiguruje logger z nowymi ustawieniami.
        """
        self.info("Reconfiguring logger...")
        # Aktualizuj tylko te części konfiguracji, które są istotne dla loggera
        # lub po prostu zastąp całą konfigurację loggera.
        # Dla bezpieczeństwa, można zaktualizować tylko znane klucze.
        logger_keys = {"log_level", "log_to_file", "log_file_name", "log_dir",
                       "log_to_console", "log_to_ui"} # Zmieniono "log_ui_to_console"

        current_logger_config = {key: self.config[key] for key in logger_keys if key in self.config}

        for key in logger_keys:
            if key in new_config:
                current_logger_config[key] = new_config[key]

        self.config.update(current_logger_config) # Aktualizuj główną konfigurację loggera

        # Jeśli log_dir się zmienił, zaktualizuj go
        if "log_dir" in new_config:
            self.log_dir = self.config.get("log_dir", os.path.join(self.base_dir, "logs"))

        self.setup_logging() # Ponownie skonfiguruj handlery
        self.info(f"Logger reconfigured. New level: {self.config.get('log_level')}")

    # Można dodać metody specyficzne dla aplikacji, jeśli potrzebne
    # np. log_user_action(user, action, details)

# Przykład użycia (globalna instancja lub przekazywanie)
# app_logger = AppLogger(config={"log_level": "DEBUG"}, base_dir=".")
# app_logger.info("To jest test.")

# Jeśli chcemy używać QtLogHandler:
# qt_handler_instance = QtLogHandler()
# app_logger_with_ui = AppLogger(config={"log_to_ui": True}, ui_log_signal_emitter=qt_handler_instance)
# qt_handler_instance.log_signal.connect(lambda msg: print(f"UI LOG: {msg}")) # Podłączenie do slotu
# app_logger_with_ui.info("Log do UI")

```

**Checklista zależności:**

- [ ] `utils/application_startup.py`:
  - Musi poprawnie inicjalizować `AppLogger`, potencjalnie w dwóch etapach: raz z konfiguracją domyślną/minimalną, a potem wywołać `reconfigure` po załadowaniu pełnego `config.json`.
  - Musi przekazać `base_dir` do `AppLogger`.
  - Jeśli logowanie do UI jest używane, `ApplicationStartup` lub `main_app.py` musi stworzyć instancję `QtLogHandler` i przekazać ją do `AppLogger`.
- [ ] `main_app.py`:
  - Jeśli `main_app.py` jest odpowiedzialny za tworzenie widgetu logów UI i podłączanie sygnału z `QtLogHandler`, musi mieć dostęp do instancji `QtLogHandler` (lub jej sygnału).
- [ ] `config.json`:
  - Należy zweryfikować/zaktualizować klucze konfiguracyjne (np. `log_to_ui` zamiast `log_ui_to_console`) oraz dodać sekcję dla loggera, jeśli to potrzebne.

**Plan testów:**

1.  **Inicjalizacja domyślna**: Sprawdzić, czy logger inicjalizuje się poprawnie bez przekazanej konfiguracji, używając wartości domyślnych (logowanie do pliku i konsoli, poziom INFO).
2.  **Inicjalizacja z konfiguracją**:
    - Sprawdzić różne poziomy logowania (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
    - Włączyć/wyłączyć logowanie do pliku.
    - Włączyć/wyłączyć logowanie do konsoli.
    - Włączyć/wyłączyć logowanie do UI (jeśli zaimplementowane i skonfigurowane).
3.  **Rotacja plików logów**: Sprawdzić, czy pliki logów są poprawnie rotowane po osiągnięciu `maxBytes`.
4.  **Format logów**: Zweryfikować, czy format logów w pliku i konsoli jest zgodny z `CustomFormatter`.
5.  **Logowanie do UI**:
    - Jeśli włączone, sprawdzić, czy logi pojawiają się w odpowiednim widgecie UI.
    - Sprawdzić, czy sygnał z `QtLogHandler` jest poprawnie emitowany.
6.  **Metoda `reconfigure`**:
    - Zainicjalizować logger z jedną konfiguracją.
    - Wywołać `reconfigure` z nową konfiguracją (np. zmiana poziomu logowania, wyłączenie handlera).
    - Sprawdzić, czy logger działa zgodnie z nową konfiguracją.
7.  **Obsługa błędów**:
    - Symulować błąd podczas `setup_logging` (np. brak uprawnień do zapisu w `log_dir`). Sprawdzić, czy logger przełącza się na basicConfig i loguje błąd.
8.  **Ścieżki i `base_dir`**: Sprawdzić, czy `log_dir` jest poprawnie tworzony względem `base_dir`.
9.  **Wydajność**: (Opcjonalnie) Przy intensywnym logowaniu sprawdzić, czy nie ma znaczących spadków wydajności.
10. **Spójność nazewnictwa**: Upewnić się, że klucz `log_to_ui` (zamiast `log_ui_to_console`) jest używany spójnie.

**Status tracking:**

- [ ] Analiza `utils/logger.py` zakończona.
- [ ] Propozycje poprawek udokumentowane.
- [ ] Zależności zidentyfikowane.
- [ ] Plan testów przygotowany.
- [ ] Oczekiwanie na implementację i testy.

---

### Etap 4: Analiza `utils/resource_manager.py` (`ResourceManager`)

**Priorytet:** ŚREDNI
**Szacowany Czas:** 2-3 godziny
**Poziom Ryzyka:** NISKI (zmiany głównie w logice ładowania zasobów, mniejsze ryzyko krytycznych błędów aplikacji)

#### Pliki do Modyfikacji:

- `utils/resource_manager.py` - Główny plik implementujący `ResourceManager`

#### Poprawki Etapu 4:

##### 4.1 Refaktoryzacja i Usprawnienia w `ResourceManager`

**Plik:** `utils/resource_manager.py`

**Znalezione Problemy (na podstawie analizy kodu `utils/resource_manager.py`):**

1.  **Zależności i Importy**:
    - Importuje `logging`, `os`, `time`, `functools.lru_cache`, `typing.Optional`.
    - Importuje `QObject`, `pyqtSignal` z `PyQt6.QtCore`.
    - Importuje `AsyncResourceLoader`, `create_css_loader`, `lazy_loader`, `performance_monitor` z `utils.performance_optimizer`.
    - Importuje `TranslationManager` z `utils.translation_manager`.
    - Używa `logger = logging.getLogger(__name__)` jako domyślnego loggera, jeśli `app_logger` nie zostanie przekazany. Powinien konsekwentnie używać przekazanej `app_logger` (instancji `AppLogger`).
2.  **Inicjalizacja (`__init__`)**:
    - Przyjmuje `base_dir` i opcjonalnie `app_logger`.
    - Tworzy instancję `AsyncResourceLoader` z `max_workers=2`.
    - Wywołuje `_setup_loaders()` do konfiguracji loaderów CSS i tłumaczeń.
    - Podłącza sygnały z `async_loader` (`resource_loaded`, `loading_failed`).
3.  **Konfiguracja Loaderów (`_setup_loaders`)**:
    - Ścieżka do CSS jest hardkodowana: `os.path.join(self.base_dir, "resources", "styles.qss")`.
    - Ścieżka do tłumaczeń jest hardcodowana w `_create_translation_loader`: `os.path.join(self.base_dir, "translations")`.
    - Rejestruje loadery w `lazy_loader` pod nazwami "main_css" i "translations".
4.  **Ładowanie Zasobów (`load_all_resources`, `_load_css_optimized`, `_load_translations`)**:
    - `load_all_resources` inicjuje asynchroniczne ładowanie CSS i tłumaczeń.
    - Metody `_load_css_optimized` i `_load_translations` najpierw próbują pobrać zasoby z `lazy_loader` (cache). Jeśli się nie uda, ładują je bezpośrednio.
    - `_load_css_optimized` jest dekorowana `@performance_monitor.measure_execution_time("css_loading")`.
    - W przypadku niepowodzenia ładowania z cache, logowane jest ostrzeżenie, a następnie zasób jest ładowany bezpośrednio przez odpowiedni loader (np. `self.css_loader()`).
5.  **Obsługa Załadowanych Zasobów (`_handle_resource_loaded`)**:
    - Po załadowaniu zasobu przez `async_loader`, ta metoda emituje odpowiedni sygnał (`css_loaded` lub `translations_loaded`) i przechowuje tłumaczenia.
6.  **Cache (`invalidate_cache`, `cached_with_ttl`)**:
    - `invalidate_cache` pozwala na usunięcie zasobu z `lazy_loader.cache`.
    - Funkcja `cached_with_ttl` jest zdefiniowana, ale nie jest używana w klasie `ResourceManager`. Wydaje się być ogólną funkcją pomocniczą, potencjalnie do użycia w innych miejscach lub była planowana do użycia tutaj.
    - `lazy_loader` (z `performance_optimizer`) wydaje się być głównym mechanizmem cache dla zasobów ładowanych przez `ResourceManager`.
7.  **Sygnały Qt**:
    - Definiuje sygnały: `resources_loaded` (nieemitowany w kodzie), `css_loaded`, `translations_loaded`, `loading_failed`.
8.  **Czyszczenie (`cleanup`)**:
    - Anuluje wszystkie zadania w `async_loader` i czyści go.
9.  **Internacjonalizacja**: Brak tekstów do tłumaczenia w tym module (poza komentarzami i docstringami).
10. **Czystość Kodu i Potencjalne Problemy**:
    - Hardcodowane ścieżki do zasobów (`resources/styles.qss`, `translations`). Lepszym podejściem byłoby przekazanie tych ścieżek przez konfigurację lub jako argumenty.
    - Sygnał `resources_loaded` jest zdefiniowany, ale nigdy nie jest emitowany. Należy zdecydować, czy jest potrzebny i kiedy powinien być emitowany (np. po załadowaniu _wszystkich_ zasobów).
    - Użycie `logger = logging.getLogger(__name__)` jako fallback zamiast polegania wyłącznie na przekazanym `app_logger` może prowadzić do niespójnego logowania, jeśli `app_logger` nie zostanie dostarczony. Lepiej wymagać `app_logger`.
    - Funkcja `cached_with_ttl` jest nieużywana w tym pliku. Jeśli nie jest potrzebna, można ją usunąć lub przenieść do bardziej ogólnego modułu narzędowego, jeśli jest używana gdzie indziej.

**Proponowane Poprawki:**

1.  **Konfiguracja Ścieżek Zasobów**:
    - Zamiast hardcodować ścieżki do `styles.qss` i katalogu `translations`, powinny być one konfigurowalne, np. poprzez plik `config.json` i przekazywane do `ResourceManager` podczas inicjalizacji lub pobierane z obiektu konfiguracyjnego.
2.  **Użycie `app_logger`**:
    - Konsekwentnie używać przekazanej instancji `app_logger`. Jeśli `app_logger` jest kluczowy, powinien być wymaganym argumentem konstruktora.
3.  **Sygnał `resources_loaded`**:
    - Zaimplementować logikę emitowania sygnału `resources_loaded` po pomyślnym załadowaniu wszystkich głównych zasobów (CSS i tłumaczeń). Może to wymagać śledzenia stanu ładowania poszczególnych zasobów.
4.  **Funkcja `cached_with_ttl`**:
    - Jeśli funkcja `cached_with_ttl` nie jest używana przez `ResourceManager` ani nie jest bezpośrednio związana z jego logiką, rozważyć jej usunięcie z tego pliku lub przeniesienie do modułu `utils/helpers.py` lub podobnego.

**Kod po zmianach (fragmenty koncepcyjne):**

```python
# filepath: c:\\_cloud\\_CFAB_UI_manager\\utils\\resource_manager.py
import logging
import os
from typing import Optional, Dict, Any # Dodano Any

from PyQt6.QtCore import QObject, pyqtSignal

from utils.performance_optimizer import (
    AsyncResourceLoader,
    create_css_loader,
    lazy_loader,
    performance_monitor,
)
from utils.translation_manager import TranslationManager

# Usunięto: logger = logging.getLogger(__name__)
# Zamiast tego będziemy polegać na app_logger

class ResourceManager(QObject):
    resources_loaded = pyqtSignal() # Sygnał emitowany po załadowaniu wszystkich kluczowych zasobów
    css_loaded = pyqtSignal(str)
    translations_loaded = pyqtSignal(dict)
    loading_failed = pyqtSignal(str, str)  # resource_name, error_message

    def __init__(self, base_dir: str, app_logger: logging.Logger, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.base_dir = base_dir
        self.logger = app_logger # Wymagany app_logger
        self.config = config if config else {}



        self.css_path = self.config.get("css_path", os.path.join("resources", "styles.qss"))
        self.translations_dir = self.config.get("translations_dir", "translations")

        # Pełne ścieżki
        self.full_css_path = os.path.join(self.base_dir, self.css_path)
        self.full_translations_dir = os.path.join(self.base_dir, self.translations_dir)

        self.css_loader = None
        self.translation_loader = None
        self.async_loader = AsyncResourceLoader(max_workers=2)
        self.translations: Dict[str, str] = {}
        self._loaded_resource_flags: Dict[str, bool] = {"main_css": False, "translations": False}

        self._setup_loaders()

        self.async_loader.resource_loaded.connect(self._handle_resource_loaded)
        self.async_loader.loading_failed.connect(self._handle_loading_failed) # Podłączono do lokalnej metody

    def _setup_loaders(self):
        self.logger.debug(f"Setting up CSS loader for path: {self.full_css_path}")
        self.css_loader = create_css_loader(self.full_css_path)
        lazy_loader.register_loader("main_css", self.css_loader)

        self.logger.debug(f"Setting up translations loader for dir: {self.full_translations_dir}")
        self.translation_loader = self._create_translation_loader()
        lazy_loader.register_loader("translations", self.translation_loader)

    def load_all_resources(self):
        self.logger.info("Requesting to load all resources...")
        self._loaded_resource_flags = {"main_css": False, "translations": False} # Reset flag
        self.async_loader.load_resource_async("main_css", self._load_css_optimized)
        self.async_loader.load_resource_async("translations", self._load_translations)

    @performance_monitor.measure_execution_time("css_loading")
    def _load_css_optimized(self) -> str:
        try:
            styles = lazy_loader.get_resource("main_css")
            self.logger.info("CSS styles successfully loaded (from cache or directly).")
            return styles
        except Exception as e:
            self.logger.error(f"Failed to load CSS from {self.full_css_path}: {e}", exc_info=True)
            # Zamiast emitować tutaj, _handle_loading_failed to zrobi
            # self.loading_failed.emit("main_css", str(e))
            raise # Rzuć wyjątek, aby async_loader go złapał i wyemitował loading_failed

    def _create_translation_loader(self):
        def load_translations_sync() -> Dict[str, str]: # Zmieniono nazwę dla jasności
            translation_manager = TranslationManager(logger=self.logger) # Przekaż logger
            # Upewnij się, że TranslationManager akceptuje logger
            self.logger.debug(f"Loading translations from: {self.full_translations_dir}")
            translations = translation_manager.load_translations(self.full_translations_dir)
            return translations
        return load_translations_sync

    def _load_translations(self) -> Dict[str, str]:
        try:
            translations = lazy_loader.get_resource("translations")
            self.logger.info("Translations successfully loaded (from cache or directly).")
            return translations
        except Exception as e:
            self.logger.error(f"Failed to load translations from {self.full_translations_dir}: {e}", exc_info=True)
            # self.loading_failed.emit("translations", str(e))
            raise # Rzuć wyjątek, aby async_loader go złapał i wyemitował loading_failed

    def _handle_resource_loaded(self, name: str, data: Any):
        self.logger.info(f"Resource '{name}' loaded successfully.")
        if name == "main_css":
            self._loaded_resource_flags["main_css"] = True
            self.css_loaded.emit(data)
        elif name == "translations":
            self._loaded_resource_flags["translations"] = True
            self.translations = data
            self.translations_loaded.emit(data)

        if all(self._loaded_resource_flags.values()):
            self.logger.info("All key resources have been loaded.")
            self.resources_loaded.emit()

    def _handle_loading_failed(self, resource_name: str, error_message: str):
        self.logger.error(f"Failed to load resource '{resource_name}': {error_message}")
        self.loading_failed.emit(resource_name, error_message)
        # Można dodać logikę np. ponawiania lub ładowania zasobów domyślnych

    def invalidate_cache(self, resource_name: Optional[str] = None):
        lazy_loader.clear_cache(resource_name)
        self.logger.info(f"Cache invalidated for {resource_name or 'all resources'}")

    def get_translations(self) -> Dict[str, str]:
        """Zwraca załadowane tłumaczenia."""
        return self.translations

    def cleanup(self):
        self.logger.debug("Cleaning up ResourceManager...")
        self.async_loader.cancel_all()
        self.async_loader.cleanup()
        self.logger.info("ResourceManager cleaned up.")

# Funkcja cached_with_ttl została usunięta z tego pliku.
# Jeśli jest potrzebna globalnie, powinna być w osobnym module utils.

```

**Checklista zależności:**

- [ ] `utils/application_startup.py`:
  - Musi poprawnie inicjalizować `AppLogger`, potencjalnie w dwóch etapach: raz z konfiguracją domyślną/minimalną, a potem wywołać `reconfigure` po załadowaniu pełnego `config.json`.
  - Musi przekazać `base_dir` do `AppLogger`.
  - Jeśli logowanie do UI jest używane, `ApplicationStartup` lub `main_app.py` musi stworzyć instancję `QtLogHandler` i przekazać ją do `AppLogger`.
- [ ] `main_app.py`:
  - Jeśli `main_app.py` jest odpowiedzialny za tworzenie widgetu logów UI i podłączanie sygnału z `QtLogHandler`, musi mieć dostęp do instancji `QtLogHandler` (lub jej sygnału).
- [ ] `config.json`:
  - Należy zweryfikować/zaktualizować klucze konfiguracyjne (np. `log_to_ui` zamiast `log_ui_to_console`) oraz dodać sekcję dla loggera, jeśli to potrzebne.

**Plan testów:**

1.  **Inicjalizacja**: Sprawdzić, czy `ResourceManager` inicjalizuje się poprawnie z `app_logger` i konfiguracją ścieżek.
2.  **Ładowanie CSS**:
    - Sprawdzić pomyślne ładowanie pliku CSS.
    - Sprawdzić emisję sygnału `css_loaded`.
    - Sprawdzić obsługę błędu (np. brak pliku CSS) i emisję `loading_failed`.
3.  **Ładowanie Tłumaczeń**:
    - Sprawdzić pomyślne ładowanie tłumaczeń.
    - Sprawdzić emisję sygnału `translations_loaded`.
    - Sprawdzić obsługę błędu (np. pusty katalog tłumaczeń, błędny format plików) i emisję `loading_failed`.
4.  **Sygnał `resources_loaded`**: Sprawdzić, czy sygnał jest emitowany po pomyślnym załadowaniu zarówno CSS, jak i tłumaczeń.
5.  **Cache (`lazy_loader`)**:
    - Sprawdzić, czy zasoby są ładowane z cache przy drugim żądaniu.
    - Przetestować `invalidate_cache` i sprawdzić, czy zasób jest ponownie ładowany ze źródła.
6.  **Asynchroniczność (`AsyncResourceLoader`)**:
    - Sprawdzić, czy ładowanie zasobów nie blokuje głównego wątku (jeśli to możliwe do zaobserwowania).
7.  **Logowanie**: Zweryfikować, czy wszystkie operacje są odpowiednio logowane przez `app_logger`.
8.  **Czyszczenie (`cleanup`)**: Sprawdzić, czy metoda `cleanup` jest wywoływana i loguje zakończenie czyszczenia.
9.  **Konfiguracja ścieżek**: Przetestować ładowanie zasobów z niestandardowych ścieżek zdefiniowanych w konfiguracji.

**Status tracking:**

- [ ] Analiza `utils/resource_manager.py` zakończona.
- [ ] Propozycje poprawek udokumentowane.
- [ ] Zależności zidentyfikowane.
- [ ] Plan testów przygotowany.
- [ ] Oczekiwanie na implementację i testy.

---

### Etap 5: Analiza `utils/config_cache.py` (`FileCache`, `ConfigurationCache`)

**Priorytet:** ŚREDNI
**Szacowany Czas:** 3-4 godziny
**Poziom Ryzyka:** ŚREDNI (zmiany w logice cache mogą wpłynąć na wydajność i spójność danych)

#### Pliki do Modyfikacji:

- `utils/config_cache.py` - Główny plik implementujący system cache

#### Poprawki Etapu 5:

##### 5.1 Refaktoryzacja i Usprawnienia w `FileCache` i `ConfigurationCache`

**Plik:** `utils/config_cache.py`

**Znalezione Problemy (na podstawie analizy kodu `utils/config_cache.py`):**

1.  **Logowanie**: Moduł używa `logger = logging.getLogger(__name__)`. Zmiana na użycie `app_logger` wymagałaby przekazania go do klas i funkcji w tym module.
2.  **Klasa `FileCache`**:
    - **Inicjalizacja**: Domyślny `cache_dir` to `.cache` w katalogu nadrzędnym modułu (`utils`). To może być nieoptymalne, jeśli aplikacja jest dystrybuowana; lepszy byłby katalog w danych użytkownika lub konfigurowalny.
    - **Metadane**: Przechowuje metadane w `cache_metadata.json`. Ładowanie i zapisywanie metadanych jest obsługiwane.
    - **Klucz cache**: Generowany na podstawie absolutnej ścieżki pliku i czasu modyfikacji (`st_mtime`). To zapewnia automatyczną inwalidację, gdy plik źródłowy się zmieni.
    - **Pobieranie z cache (`get`)**: Sprawdza istnienie pliku źródłowego. Jeśli cache jest ważny (plik cache istnieje i plik źródłowy nie jest nowszy), ładuje z cache (używając `pickle`). W przeciwnym razie używa `loader_func` do załadowania danych i zapisuje je w cache.
    - **Zapis do cache (`_store_in_cache`)**: Używa `pickle.HIGHEST_PROTOCOL`. Wykonuje `_cleanup_cache_if_needed`.
    - **Czyszczenie cache (`_cleanup_cache_if_needed`)**: Usuwa najstarsze (wg `last_access`) wpisy, jeśli całkowity rozmiar przekracza `max_cache_size`. Czyści do 80% limitu.
    - **Serializacja**: Używa `pickle` do przechowywania obiektów w cache. Może to być problematyczne, jeśli struktura cachowanych obiektów zmieni się między wersjami aplikacji, prowadząc do błędów deserializacji. JSON jest bezpieczniejszy dla prostych danych, ale `pickle` jest bardziej uniwersalny.
    - **Bezpieczeństwo wątków**: Komentarz wspomina o "Thread-safe operations", ale nie widać jawnych mechanizmów synchronizacji (np. `threading.Lock`) wokół dostępu do plików czy metadanych. Operacje na plikach w `pathlib` i standardowych modułach Pythona są generalnie thread-safe na poziomie systemu operacyjnego, ale modyfikacje współdzielonych struktur danych (jak `self.metadata`) mogą wymagać blokad, jeśli instancja `FileCache` jest współdzielona między wątkami i modyfikowana.
3.  **Klasa `ConfigurationCache`**:
    - Jest to fasada nad `FileCache`, dostarczająca specjalizowane metody `get_config`, `get_translations`, `get_css_styles`.
    - Każda z tych metod definiuje własną `loader_func` (dla JSON, JSON, plain text).
    - Używa dekoratora `@handle_error_gracefully` z `utils.exceptions`.
    - Nie implementuje logiki hot-reloadingu wspomnianej w docstringu (`_watchers` jest pusty i nieużywany).
4.  **Globalna instancja i Dekoratory**:
    - `_global_cache` i `get_global_cache()`: Implementują wzorzec singleton dla `ConfigurationCache`.
    - `@cached_config`: Dekorator do cachowania funkcji ładujących konfigurację. Używa globalnego cache.
    - `@cached_file_operation`: Bardziej generyczny dekorator, który próbuje automatycznie wybrać metodę cache na podstawie rozszerzenia pliku (`.json`, `.qss`) lub używa określonego `cache_type`.
5.  **Funkcja `get_file_hash`**:
    - Używa `hashlib.md5()` do generowania hasha pliku. Jest dekorowana `@lru_cache`.
    - Nie jest bezpośrednio używana przez `FileCache` ani `ConfigurationCache` (które polegają na `st_mtime`). Może być używana gdzie indziej lub była częścią alternatywnego mechanizmu inwalidacji.
6.  **Logowanie**: Komunikaty logów są po angielsku.
7.  **Internacjonalizacja**: Brak tekstów do tłumaczenia w tym module (poza komentarzami i docstringami).
8.  **Czystość Kodu i Potencjalne Problemy**:
    - **Domyślna lokalizacja `.cache`**: Może powodować problemy z uprawnieniami zapisu, jeśli aplikacja jest zainstalowana w miejscu chronionym. Lepsze byłoby użycie `appdirs` lub podobnej biblioteki do znalezienia odpowiedniego katalogu cache użytkownika.
    - **Ryzyko `pickle`**: Jak wspomniano, `pickle` może być problematyczny przy zmianach definicji klas. Dla konfiguracji (JSON), tłumaczeń (JSON) i CSS (text), `pickle` nie jest konieczny; można by zapisywać te dane w ich natywnym formacie lub jako JSON, co byłoby bezpieczniejsze i bardziej przenośne.
    - **Brak hot-reloading**: Funkcjonalność hot-reloading wspomniana w docstringu `ConfigurationCache` nie jest zaimplementowana.
    - **Potencjalny brak bezpieczeństwa wątków**: Jeśli `FileCache` lub globalna instancja `ConfigurationCache` są używane z wielu wątków, modyfikacje `self.metadata` i operacje plikowe powinny być chronione blokadami.

**Proponowane Poprawki:**

1.  **Lokalizacja Katalogu Cache (`FileCache.__init__`)**:
    - Zamiast domyślnego `.cache` w katalogu projektu, użyć standardowej lokalizacji dla danych cache aplikacji (np. używając biblioteki `appdirs` lub `platformdirs` do znalezienia odpowiedniej ścieżki, np. `user_cache_dir`). Powinno to być konfigurowalne.
2.  **Serializacja (`FileCache._store_in_cache`, `FileCache.get`)**:
    - Dla typów danych obsługiwanych przez `ConfigurationCache` (JSON, text), unikać `pickle`. Zapisywać je jako pliki `.json` lub `.txt` bezpośrednio. `FileCache` mógłby przyjmować opcjonalne funkcje `serializer` i `deserializer` lub obsługiwać różne formaty na podstawie rozszerzenia pliku cache.
    - Jeśli `pickle` jest nadal potrzebny dla ogólnego zastosowania `FileCache`, zachować go, ale z wyraźnym ostrzeżeniem o potencjalnych problemach.
3.  **Bezpieczeństwo Wątków (`FileCache`)**:
    - Dodać `threading.Lock` do ochrony dostępu do `self.metadata` i operacji na plikach, jeśli instancje mają być współdzielone między wątkami.
4.  **Hot-reloading (`ConfigurationCache`)**:
    - Jeśli hot-reloading jest pożądaną funkcją, zaimplementować ją. Wymagałoby to monitorowania plików źródłowych (np. za pomocą `watchdog` lub prostszego mechanizmu opartego na `QFileSystemWatcher` jeśli w kontekście Qt) i automatycznego odświeżania cache oraz emitowania sygnału o zmianie konfiguracji.
    - Jeśli nie jest planowany, usunąć wzmiankę z docstringu i atrybut `_watchers`.
5.  **Użycie `app_logger`**:
    - Przekazać instancję `AppLogger` do `FileCache` i `ConfigurationCache` (lub do globalnej instancji) i używać jej zamiast `logging.getLogger(__name__)` dla spójności logowania w aplikacji.
6.  **Nieużywana funkcja `get_file_hash`**:
    - Jeśli `get_file_hash` nie jest używana, rozważyć jej usunięcie, aby uprościć kod. Jeśli jest używana gdzie indziej, może pozostać.
7.  **Konfiguracja `FileCache`**: Rozważyć przekazanie `max_cache_size` do `ConfigurationCache` i dalej do `FileCache` z pliku konfiguracyjnego aplikacji.
8.  **Typowanie**: Uzupełnić type hints, gdzie brakuje.

**Kod po zmianach (fragmenty koncepcyjne):**

```python
# filepath: c:\\_cloud\\_CFAB_UI_manager\\utils\\config_cache.py
# ... (importy) ...
import threading # Dla Lock
from platformdirs import user_cache_dir # Lepsza lokalizacja cache

# logger = logging.getLogger(__name__) # Zastąpione przez app_logger

class FileCache:
    def __init__(self, cache_dir: Optional[str] = None, max_cache_size_mb: int = 50, app_logger: Optional[logging.Logger] = None):
        self.app_logger = app_logger if app_logger else logging.getLogger("FileCache") # Fallback logger

        if cache_dir is None:
            # Użyj standardowego katalogu cache dla aplikacji
            # Nazwa aplikacji i autora mogą być pobierane z konfiguracji lub stałych
            app_name = "CFAB_UI_Manager" # Przykładowa nazwa
            app_author = "CFAB" # Przykładowy autor
            cache_dir = user_cache_dir(app_name, app_author)

        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.app_logger.error(f"Could not create cache directory {self.cache_dir}: {e}. Caching might be disabled or use a temporary location.")
            # Można ustawić tymczasowy katalog cache lub wyłączyć cachowanie
            # self.cache_dir = Path(tempfile.gettempdir()) / "cfab_ui_cache"
            # self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_cache_size = max_cache_size_mb * 1024 * 1024
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._lock = threading.Lock() # Dla operacji na metadanych i plikach
        self.metadata = self._load_metadata()
        self.app_logger.debug(f"FileCache initialized with cache_dir: {self.cache_dir}")

    def _load_metadata(self) -> Dict:
        with self._lock:
            # ... (logika ładowania metadanych, użyj self.app_logger) ...
            # ... existing code ...
            pass # Placeholder

    def _save_metadata(self) -> None:
        with self._lock:
            # ... (logika zapisywania metadanych, użyj self.app_logger) ...
            # ... existing code ...
            pass # Placeholder

    # ... (_generate_cache_key bez zmian) ...

    @performance_monitor.measure_execution_time("cache_get")
    def get(self, source_file: Union[str, Path], loader_func: callable = None, serializer: str = 'pickle') -> Optional[Any]:
        source_path = Path(source_file)
        if not source_path.exists():
            self.app_logger.warning(f"Source file does not exist: {source_path}")
            return None

        cache_key = self._generate_cache_key(source_path)
        # Dodaj rozszerzenie na podstawie serializatora dla jasności
        cache_file_ext = ".dat" if serializer == 'pickle' else f".{serializer}"
        cache_file = self.cache_dir / f"{cache_key}{cache_file_ext}"

        with self._lock:
            if cache_file.exists():
                try:
                    cache_mtime = cache_file.stat().st_mtime
                    source_mtime = source_path.stat().st_mtime
                    if source_mtime <= cache_mtime:
                        self.app_logger.debug(f"Cache hit for {source_path.name}, loading from {cache_file}")
                        if serializer == 'pickle':
                            with open(cache_file, "rb") as f:
                                data = pickle.load(f)
                        elif serializer == 'json':
                            with open(cache_file, "r", encoding='utf-8') as f:
                                data = json.load(f)
                        elif serializer == 'text':
                            with open(cache_file, "r", encoding='utf-8') as f:
                                data = f.read()
                        else:
                            self.app_logger.error(f"Unknown serializer: {serializer}")
                            return None
                        # ... (aktualizacja metadanych) ...
                        return data
                    else:
                        self.app_logger.debug(f"Cache expired for {source_path.name}")
                except Exception as e:
                    self.app_logger.warning(f"Error reading cache file {cache_file}: {e}")

        # Cache miss or invalid
        if loader_func is None:
            self.app_logger.warning(f"No loader function provided for {source_path}")
            return None
        try:
            data = loader_func(source_path)
            self._store_in_cache(cache_key, cache_file, data, source_path, serializer)
            return data
        except Exception as e:
            self.app_logger.error(f"Error loading data from {source_path}: {e}", exc_info=True)
            return None

    def _store_in_cache(self, cache_key: str, cache_file: Path, data: Any, source_path: Path, serializer: str = 'pickle') -> None:
        with self._lock:
            try:
                self._cleanup_cache_if_needed() # Powinno być również pod self._lock
                with open(cache_file, "wb" if serializer == 'pickle' else "w", encoding=None if serializer == 'pickle' else 'utf-8') as f:
                    if serializer == 'pickle':
                        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                    elif serializer == 'json':
                        json.dump(data, f, indent=2)
                    elif serializer == 'text':
                        f.write(data)
                    else:
                        self.app_logger.error(f"Unknown serializer for storing: {serializer}")
                        return
                # ... (aktualizacja metadanych) ...
                self.app_logger.debug(f"Cached data for {source_path.name} using {serializer} to {cache_file}")
            except Exception as e:
                self.app_logger.error(f"Error storing cache for {source_path}: {e}", exc_info=True)

    def _cleanup_cache_if_needed(self) -> None:
        # Ta metoda powinna być wywoływana wewnątrz bloku self._lock
        # ... (logika czyszczenia, użyj self.app_logger) ...
        # ... existing code ...
        pass # Placeholder

    def clear(self) -> None:
        with self._lock:
            # ... (logika czyszczenia, użyj self.app_logger) ...
            # ... existing code ...
            pass # Placeholder

    # ... (get_stats bez zmian, ale może używać self.app_logger) ...

class ConfigurationCache:
    def __init__(self, cache_dir: Optional[str] = None, app_logger: Optional[logging.Logger] = None, max_cache_size_mb: int = 50):
        self.app_logger = app_logger if app_logger else logging.getLogger("ConfigurationCache")
        self.file_cache = FileCache(cache_dir, max_cache_size_mb, self.app_logger)
        # self._watchers = {} # Usunięto, jeśli hot-reloading nie jest implementowany
        self._cached_configs = {} # Może nie być potrzebne, jeśli FileCache jest wystarczający
        self.app_logger.debug("ConfigurationCache initialized.")

    @handle_error_gracefully
    def get_config(self, config_path: Union[str, Path], validator_func: callable = None) -> Optional[Dict]:
        def config_loader(path):
            # ... (logika ładowania JSON, użyj self.app_logger) ...
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
            if validator_func:
                config = validator_func(config)
            return config
        return self.file_cache.get(config_path, config_loader, serializer='json')

    def get_translations(self, translations_path: Union[str, Path]) -> Optional[Dict[str, str]]:
        def translations_loader(path):
            # ... (logika ładowania tłumaczeń, użyj self.app_logger) ...
            return TranslationManager.load_translations(path)
        return self.file_cache.get(translations_path, translations_loader, serializer='json')

    def get_css_styles(self, css_path: Union[str, Path]) -> Optional[str]:
        def css_loader(path):
            # ... (logika ładowania CSS, użyj self.app_logger) ...
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return self.file_cache.get(css_path, css_loader, serializer='text')

# Globalna instancja - inicjalizacja powinna przyjmować app_logger i konfigurację cache
_global_cache_instance: Optional[ConfigurationCache] = None
_global_cache_lock = threading.Lock()

def get_global_cache(app_logger: Optional[logging.Logger] = None, cache_settings: Optional[Dict] = None) -> ConfigurationCache:
    global _global_cache_instance
    if _global_cache_instance is None:
        with _global_cache_lock:
            if _global_cache_instance is None:
                cs = cache_settings if cache_settings else {}
                _global_cache_instance = ConfigurationCache(
                    cache_dir=cs.get('cache_dir'),
                    app_logger=app_logger,
                    max_cache_size_mb=cs.get('max_cache_size_mb', 50)
                )
    return _global_cache_instance

# Dekoratory powinny pobierać logger i ustawienia z kontekstu aplikacji, jeśli to możliwe,
# lub być konfigurowane przy starcie.
# ... (aktualizacja dekoratorów, aby używały skonfigurowanej instancji cache) ...

# config_cache = get_global_cache() # Inicjalizacja powinna być bardziej kontrolowana przez aplikację

```

**Checklista zależności:**

- [ ] `utils/application_startup.py` (lub inny główny moduł aplikacji):
  - Należy upewnić się, że standardowy logger Pythona używany przez moduł `utils.exceptions` (tj. `logging.getLogger("utils.exceptions")`) jest skonfigurowany tak, aby jego komunikaty były przesyłane do tych samych handlerów (plik, konsola, UI) co główny `AppLogger` aplikacji. To zapewni, że błędy logowane automatycznie przez `CFABError` pojawią się w głównych logach aplikacji bez potrzeby przekazywania instancji `AppLogger` do klas wyjątków.
- [ ] Wszystkie miejsca używające `handle_error_gracefully` lub `log_error_with_context` będą korzystać ze zaktualizowanej logiki.
- [ ] (Opcjonalnie) `from typing import Any, Dict, Optional` na początku pliku.

**Plan testów:**

1.  **Logowanie `CFABError`**: Sprawdzić, czy rzucenie dowolnego wyjątku dziedziczącego po `CFABError` powoduje pojedynczy, poprawnie sformatowany wpis w logach aplikacji (zgodnie z konfiguracją `AppLogger`).
2.  **Logowanie przez `handle_error_gracefully`**:
    - Przetestować dekorator na funkcji rzucającej `CFABError` – sprawdzić, czy błąd jest logowany raz (przez `CFABError.__init__`) i poprawnie rzucany dalej.
    - Przetestować dekorator na funkcji rzucającej standardowy wyjątek (np. `ValueError`) – sprawdzić, czy jest on opakowywany w `CFABError` (z kodem `UNEXPECTED`), logowany raz i rzucany dalej.
3.  **Logowanie przez `log_error_with_context`**:
    - Przekazać instancję `CFABError` – sprawdzić, czy do logów dodawana jest tylko informacja o dodatkowym kontekście, a szczegóły błędu są aktualizowane, bez duplikowania pełnego logu błędu.
    - Przekazać standardowy wyjątek – sprawdzić, czy jest on logowany jako "Unhandled error" z pełnym tracebackiem i dodatkowym kontekstem.
4.  **Struktura logów**: Zweryfikować, czy logi błędów zawierają kod błędu, wiadomość, szczegóły (`details`), informacje o oryginalnym wyjątku (jeśli dotyczy) oraz `exc_info` tam, gdzie to stosowne.
5.  **Typowanie**: Upewnić się, że zmiany w typowaniu (np. `Optional[Dict[str, Any]]`) nie powodują problemów.
6.  **Działanie `ErrorCode`**: Sprawdzić, czy kody błędów są poprawnie przypisywane i logowane.

**Status tracking:**

- [ ] Analiza `utils/exceptions.py` zakończona.
- [ ] Propozycje poprawek udokumentowane.
- [ ] Zależności zidentyfikowane.
- [ ] Plan testów przygotowany.
- [ ] Oczekiwanie na implementację i testy.

---

### Etap 8: Analiza `utils/improved_thread_manager.py` (`ThreadManager`, `ImprovedWorkerTask`)

**Priorytet:** WYSOKI (kluczowy dla operacji w tle i stabilności aplikacji)
**Szacowany Czas:** 3-4 godziny
**Poziom Ryzyka:** WYSOKI (zmiany w zarządzaniu wątkami mogą wpłynąć na wydajność i responsywność)

#### Pliki do Modyfikacji:

- `utils/improved_thread_manager.py`

#### Poprawki Etapu 8:

##### 8.1 Refaktoryzacja i Usprawnienia w Zarządzaniu Wątkami

**Plik:** `utils/improved_thread_manager.py`

**Znalezione Problemy:**

1.  **Logowanie**: Zarówno `ThreadManager`, `ImprovedWorkerTask`, jak i `LogQueue` używają `logger = logging.getLogger(__name__)`. Dla spójności z resztą aplikacji, powinny przyjmować instancję `AppLogger` i jej używać.
2.  **Klasa `LogQueue`**: Ta klasa implementuje własny mechanizm kolejkowania i przetwarzania logów w osobnym wątku. Wydaje się to być redundantne, jeśli `AppLogger` (z jego standardowymi, wątkowo-bezpiecznymi handlerami) jest używany. Bezpośrednie logowanie do `AppLogger` z zadań roboczych powinno być wystarczające i prostsze.
3.  **Anulowanie Zadań (`cancel_task`)**: Metoda `ThreadManager.cancel_task(task_id: str)` jest oznaczona jako problematyczna z powodu użycia `weakref.WeakSet` dla `active_tasks`. `WeakSet` nie pozwala na łatwe wyszukiwanie obiektów po atrybucie (jak `task_id`) w celu ich anulowania. Obecna implementacja zwraca `False` i loguje ostrzeżenie.
4.  **Metoda Kompatybilności `run_in_thread`**: Ta metoda w `ThreadManager` służy do zachowania kompatybilności ze starszym API. Jej implementacja jest dość złożona, tworzy własne obiekty `ImprovedWorkerTask` i pomocnicze obiekty sygnałowe, co częściowo dubluje logikę `submit_task`. Może to prowadzić do niespójności w śledzeniu zadań.
5.  **Konfiguracja**: Parametry takie jak `max_workers` i `task_timeout` są przekazywane w konstruktorze `ThreadManager`. Mogłyby być ładowane z centralnej konfiguracji aplikacji.
6.  **Nazewnictwo**: Nazwa pliku to `improved_thread_manager.py`, ale główna klasa w nim to `ThreadManager`. Komentarz w kodzie (`ThreadManager(QObject): # Zmieniono nazwę z ImprovedThreadManager`) sugeruje, że nazwa klasy została zmieniona. Dla spójności warto to ujednolicić.
7.  **Przekazywanie `app_logger` do `ImprovedWorkerTask`**: `ImprovedWorkerTask` powinien również otrzymywać i używać instancji `app_logger`.

**Proponowane Poprawki:**

1.  **Ujednolicenie Logowania**:
    - Zmodyfikować konstruktory `ThreadManager` i `ImprovedWorkerTask`, aby przyjmowały instancję `app_logger` (z `utils.logger.AppLogger`).
    - Wszystkie operacje logowania w tych klasach powinny używać przekazanego `app_logger`.
    - Parametr `enable_logging` w `ThreadManager` może stać się zbędny, jeśli `app_logger` jest zawsze dostarczany, a jego poziom i handlery są konfigurowane centralnie.
2.  **Usunięcie `LogQueue`**:
    - Całkowicie usunąć klasę `LogQueue`.
    - Zamiast `self.log_queue.add_log(...)`, `ThreadManager` i `ImprovedWorkerTask` powinny bezpośrednio wywoływać metody `app_logger` (np. `self.app_logger.debug(...)`).
3.  **Poprawa `cancel_task`**:
    - **Opcja A (jeśli anulowanie po ID jest krytyczne):**
      - `ThreadManager` powinien utrzymywać słownik mapujący `task_id` na `weakref(task_object)`.
      - `ImprovedWorkerTask` powinien przechowywać swój `task_id` jako atrybut.
      - `submit_task` dodawałby zadanie do `WeakSet` oraz do tego słownika.
      - `cancel_task` używałby słownika do znalezienia i anulowania zadania.
    - **Opcja B (jeśli można zmienić API lub anulowanie po ID nie jest kluczowe):**
      - Rozważyć usunięcie `cancel_task(task_id)` lub zmianę API, np. na anulowanie przez przekazanie samego obiektu zadania.
4.  **Refaktoryzacja `run_in_thread`**:
    - **Opcja A (preferowana):** Zmodyfikować kod używający `run_in_thread`, aby korzystał z nowszego i czystszego API `submit_task`.
    - **Opcja B (jeśli kompatybilność musi być zachowana):** Uprościć `run_in_thread`. Metoda `submit_task` powinna zwracać obiekt `ImprovedWorkerTask` (a nie tylko `task_id`). `run_in_thread` wywoływałaby `submit_task`, a następnie tworzyła prosty obiekt-wrapper wokół zwróconego `ImprovedWorkerTask`, który eksponowałby sygnały (`finished`, `error`) i metodę `cancel` zgodnie ze starym API.
5.  **Konfiguracja Zewnętrzna**:
    - Umożliwić konfigurację `max_workers` i domyślnego `task_timeout` dla `ThreadManager` poprzez główny plik konfiguracyjny aplikacji (np. `config.json`). Te wartości byłyby przekazywane do konstruktora `ThreadManager`.
6.  **Nazewnictwo (Niski priorytet)**:
    - Rozważyć zmianę nazwy pliku na `thread_manager.py` lub klasy z powrotem na `ImprovedThreadManager` dla spójności. Na potrzeby tej dokumentacji zakładamy, że klasa pozostaje `ThreadManager`.

**Kod po zmianach (fragmenty koncepcyjne):**

```python
# filepath: c:\\_cloud\\_CFAB_UI_manager\\utils\\improved_thread_manager.py
# import logging # Usunięto, będzie przekazywany app_logger
import queue
import threading
import time
import weakref
from typing import Any, Callable, Dict, List, Optional, Tuple # Dodano Tuple

from PyQt6.QtCore import QObject, QRunnable, QThread, QThreadPool, QTimer, pyqtSignal

# logger = logging.getLogger(__name__) # Usunięto

class WorkerSignals(QObject):
    # ... (bez zmian) ...
    pass

class ImprovedWorkerTask(QRunnable):
    def __init__(self, func: Callable, app_logger: logging.Logger, task_id: str, timeout: int = 300, *args, **kwargs):
        super().__init__()
        self.func = func
        self.app_logger = app_logger # Przekazany logger
        self.task_id = task_id # ID zadania
        self.args = args
        self.kwargs = kwargs
        self.timeout = timeout # Timeout nie jest aktywnie używany do przerwania func w tej implementacji
        self.signals = WorkerSignals()
        self._is_cancelled = False

    def run(self):
        try:
            self.app_logger.debug(f"Task {self.task_id} starting: {self.func.__name__}")
            if self._is_cancelled:
                self.app_logger.debug(f"Task {self.task_id} was cancelled before execution.")
                return

            result = self.func(*self.args, **self.kwargs)

            if not self._is_cancelled:
                self.signals.finished.emit(result)
                self.app_logger.debug(f"Task {self.task_id} completed: {self.func.__name__}")
            else:
                self.app_logger.debug(f"Task {self.task_id} was cancelled during execution.")

        except Exception as e:
            self.app_logger.error(f"Task {self.task_id} failed: {self.func.__name__}: {e}", exc_info=True)
            if not self._is_cancelled:
                self.signals.error.emit(e)

    def cancel(self):
        self.app_logger.debug(f"Cancelling task {self.task_id}: {self.func.__name__}")
        self._is_cancelled = True

# Klasa LogQueue została usunięta

class ThreadManager(QObject):
    def __init__(
        self,
        app_logger: logging.Logger,
        max_workers: int = 4,
        task_timeout: int = 300 # Domyślny timeout dla zadań
    ):
        super().__init__()
        self.app_logger = app_logger
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(max_workers)

        self.active_tasks_refs = weakref.WeakSet() # Do śledzenia aktywnych QRunnables
        self.task_id_to_worker_ref: Dict[str, weakref.ReferenceType[ImprovedWorkerTask]] = {} # Dla cancel_task

        self.app_logger.info(f"ThreadManager initialized with {max_workers} workers.")

        self.default_task_timeout = task_timeout
        self.task_counter = 0

        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(30000)  # Cleanup co 30 sekund

        self._start_time = time.time()
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._lock = threading.Lock() # Dla statystyk

    def submit_task(self, func: Callable, *args, **kwargs) -> Tuple[str, ImprovedWorkerTask]:
        timeout = self.default_task_timeout
        # ... (logika wyciągania timeout z args/kwargs jak wcześniej) ...

        with self._lock:
            self.task_counter += 1
            task_id = f"task_{self.task_counter}"

        task = ImprovedWorkerTask(func, self.app_logger, task_id, timeout, *args, **kwargs)
        task_ref = weakref.ref(task)
        self.active_tasks_refs.add(task)
        self.task_id_to_worker_ref[task_id] = task_ref

        def on_finished(result):
            with self._lock:
                self._tasks_completed += 1
            self.app_logger.debug(f"Task {task_id} finished signal received. Result: {result}")
            self._remove_task_mapping(task_id)

        def on_error(error):
            with self._lock:
                self._tasks_failed += 1
            self.app_logger.error(f"Task {task_id} error signal received: {error}", exc_info=isinstance(error, Exception))
            self._remove_task_mapping(task_id)

        task.signals.finished.connect(on_finished)
        task.signals.error.connect(on_error)

        self.thread_pool.start(task)
        self.app_logger.debug(f"Submitted task {task_id}: {func.__name__}")
        return task_id, task # Zwracamy ID i obiekt zadania

    def _remove_task_mapping(self, task_id: str):
        if task_id in self.task_id_to_worker_ref:
            del self.task_id_to_worker_ref[task_id]
            self.app_logger.debug(f"Removed task ID {task_id} from mapping.")

    def cancel_task(self, task_id: str) -> bool:
        task_ref = self.task_id_to_worker_ref.get(task_id)
        if task_ref:
            task = task_ref()
            if task:
                task.cancel()
                # self._remove_task_mapping(task_id) # Usunięcie mapowania nastąpi w on_finished/on_error
                self.app_logger.info(f"Cancellation requested for task {task_id}")
                return True
            else:
                self.app_logger.warning(f"Task {task_id} ref is dead, already collected?")
                self._remove_task_mapping(task_id) # Usuń nieaktualne mapowanie
        else:
            self.app_logger.warning(f"Cannot cancel task: No active task found with ID {task_id}")
        return False

    def get_active_task_count(self) -> int:
        # Liczy żywe referencje w task_id_to_worker_ref
        count = 0
        for task_id in list(self.task_id_to_worker_ref.keys()): # Iteruj po kopii kluczy
            ref = self.task_id_to_worker_ref.get(task_id)
            if ref and ref(): # Jeśli referencja istnieje i obiekt wciąż żyje
                count += 1
            elif ref is None or not ref(): # Jeśli ref jest None lub obiekt nie żyje
                self._remove_task_mapping(task_id) # Oczyść nieaktualne wpisy
        return count

    # ... (get_pool_info, _log_rate_limiter, get_thread_health_status, get_performance_metrics - używają self.app_logger) ...
    # ... (cleanup_finished_threads - może logować stan, używa self.app_logger) ...

    def _periodic_cleanup(self):
        # ... (loguje statystyki używając self.app_logger) ...
        # Sprawdź task_id_to_worker_ref pod kątem martwych referencji
        active_count_map = 0
        for task_id in list(self.task_id_to_worker_ref.keys()):
            ref = self.task_id_to_worker_ref.get(task_id)
            if ref and ref():
                active_count_map +=1
            else:
                self.app_logger.debug(f"Periodic cleanup removing dead ref for task_id: {task_id}")
                del self.task_id_to_worker_ref[task_id]
        self.app_logger.debug(f"Periodic cleanup: {active_count_map} tasks in id_map. {len(self.active_tasks_refs)} refs in WeakSet.")

    def wait_for_completion(self, timeout: int = 30) -> bool:
        self.app_logger.debug(f"Waiting for all tasks to complete (timeout: {timeout}s)")
        return self.thread_pool.waitForDone(timeout * 1000)

    def cleanup(self):
        self.app_logger.info("Starting ThreadManager cleanup...")
        self.cleanup_timer.stop()

        tasks_to_cancel_ids = list(self.task_id_to_worker_ref.keys())
        self.app_logger.debug(f"Requesting cancellation for {len(tasks_to_cancel_ids)} active tasks during cleanup.")
        for task_id in tasks_to_cancel_ids:
            self.cancel_task(task_id)

        if not self.wait_for_completion(10):
            self.app_logger.warning("Some tasks did not complete within timeout during cleanup")

        # LogQueue już nie istnieje, więc nie ma self.log_queue.stop()
        self.thread_pool.clear()
        self.app_logger.info("ThreadManager cleanup completed")

    def run_in_thread(self, func, *args, **kwargs):
        self.app_logger.debug(f"Legacy run_in_thread called for: {func.__name__}")
        # Uproszczona implementacja: użyj submit_task i zwróć obiekt kompatybilny
        # Wyciągnij 'on_finished', 'on_error' z kwargs, jeśli są tam dla starego API
        legacy_on_finished = kwargs.pop('on_finished', None)
        legacy_on_error = kwargs.pop('on_error', None)

        task_id, task_object = self.submit_task(func, *args, **kwargs)

        # Stwórz prosty obiekt QObject do eksponowania sygnałów dla starego API
        # Stary kod mógł oczekiwać obiektu workera z sygnałami .finished i .error
        worker_compat_obj = QObject()
        # Bezpośrednie przypisanie sygnałów z task_object.signals
        worker_compat_obj.finished = task_object.signals.finished
        worker_compat_obj.error = task_object.signals.error
        # Można też dodać metodę cancel, jeśli stary API tego oczekiwał
        # worker_compat_obj.cancel = task_object.cancel

        # Jeśli stary kod podał callbacki, podłącz je
        if legacy_on_finished:
            worker_compat_obj.finished.connect(legacy_on_finished)
        if legacy_on_error:
            worker_compat_obj.error.connect(legacy_on_error)

        # self.workers.append(worker_compat_obj) # Jeśli lista self.workers jest nadal potrzebna
        self.app_logger.debug(f"Submitted task {task_id} with legacy wrapper.")
        return worker_compat_obj
```

**Checklista zależności:**

- [ ] `utils/application_startup.py` (lub inny główny moduł aplikacji):
  - Musi tworzyć i przekazywać instancję `AppLogger` do `ThreadManager`.
  - Może odczytywać konfigurację `max_workers` i `default_task_timeout` z `config.json` i przekazywać je do `ThreadManager`.
- [ ] Wszystkie części aplikacji używające `ThreadManager` (bezpośrednio lub przez `run_in_thread`) będą korzystać ze zaktualizowanej implementacji.
- [ ] Jeśli `run_in_thread` jest nadal używane, upewnić się, że przekazywane callbacki (`on_finished`, `on_error`) są poprawnie obsługiwane przez uproszczony wrapper.

**Plan testów:**

1.  **Logowanie**: Sprawdzić, czy wszystkie komunikaty z `ThreadManager` i `ImprovedWorkerTask` są logowane przez przekazaną instancję `AppLogger` i pojawiają się w skonfigurowanych miejscach (plik, konsola, UI).
2.  **Przesyłanie zadań (`submit_task`)**:
    - Przetestować pomyślne wykonanie zadania i sygnał `finished`.
    - Przetestować zadanie rzucające wyjątek i sygnał `error`.
    - Sprawdzić, czy `task_id` i obiekt zadania są poprawnie zwracane.
3.  **Anulowanie zadań (`cancel_task`)**:
    - Przesłać zadanie, a następnie je anulować przed jego zakończeniem. Sprawdzić, czy zadanie jest poprawnie oznaczane jako anulowane i czy nie emituje `finished`/`error` po anulowaniu.
    - Spróbować anulować nieistniejące zadanie lub zadanie już zakończone.
4.  **Metoda `run_in_thread` (jeśli zachowana)**:
    - Przetestować kompatybilność wsteczną, upewniając się, że zadania są wykonywane, a sygnały `finished`/`error` (lub podłączone callbacki) działają zgodnie z oczekiwaniami starego API.
5.  **Zarządzanie pulą wątków (`QThreadPool`)**:
    - Sprawdzić, czy `max_workers` jest respektowane.
    - Monitorować aktywne wątki i zadania.
6.  **Statystyki i stan (`get_pool_info`, `get_performance_metrics`, `get_thread_health_status`)**:
    - Zweryfikować poprawność zwracanych informacji.
7.  **Czyszczenie (`cleanup`, `_periodic_cleanup`)**:
    - Sprawdzić, czy metoda `cleanup` poprawnie zatrzymuje wszystkie zadania, timery i czyści zasoby.
    - Sprawdzić, czy `_periodic_cleanup` poprawnie usuwa odwołania do zakończonych/anulowanych zadań z `task_id_to_worker_ref`.
8.  **Konfiguracja**: Przetestować działanie z różnymi wartościami `max_workers` i `default_task_timeout` (jeśli są ładowane z konfiguracji).
9.  **Wycieki pamięci / zasobów**: (Trudniejsze do automatyzacji) Obserwować użycie pamięci i zasobów przy długotrwałym działaniu i wielokrotnym przesyłaniu zadań, aby upewnić się, że `WeakSet` i `weakref` działają zgodnie z oczekiwaniami.

**Status tracking:**

- [ ] Analiza `utils/improved_thread_manager.py` zakończona.
- [ ] Propozycje poprawek udokumentowane.
- [ ] Zależności zidentyfikowane.
- [ ] Plan testów przygotowany.
- [ ] Oczekiwanie na implementację i testy.

---

(Kolejne etapy będą dodawane tutaj)
