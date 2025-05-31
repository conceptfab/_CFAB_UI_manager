<!-- filepath: c:\_cloud\_CFAB_UI_manager\corrections.md -->

## ETAP 2: SZCZEGÓŁOWA ANALIZA I KOREKCJE - `main_app.py`

### 📋 Identyfikacja

- **Plik główny:** `main_app.py`
- **Priorytet:** 🔴 WYSOKI PRIORYTET
- **Zależności:** `UI/main_window.py`, `utils/application_startup.py`, `utils/enhanced_splash.py`, `utils/exceptions.py`, `utils/logger.py`, `utils/performance_optimizer.py`, `utils/validators.py`, `config.json`, `resources/img/icon.png`, `resources/img/splash.jpg`

### 🔍 Analiza problemów

1.  **Błędy krytyczne:**

    - Brak bezpośrednich błędów krytycznych uniemożliwiających uruchomienie, jednak złożoność inicjalizacji w bloku `if __name__ == "__main__":` może prowadzić do trudności w debugowaniu i testowaniu.
    - Potencjalny problem: Jeśli `app.initialize()` zwróci `False`, aplikacja zakończy działanie z `sys.exit(1)`, ale `main_win` i `splash` mogą nie zostać poprawnie zainicjalizowane, co może prowadzić do błędów przy próbie odwołania się do nich w nieprzewidzianych sytuacjach (choć obecna logika wydaje się to obsługiwać).

2.  **Optymalizacje:**

    - **Struktura klasy `Application`:**
      - Inicjalizacja `self._config` wartościami domyślnymi jest dobra, ale mogłaby być połączona z logiką ładowania konfiguracji w `ApplicationStartup` dla większej spójności.
      - Przechowywanie `base_dir` jako atrybutu instancji jest w porządku, ale warto upewnić się, że jest to spójne z innymi częściami aplikacji.
    - **Logika w `if __name__ == "__main__":`:**
      - Blok ten jest bardzo długi i zawiera wiele logiki związanej z inicjalizacją UI, splash screenem i monitorowaniem wydajności. Warto rozważyć przeniesienie części tej logiki do dedykowanych metod w klasie `Application` lub nowej klasy zarządzającej cyklem życia aplikacji, aby zwiększyć czytelność i testowalność.
      - Tworzenie ścieżek do zasobów (ikona, splash) jest powtarzalne. Można to scentralizować w `ResourceManager` (jeśli istnieje i jest odpowiednio rozbudowany) lub metodzie pomocniczej.
      - Symulacja postępu zadań dla splash screena (`progress_tracker.start_task` / `complete_task`) jest wykonana sekwencyjnie i statycznie. W rzeczywistej aplikacji postęp powinien być aktualizowany dynamicznie w miarę wykonywania rzeczywistych zadań inicjalizacyjnych.
      - Użycie `QTimer.singleShot` z lambdą do finalizacji zadań splash screena jest funkcjonalne, ale może być mniej czytelne. Rozważenie dedykowanej metody mogłoby poprawić przejrzystość.
    - **Ładowanie konfiguracji:**
      - Klasa `ConfigLoader` jest zdefiniowana, ale nie jest używana w `main_app.py`. Zamiast tego `ApplicationStartup` prawdopodobnie obsługuje ładowanie konfiguracji. Należy zweryfikować, czy `ConfigLoader` jest potrzebny, czy też jego funkcjonalność jest zduplikowana lub nieużywana. Jeśli jest używany w innym miejscu, to jest w porządku.
      - Walidacja konfiguracji odbywa się za pomocą `ConfigValidator.validate_config_file(config_path)` w `ConfigLoader`. Należy upewnić się, że `ApplicationStartup` również korzysta z tej walidacji lub ma własny, równie solidny mechanizm.
    - **Przekazywanie zależności:**
      - `app_logger` jest przekazywany do `MainWindow` warunkowo. Lepszym podejściem mogłoby być zapewnienie, że `app_logger` jest zawsze dostępny po inicjalizacji (np. przez DI lub jako singleton, jeśli pasuje to do architektury).
      - `main_win.preferences = app.config` - bezpośrednie przypisanie słownika konfiguracji. Warto rozważyć, czy `MainWindow` nie powinno otrzymywać tylko tych części konfiguracji, których potrzebuje, lub korzystać z dedykowanego serwisu konfiguracyjnego.

3.  **Refaktoryzacja:**

    - **Podział bloku `if __name__ == "__main__":`:**
      - Wydzielenie logiki inicjalizacji UI (tworzenie `MainWindow`, ustawianie ikony, pokazywanie okna) do metody np. `Application.setup_ui()`.
      - Wydzielenie logiki splash screena do metody np. `Application.show_splash_screen(main_window_instance)`.
      - Wydzielenie logiki monitorowania wydajności do dedykowanej klasy lub modułu, który jest tylko inicjalizowany i uruchamiany z `main_app.py`.
    - **Klasa `Application`:**
      - Rozważenie przeniesienia większej ilości logiki inicjalizacyjnej z `if __name__ == "__main__":` do metod klasy `Application`, aby uczynić ją bardziej odpowiedzialną za cały cykl życia aplikacji.
      - Uspójnienie zarządzania `AppLogger`. Obecnie jest tworzony w `ApplicationStartup` i przekazywany przez sygnał. Można rozważyć jego wcześniejszą inicjalizację i bezpośrednie przekazanie do `ApplicationStartup`.
    - **Obsługa błędów:**
      - Upewnić się, że wszystkie potencjalne wyjątki podczas inicjalizacji są odpowiednio przechwytywane i logowane przez `handle_error_gracefully` lub dedykowane bloki try-except, a użytkownik otrzymuje stosowny komunikat w przypadku krytycznych błędów uniemożliwiających start.

4.  **Nadmiarowy kod / Nieużywane elementy:**

    - Zweryfikować użycie klasy `ConfigLoader`. Jeśli nie jest używana, można ją usunąć lub oznaczyć jako przestarzałą, jeśli planowane jest jej użycie w przyszłości.

5.  **Hardkodowane teksty:**

    - Komunikaty logów (np. "Configuration loaded and validated successfully") są w języku angielskim. Jeśli aplikacja ma być w pełni spolszczona, te teksty również powinny podlegać tłumaczeniu, chociaż logi często pozostają w języku angielskim dla ułatwienia pracy deweloperom.
    - Nazwy zadań w `startup_tasks` dla splash screena (np. "Loading configuration") są hardkodowane. Jeśli mają być widoczne dla użytkownika i aplikacja wspiera wiele języków, powinny być tłumaczone.

6.  **Zależności:**
    - Plik ma wiele zależności, co jest naturalne dla głównego pliku aplikacji. Ważne jest, aby te zależności były dobrze zarządzane (np. przez wstrzykiwanie zależności, jeśli stosowane w projekcie) i aby cykle zależności nie występowały.
    - Zależność od konkretnych ścieżek (`resources/img/icon.png`, `resources/img/splash.jpg`) – warto rozważyć użycie `ResourceManager` do abstrakcji dostępu do zasobów, co ułatwi zarządzanie ścieżkami i potencjalne zmiany w strukturze katalogów.

### 🧪 Plan testów

- **Test funkcjonalności podstawowej:**
  1.  Uruchomienie aplikacji: Sprawdzenie, czy aplikacja uruchamia się bez błędów.
  2.  Wyświetlanie splash screena: Jeśli `show_splash` jest `True`, sprawdzić, czy splash screen jest wyświetlany poprawnie z postępem (nawet symulowanym).
  3.  Wyświetlanie głównego okna: Sprawdzenie, czy główne okno aplikacji (`MainWindow`) pojawia się po splash screenie (lub od razu, jeśli splash jest wyłączony).
  4.  Ładowanie konfiguracji: Sprawdzenie, czy konfiguracja domyślna i z pliku `config.json` jest poprawnie ładowana i stosowana (np. `log_level`).
  5.  Logowanie: Sprawdzenie, czy logi są zapisywane zgodnie z konfiguracją (poziom, plik/konsola).
  6.  Zamknięcie aplikacji: Sprawdzenie, czy aplikacja zamyka się poprawnie i czy wykonywana jest metoda `app.cleanup()`.
- **Test integracji:**
  1.  Integracja z `ApplicationStartup`: Sprawdzenie, czy sygnały `config_loaded`, `startup_failed`, `startup_completed` są poprawnie emitowane i obsługiwane.
  2.  Integracja z `MainWindow`: Sprawdzenie, czy `MainWindow` otrzymuje konfigurację i instancję loggera.
  3.  Integracja z `PerformanceMonitor`: Sprawdzenie, czy monitor wydajności zbiera dane i czy timer do okresowego sprawdzania pamięci działa.
  4.  Integracja z `ResourceManager` (pośrednio przez `ApplicationStartup`): Sprawdzenie, czy style CSS są ładowane i stosowane.
- **Test obsługi błędów:**
  1.  Brak pliku `config.json`: Sprawdzenie, czy aplikacja obsługuje tę sytuację (np. używa domyślnej konfiguracji, loguje błąd, wyświetla komunikat).
  2.  Niepoprawny format `config.json` (np. błąd JSON): Sprawdzenie reakcji aplikacji.
  3.  Brak plików zasobów (ikona, splash): Sprawdzenie, czy aplikacja obsługuje brakujące zasoby (np. używa domyślnych, loguje błąd).

### 📊 Status tracking

- [ ] Kod zaimplementowany (wstępna analiza - bez zmian w kodzie na tym etapie)
- [ ] Testy podstawowe przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Testy integracji przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Dokumentacja zaktualizowana (komentarze w kodzie, jeśli dotyczy)
- [ ] Gotowe do wdrożenia (po implementacji poprawek i testach)

---

_Analiza pliku `main_app.py` zakończona._

---

## ETAP 2: SZCZEGÓŁOWA ANALIZA I KOREKCJE - `architecture/config_management.py`

### 📋 Identyfikacja

- **Plik główny:** `architecture/config_management.py`
- **Priorytet:** 🔴 WYSOKI PRIORYTET
- **Zależności:** Potencjalnie `config.json`, `hardware.json`, `utils/logger.py`, `utils/validators.py` (na podstawie komentarzy i przeznaczenia).

### 🔍 Analiza problemów

1.  **Błędy krytyczne:**

    - Plik w obecnej formie zawiera głównie szkielet klasy `ConfigManager` z zakomentowaną lub pominiętą logiką (`pass`). Nie implementuje faktycznego ładowania, zapisywania ani zarządzania konfiguracją. W takim stanie jest niefunkcjonalny.

2.  **Optymalizacje:**

    - **Singleton Pattern:** Użycie wzorca Singleton (`__new__`, `_instance`) jest widoczne. Należy upewnić się, że jest to najlepsze podejście dla zarządzania konfiguracją w tej aplikacji. Singleton może utrudniać testowanie i wprowadzać globalny stan.
    - **Inicjalizacja:** Metoda `_initialize` jest miejscem na inicjalizację loggera, walidatora itp., ale są one zakomentowane. Należy je zaimplementować.
    - **Cache:** `self.config_cache = {}` jest zadeklarowany, ale logika jego użycia w `load_config` i `get_config_value` jest pominięta.

3.  **Refaktoryzacja:**

    - **Implementacja metod:** Wszystkie kluczowe metody (`load_config`, `save_config`, `get_config_value`, `set_config_value`, `get_language_setting`, `set_language_setting`) wymagają pełnej implementacji.
      - `load_config`: Powinno zawierać logikę otwierania pliku (np. `config.json`), parsowania JSON, walidacji (np. przy użyciu `ConfigValidator` z `utils.validators`), obsługi błędów (np. brak pliku, niepoprawny format) i zapisywania do `config_cache`.
      - `save_config`: Powinno zawierać logikę zapisu zawartości `config_cache` (lub określonej części konfiguracji) do pliku JSON, obsługę błędów zapisu.
      - `get_config_value`: Powinno pobierać wartość z `config_cache`, obsługiwać klucze zagnieżdżone (np. `"language.default"`) i zwracać wartość domyślną, jeśli klucz nie istnieje.
      - `set_config_value`: Powinno aktualizować wartość w `config_cache` i opcjonalnie wywoływać `save_config` (lub oznaczać konfigurację jako "brudną" do zapisu później).
    - **Integracja z innymi modułami:** Komentarze wskazują na potrzebę integracji z `ConfigLoader` (z `main_app.py`), `ConfigValidator`, `ConfigTransaction`, `ConfigBackup`, `config_cache.py`. Należy podjąć decyzję, czy funkcjonalność tych modułów ma być wchłonięta przez `ConfigManager`, czy `ConfigManager` ma z nich korzystać.
    - **Ścieżka do pliku konfiguracyjnego:** `self.config_path` jest zadeklarowane, ale nie jest jasne, jak jest ustawiane. Powinno być przekazywane do `load_config` i `save_config` lub ustawiane globalnie dla instancji `ConfigManager`.
    - **Obsługa błędów:** Należy zaimplementować robustną obsługę błędów (np. używając wyjątków z `utils.exceptions`) dla operacji plikowych, walidacji itp.

4.  **Nadmiarowy kod / Nieużywane elementy:**

    - Zakomentowany kod (`self.logger`, `self.validator`, `self.backup_manager`, przykładowe implementacje metod) powinien zostać albo zaimplementowany, albo usunięty, jeśli nie jest potrzebny.
    - Komentarze typu `# ...logika ładowania...` powinny zostać zastąpione rzeczywistym kodem.

5.  **Hardkodowane teksty:**

    - Domyślne wartości, takie jak `"en"` w `get_language_setting`, jeśli zostaną zaimplementowane, powinny być zarządzane w sposób spójny (np. jako stałe lub konfigurowalne).

6.  **Zależności:**
    - Należy jawnie zdefiniować importy dla `logging`, `ConfigValidator` oraz potencjalnie `json`, `os` i wyjątków z `utils.exceptions`.

### 🧪 Plan testów

Po zaimplementowaniu funkcjonalności:

- **Test funkcjonalności podstawowej:**
  1.  Inicjalizacja `ConfigManager`: Sprawdzenie, czy instancja jest tworzona poprawnie (singleton).
  2.  Ładowanie konfiguracji:
      - Test ładowania z istniejącego, poprawnego pliku `config.json`.
      - Test obsługi braku pliku konfiguracyjnego (np. tworzenie domyślnego, logowanie błędu).
      - Test obsługi niepoprawnego formatu JSON w pliku.
      - Test użycia cache (ładowanie drugi raz powinno być szybsze lub nie odczytywać pliku, jeśli `use_cache=True`).
  3.  Pobieranie wartości:
      - Test `get_config_value` dla istniejącego klucza.
      - Test `get_config_value` dla nieistniejącego klucza (powinien zwrócić `default`).
      - Test `get_config_value` dla kluczy zagnieżdżonych.
  4.  Ustawianie wartości:
      - Test `set_config_value` dla nowego klucza.
      - Test `set_config_value` dla istniejącego klucza.
  5.  Zapisywanie konfiguracji:
      - Test `save_config` i weryfikacja, czy plik został poprawnie zapisany z nowymi wartościami.
      - Test obsługi błędów zapisu (np. brak uprawnień).
  6.  Specyficzne metody (np. `get_language_setting`, `set_language_setting`): Testowanie ich logiki po implementacji.
- **Test integracji:**
  1.  Integracja z `ConfigValidator`: Sprawdzenie, czy walidacja jest wywoływana podczas `load_config`.
  2.  Integracja z `AppLogger`: Sprawdzenie, czy `ConfigManager` poprawnie loguje swoje operacje i błędy.
  3.  Sprawdzenie, czy inne części aplikacji (np. `main_app.py`, moduły UI) mogą poprawnie używać `ConfigManager` do odczytu i zapisu konfiguracji.
- **Test obsługi błędów:**
  1.  Testowanie reakcji na różne typy błędów (plikowe, walidacyjne, parsowania) i czy są one poprawnie obsługiwane i logowane.

### 📊 Status tracking

- [ ] Kod zaimplementowany (plik wymaga pełnej implementacji)
- [ ] Testy podstawowe przeprowadzone
- [ ] Testy integracji przeprowadzone
- [ ] Dokumentacja zaktualizowana
- [ ] Gotowe do wdrożenia

---

_Analiza pliku `architecture/config_management.py` zakończona._

---

## ETAP 2: SZCZEGÓŁOWA ANALIZA I KOREKCJE - `architecture/dependency_injection.py`

### 📋 Identyfikacja

- **Plik:** `architecture/dependency_injection.py`
- **Priorytet:** 🔴 WYSOKI PRIORYTET
- **Zależności:** `functools`, `inspect`, `typing` (standard library). Przeznaczony do użycia przez inne moduły aplikacji.

### 🔍 Analiza problemów

1.  **Błędy krytyczne:**

    - Brak bezpośrednich błędów krytycznych uniemożliwiających działanie podstawowej funkcjonalności. Moduł wydaje się być dobrze przemyślany.
    - Potencjalny problem: W dekoratorze `@register_service`, parametr `singleton=False` jest opisany jako nie w pełni zaimplementowany, ponieważ `ServiceContainer.resolve` zawsze cache'uje instancje. To może prowadzić do nieporozumień, jeśli użytkownik oczekuje prawdziwego zachowania "transient". Ostrzeżenie jest logowane, co jest dobrym środkiem tymczasowym.

2.  **Optymalizacje:**

    - **Obsługa zasięgu (scope):** Jak wspomniano w TODO i komentarzach, brakuje pełnej obsługi różnych zasięgów serwisów (singleton, transient, per-request). Obecnie wszystko działa jak singleton. Rozbudowa `ServiceContainer` o tę funkcjonalność byłaby znaczącym ulepszeniem.
    - **Automatyczne wstrzykiwanie do konstruktora rejestrowanej klasy:** W `@register_service`, domyślny `actual_provider = cls` tworzy instancję bez automatycznego rozwiązywania zależności jej konstruktora. Jeśli rejestrowana klasa sama ma zależności, które powinny być wstrzyknięte, wymagałoby to ręcznego definiowania `provider` lub rozbudowy mechanizmu.
    - **Wydajność `resolve`:** Dla bardzo dużej liczby serwisów lub częstych wywołań `resolve`, obecna implementacja z przeszukiwaniem słowników jest zazwyczaj wystarczająco szybka, ale w skrajnych przypadkach mogłaby być profilem pod kątem optymalizacji.
    - **Typowanie:** Typowanie jest używane, co jest bardzo dobre. Można by rozważyć użycie `TypeVar` dla bardziej precyzyjnego typowania w `resolve` i `register_service`, aby powiązać typ rejestrowanej klasy/providera z typem zwracanym przez `resolve`.
    - **Obsługa błędów w `inject`:** W dekoratorze `inject`, gdy serwis jest wstrzykiwany pozycyjnie (`@inject("service_a")`) i nie ma parametru o takiej nazwie, logowane jest ostrzeżenie. Warto rozważyć, czy nie powinno to być konfigurowalne (np. strict mode rzucający błąd).

3.  **Refaktoryzacja:**

    - **Implementacja TODO:** Kluczowe elementy z listy TODO powinny zostać zaadresowane:
      - Obsługa zależności cyklicznych: Obecnie może to prowadzić do `RecursionError`. Wymaga to mechanizmu wykrywania cykli lub odroczonego rozwiązywania zależności.
      - Pełna implementacja zasięgów (singleton/transient).
      - Bardziej rozbudowana obsługa błędów (np. konfigurowalne zachowanie przy braku serwisu).
      - Możliwość wstrzykiwania przez atrybuty klasy (property injection).
      - Auto-wiring na podstawie typów (choć to znacząco zwiększa złożoność).
    - **Logika `singleton=False` w `@register_service`:** Należy albo usunąć ten parametr, albo w pełni zaimplementować zachowanie "transient" w `ServiceContainer.resolve`. Obecne ostrzeżenie jest tylko półśrodkiem.
    - **Metoda `unregister_service`:** Obecnie cicho ignoruje próbę wyrejestrowania nieistniejącego serwisu. Można by dodać opcjonalny parametr `raise_if_not_found=False`, aby kontrolować to zachowanie.
    - **Przejrzystość `inject`:** Logika w dekoratorze `inject` dotycząca rozróżniania argumentów pozycyjnych, nazwanych i tych do wstrzyknięcia jest dość złożona. Warto upewnić się, że wszystkie przypadki brzegowe są dobrze obsłużone i przetestowane. Komentarze są pomocne, ale sama logika mogłaby być ewentualnie uproszczona, jeśli to możliwe bez utraty funkcjonalności.

4.  **Nadmiarowy kod / Nieużywane elementy:**

    - Brak ewidentnie nadmiarowego lub nieużywanego kodu. Komentarze TODO wskazują na planowane rozszerzenia, a nie na zbędne fragmenty.

5.  **Hardkodowane teksty:**

    - Komunikaty wyjątków (`ServiceNotFoundError`, `ServiceAlreadyRegisteredError`) są w języku angielskim. Jeśli aplikacja ma być w pełni spolszczona na każdym poziomie, można by rozważyć ich tłumaczenie, choć dla wyjątków wewnętrznych bibliotek często pozostawia się angielski.
    - Ostrzeżenie w `@register_service` (`Warning: Service '{name}' registered with singleton=False...`) jest hardkodowane.
    - Ostrzeżenie w `@inject` (`Warning: For service '{service_name}' (injected by position)...`) jest hardkodowane.

6.  **Zależności:**
    - Moduł jest dobrze izolowany, korzysta tylko ze standardowej biblioteki. Jego celem jest zarządzanie zależnościami innych modułów.

### 🧪 Plan testów

- **Testy jednostkowe `ServiceContainer`:**
  1.  Rejestracja i rozwiązywanie serwisu przez providera (`register_service`, `resolve`).
  2.  Rejestracja i rozwiązywanie instancji (`register_instance`, `resolve`).
  3.  Zachowanie singletona: wielokrotne `resolve` zwraca tę samą instancję.
  4.  Nadpisywanie serwisu (`overwrite=True`).
  5.  Obsługa błędów: `ServiceNotFoundError`, `ServiceAlreadyRegisteredError`.
  6.  Wyrejestrowywanie serwisu (`unregister_service`).
  7.  Czyszczenie kontenera (`clear`).
  8.  Poprawne działanie `get_instance` (zwraca ten sam obiekt).
- **Testy jednostkowe dekoratora `@register_service`:**
  1.  Rejestracja klasy jako serwisu.
  2.  Rejestracja z własnym providerem.
  3.  Rejestracja z `overwrite=True`.
  4.  Sprawdzenie (nawet jeśli tylko logowane) zachowania z `singleton=False`.
- **Testy jednostkowe dekoratora `@inject`:**
  1.  Wstrzykiwanie zależności do konstruktora (`__init__`).
  2.  Wstrzykiwanie zależności do zwykłej metody.
  3.  Wstrzykiwanie przez nazwy argumentów pasujące do nazw serwisów (`@inject("service_a")`).
  4.  Wstrzykiwanie przez mapowanie nazw serwisów na argumenty (`@inject(arg_name="service_a")`).
  5.  Poprawne przekazywanie dodatkowych argumentów (nie wstrzykiwanych).
  6.  Obsługa błędów: brak serwisu, błędna nazwa parametru w `service_map`.
  7.  Wstrzykiwanie do funkcji, która przyjmuje `*args` i `**kwargs`.
  8.  Przypadki, gdy argument jest już jawnie przekazany (nie powinien być nadpisywany przez wstrzyknięcie).
- **Testy integracyjne (przykładowe scenariusze użycia):**
  1.  Złożenie kilku serwisów, gdzie jeden zależy od drugiego.
  2.  Użycie kontenera w kontekście symulowanej aplikacji.

### 📊 Status tracking

- [ ] Kod zaimplementowany (wstępna analiza - bez zmian w kodzie na tym etapie)
- [ ] Testy podstawowe przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Testy integracji przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Dokumentacja zaktualizowana (komentarze w kodzie, jeśli dotyczy)
- [ ] Gotowe do wdrożenia (po implementacji poprawek i testach)

---

_Analiza pliku `architecture/dependency_injection.py` zakończona._

---

## ETAP 2: SZCZEGÓŁOWA ANALIZA I KOREKCJE - `architecture/mvvm.py`

### 📋 Identyfikacja

- **Plik główny:** `architecture/mvvm.py`
- **Priorytet:** 🔴 WYSOKI PRIORYTET
- **Zależności:** `logging`, `abc`, `typing`, `PyQt6.QtCore`
- **Opis problemu/potrzeby:** Implementacja podstawowych klas dla wzorca MVVM. Wymaga sprawdzenia kompletności, poprawności implementacji sygnałów i slotów, obsługi błędów oraz potencjalnych optymalizacji.

### 🔍 Analiza problemów

1.  **Błędy krytyczne:** Brak.

2.  **Optymalizacje:**

    - W `BaseModel.set_property`: Rozważyć, czy sygnał `data_changed` powinien być emitowany tylko wtedy, gdy nowa wartość faktycznie różni się od starej. Obecnie tak jest, co jest poprawne.
    - W `BaseViewModel.execute_command`: Logowanie błędów jest ogólne. Można rozważyć bardziej szczegółowe logowanie lub przekazywanie wyjątków wyżej w stosie wywołań, jeśli jest to potrzebne.
    - `MVVMFactory`: W metodach `create_model` i `create_view_model` zastosowano próbę rozwiązania zależności przez kontener, a w przypadku niepowodzenia - bezpośrednią instancjację. To dobre podejście fallback, ale warto upewnić się, że kontener DI jest prawidłowo skonfigurowany, aby uniknąć częstego fallbacku.

3.  **Refaktoryzacja:**

    - Klasa `BaseView` jest abstrakcyjna i definiuje metody `on_property_changed` oraz `on_command_executed` jako abstrakcyjne. To wymusza ich implementację w klasach pochodnych, co jest zgodne z założeniami wzorca.
    - Rozważyć dodanie typowania dla `command` w `BaseViewModel.register_command` (np. `Callable`).

4.  **Zduplikowany kod:** Brak widocznych fragmentów zduplikowanego kodu.

5.  **Teksty zakodowane na stałe:** Brak.

6.  **Zależności zewnętrzne:** `PyQt6` - kluczowa zależność, należy upewnić się, że jest zarządzana i wersjonowana.

7.  **Testowalność:** Klasy bazowe wydają się być dobrze przygotowane do testowania jednostkowego dzięki wyraźnemu podziałowi odpowiedzialności.

### 📜 Proponowane zmiany i poprawki:

1.  Dodać bardziej szczegółowe typowanie tam, gdzie to możliwe (np. `Callable` dla komend).
2.  Przeanalizować logikę `MVVMFactory` w kontekście używanego kontenera DI, aby zapewnić optymalne działanie.

### 🧪 Plan testów

- Testy jednostkowe dla `BaseModel`: sprawdzanie ustawiania/pobierania właściwości, emitowania sygnału `data_changed`.
- Testy jednostkowe dla `BaseViewModel`: sprawdzanie bindowania modelu, reakcji na zmiany w modelu, rejestracji i wykonywania komend, emitowania sygnałów `property_changed` i `command_executed`.
- Testy jednostkowe dla `MVVMFactory`: sprawdzanie tworzenia instancji modeli i viewmodeli, zarówno z użyciem kontenera DI, jak i bez.

### 📊 Status tracking

- [ ] Kod zaimplementowany (wstępna analiza - bez zmian w kodzie na tym etapie)
- [ ] Testy podstawowe przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Testy integracji przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Dokumentacja zaktualizowana (komentarze w kodzie, jeśli dotyczy)
- [ ] Gotowe do wdrożenia (po implementacji poprawek i testach)

---

_Analiza pliku `architecture/mvvm.py` zakończona._

---

## ETAP 2: SZCZEGÓŁOWA ANALIZA I KOREKCJE - `architecture/state_management.py`

### 📋 Identyfikacja

- **Plik główny:** `architecture/state_management.py`
- **Priorytet:** 🔴 WYSOKI PRIORYTET
- **Zależności:** `logging`, `copy`, `typing`, `PyQt6.QtCore`
- **Opis problemu/potrzeby:** Implementacja scentralizowanego zarządzania stanem aplikacji w stylu Flux/Redux. Kluczowe jest zapewnienie poprawności działania dyspozytora akcji, reduktorów, middleware oraz subskrybentów. Należy również ocenić wydajność operacji na stanie, zwłaszcza `deepcopy`.

### 🔍 Analiza problemów

1.  **Błędy krytyczne:** Brak widocznych na pierwszy rzut oka.

2.  **Optymalizacje:**

    - Użycie `deepcopy` w `ActionDispatcher.dispatch` oraz `ActionDispatcher.get_state` i w reduktorach może być kosztowne dla dużych stanów. Należy rozważyć, czy we wszystkich przypadkach jest to konieczne, czy może wystarczyłoby płytkie kopiowanie lub bardziej selektywne aktualizacje, jeśli struktura stanu na to pozwala. W przypadku wzorca Redux, `deepcopy` jest często używane do zapewnienia niemutowalności stanu, co jest dobrą praktyką, ale warto monitorować wydajność.
    - Historia akcji (`_action_history`) ma stały limit (`_max_history`). Dla bardzo aktywnych aplikacji, warto rozważyć, czy ten limit jest odpowiedni.
    - W `ActionDispatcher._apply_middleware`: pętla po middleware jest standardowa, ale warto upewnić się, że logika `next` (tutaj uproszczona do `lambda a: a`) jest wystarczająca dla planowanych zastosowań middleware. W typowych implementacjach Redux middleware, `next` odnosi się do następnego middleware w łańcuchu.

3.  **Refaktoryzacja:**

    - Rozważyć wprowadzenie stałych (enumów) dla typów akcji (`action.type`), aby uniknąć literówek i ułatwić zarządzanie akcjami.
    - Reduktory (`_ui_reducer`, `_hardware_reducer`, etc.) są zaimplementowane jako prywatne metody klasy `Store`. To jest akceptowalne, ale w większych aplikacjach często oddziela się reduktory do osobnych modułów/plików dla lepszej organizacji.
    - Funkcje pomocnicze na końcu pliku (`set_current_tab`, `set_language`, etc.) są wygodne, ale globalny dostęp do store (`get_store()`) może utrudniać testowanie i prowadzić do zbyt luźnych powiązań. Wstrzykiwanie zależności (np. instancji store) tam, gdzie jest potrzebna, jest często preferowane.

4.  **Zduplikowany kod:** Logika tworzenia nowego stanu przez `deepcopy(state)` i następnie modyfikowanie go jest powtarzana w każdym reduktorze. Można by rozważyć stworzenie funkcji pomocniczej lub dekoratora, który obsługiwałby kopiowanie stanu.

5.  **Teksty zakodowane na stałe:** Typy akcji (np. "SET_CURRENT_TAB") są stringami. Klucze w initial_state również.

6.  **Zależności zewnętrzne:** `PyQt6.QtCore` dla `QObject` i `pyqtSignal` - używane do integracji z systemem sygnałów Qt, co jest dobre dla aplikacji Qt.

7.  **Testowalność:**

    - `ActionDispatcher` i `Store` wydają się być testowalne. Możliwość resetowania globalnego store (`reset_store()`) jest pomocna w testach.
    - Poszczególne reduktory, jako czyste funkcje (lub prawie czyste, jeśli nie modyfikują bezpośrednio stanu wejściowego przed `deepcopy`), powinny być łatwe do testowania jednostkowego.

### 📜 Proponowane zmiany i poprawki:

1.  **Typy Akcji:** Zdefiniować typy akcji jako stałe (np. w dedykowanej klasie lub enumie), aby uniknąć błędów związanych z literówkami i poprawić czytelność.
2.  **Optymalizacja `deepcopy`:** Przeanalizować użycie `deepcopy`. Jeśli stan jest bardzo duży i często aktualizowany, rozważyć strategie optymalizacyjne, np. użycie bibliotek do zarządzania niemutowalnym stanem (immutable.js, Immuter w Pythonie) lub bardziej granularne aktualizacje stanu.
3.  **Struktura Reduktorów:** Dla większej skali, rozważyć wydzielenie reduktorów do osobnych plików/modułów i użycie funkcji `combine_reducers` (lub jej odpowiednika) do ich kompozycji.
4.  **Middleware `next`:** Upewnić się, że implementacja `_apply_middleware` i przekazywanie `next` jest zgodne z oczekiwaną funkcjonalnością middleware (np. możliwość asynchronicznych operacji).
5.  **Dostęp do Store:** Rozważyć strategię dostępu do store – globalny singleton jest prosty, ale wstrzykiwanie zależności może być lepsze dla większych projektów i testowalności.

### 🧪 Plan testów

- Testy jednostkowe dla `Action` i `ActionDispatcher`: dispatchowanie akcji, działanie middleware (blokowanie, modyfikacja), rejestracja i powiadamianie subskrybentów, historia akcji.
- Testy jednostkowe dla `Store`: inicjalizacja stanu, rejestracja reduktorów i middleware, dispatchowanie akcji przez store.
- Testy jednostkowe dla każdego reduktora: sprawdzanie poprawności transformacji stanu dla różnych akcji i payloadów.
- Testy integracyjne dla przepływu akcji: od dispatcha, przez middleware, reduktory, aż po aktualizację stanu i powiadomienie subskrybentów.

### 📊 Status tracking

- [ ] Kod zaimplementowany (wstępna analiza - bez zmian w kodzie na tym etapie)
- [ ] Testy podstawowe przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Testy integracji przeprowadzone (do wykonania po ewentualnych zmianach)
- [ ] Dokumentacja zaktualizowana (komentarze w kodzie, jeśli dotyczy)
- [ ] Gotowe do wdrożenia (po implementacji poprawek i testach)

---

_Analiza pliku `architecture/state_management.py` zakończona._

---

## Analiza pliku: `UI/main_window.py`

- **Priorytet:** 🔴 Wysoki
- **Zależności:** `json`, `logging`, `os`, `PyQt6.QtCore`, `PyQt6.QtWidgets`, komponenty UI (`ConsoleWidget`, `MenuBar`, `TabOneWidget`, etc.), dialogi (`HardwareProfilerDialog`, `PreferencesDialog`), managery (`ThreadManager`, `TranslationManager`), optymalizatory (`performance_optimizer`).
- **Opis problemu/potrzeby:** Główne okno aplikacji, serce interfejsu użytkownika. Wymaga szczegółowej analizy pod kątem logiki UI, obsługi zdarzeń, zarządzania stanem (preferencje), integracji z innymi modułami (logowanie, wątki, tłumaczenia) oraz wydajności.
- **Analiza szczegółowa:**
  - **Błędy krytyczne:**
    - W `__init__`: `self.logger` jest inicjalizowane, a następnie `self.app_logger` jest przypisywane. Może to prowadzić do niejasności, która instancja loggera powinna być używana. Należy ujednolicić użycie loggera. `app_logger` jest przekazywany, ale `self.logger` jest tworzony lokalnie, jeśli `app_logger` to `None`. Sugeruje to, że `self.logger` powinno być głównym loggerem klasy.
    - W `_init_ui`: Domyślne wartości dla `window_size` i `window_pos` są używane, jeśli nie ma ich w preferencjach. To jest w porządku, ale warto upewnić się, że format tych wartości jest spójny z tym, co jest zapisywane i odczytywane.
    - W `_init_console`: Rejestracja `ConsoleWidget` w `AppLogger` jest owinięta w `try-except`, co jest dobre. Jednakże, logowanie testowe (`self.app_logger.async_logger.log`) może być mylące, jeśli `app_logger` nie jest w pełni skonfigurowany lub jeśli `async_logger` nie jest gotowy.
    - W `show_preferences_dialog`: Aktualizacja języka i poziomu logowania odbywa się po zapisaniu preferencji. Jeśli zapis asynchroniczny się nie powiedzie, UI może odzwierciedlać zmiany, które nie zostały utrwalone.
    - W `update_translations`: Próba aktualizacji tłumaczeń w widgetach zakładek (`_tab_widgets["tab1"].update_translations()`) jest uzależniona od istnienia atrybutów `_lazy_tabX_widget`. To wydaje się być pozostałością po poprzedniej implementacji lazy loadingu i może nie działać poprawnie z obecną logiką `_tab_widgets` i `_on_tab_changed`.
    - W `closeEvent`: Zapis preferencji jest asynchroniczny. Jeśli aplikacja zamknie się zanim zapis się zakończy, preferencje mogą nie zostać zapisane. Należy rozważyć synchroniczny zapis w tym miejscu lub mechanizm oczekiwania na zakończenie operacji asynchronicznych.
    - W `_on_tab_changed`: Logika lazy loadingu wydaje się skomplikowana i może być podatna na błędy. Sprawdzanie `hasattr(current_widget, "findChild")` i `current_widget.findChild(QLabel)` jest mało odporne. Lepszym podejściem byłoby przechowywanie informacji o tym, czy zakładka jest placeholderem w inny sposób.
  - **Optymalizacje:**
    - `FileWorker` wykonuje operacje plikowe w osobnym wątku, co jest dobre dla responsywności UI.
    - Użycie `@performance_monitor.measure_execution_time` jest dobrym pomysłem do monitorowania wydajności.
    - Lazy loading zakładek (`_on_tab_changed`) jest próbą optymalizacji czasu startu, ale jego implementacja wymaga uproszczenia i uodpornienia.
  - **Refaktoryzacja:**
    - **Ujednolicenie Loggera:** Zdecydować, czy używać `self.logger` czy `self.app_logger` i trzymać się jednej konwencji. Prawdopodobnie `self.logger` powinno być instancją przekazanego `app_logger` lub domyślnego loggera.
    - **Zarządzanie Preferencjami:** Logika wczytywania i zapisywania preferencji jest rozproszona. `_preferences` jest modyfikowane w kilku miejscach. Rozważyć stworzenie dedykowanej klasy lub serwisu do zarządzania preferencjami, który obsługiwałby wczytywanie, zapisywanie (również asynchroniczne z odpowiednią obsługą) i dostarczanie wartości.
    - **Lazy Loading Zakładek:** Uprościć mechanizm lazy loadingu. Zamiast placeholderów z QLabel, można inicjalizować zakładki z pustym widgetem lub specjalnym widgetem "ładowania", a następnie zastępować go właściwą treścią przy pierwszym przełączeniu. Stan załadowania można przechowywać w słowniku.
    - **Metoda `update_translations`:** Uprościć logikę aktualizacji tłumaczeń dla zakładek, upewniając się, że odwołuje się do poprawnie załadowanych widgetów.
    - **Obsługa `closeEvent`:** Zapewnić, że krytyczne operacje (jak zapis preferencji) są zakończone przed zamknięciem aplikacji.
    - **Klasa `FileWorker`:** Może być bardziej generyczna lub zastąpiona przez bardziej rozbudowany system zadań w tle, jeśli operacji plikowych będzie więcej.
  - **Zduplikowany kod:**
    - Logika pobierania `window_size` i `window_pos` z preferencji z wartościami domyślnymi powtarza się w `_init_ui` i `_apply_window_settings`.
  - **Teksty zakodowane na stałe:** Klucze preferencji (np. "remember_window_size"), klucze tłumaczeń (np. "app.title"), nazwy zakładek w `_tab_widgets` ("tab1", "tab2").
  - **Zależności zewnętrzne:** `PyQt6` - główna biblioteka UI.
  - **Testowalność:** Główne okno jest złożonym komponentem. Testowanie jednostkowe poszczególnych metod może być trudne bez mockowania wielu zależności. Testy integracyjne UI będą kluczowe.
- **Proponowane zmiany i poprawki:**
  1.  **Logger:** Ujednolicić użycie loggera (np. `self.logger = app_logger or logging.getLogger("MainWindowApp")`).
  2.  **Zarządzanie Preferencjami:** Stworzyć klasę `PreferencesManager` do obsługi wczytywania, zapisywania i dostępu do preferencji. Powinna ona obsługiwać operacje asynchroniczne i zapewniać spójność danych.
  3.  **Lazy Loading:** Przeprojektować lazy loading zakładek. Np. `QTabWidget.widget(index)` może początkowo zwracać `None` lub placeholder, a `_on_tab_changed` tworzyłoby i ustawiało właściwy widget przy pierwszym dostępie.
  4.  **`update_translations`:** Poprawić logikę, aby iterowała po istniejących widgetach w `self.tabs` i wywoływała ich metody `update_translations` (jeśli istnieją).
  5.  **`closeEvent`:** Zapewnić synchroniczny zapis preferencji lub mechanizm oczekiwania na zakończenie zapisu asynchronicznego przed zamknięciem.
  6.  **Stałe:** Przenieść klucze preferencji i typy akcji (jeśli dotyczy) do stałych/enumów.
  7.  **`FileWorker`:** Rozważyć, czy jego funkcjonalność nie powinna być częścią `PreferencesManager` lub ogólniejszego `BackgroundTaskManager`.
  8.  **Wyjątki w `__init__`:** Upewnić się, że logowanie błędów w `__init__` jest skuteczne i nie zależy od niepełnie zainicjalizowanych komponentów.
- **Plan testów:**
  - Testy jednostkowe dla `FileWorker` (jeśli pozostanie jako osobna klasa).
  - Testy jednostkowe dla (nowego) `PreferencesManager`.
  - Testy interakcji dla `MainWindow`: otwieranie dialogów, zmiana zakładek (z uwzględnieniem lazy loadingu), reakcja na zmiany preferencji, proces zamykania.
  - Testy wizualne i manualne dla poprawności wyświetlania UI, tłumaczeń, działania zakładek i menu.

---

## Analiza pliku: `utils/improved_thread_manager.py`

- **Priorytet:** 🔴 Wysoki
- **Zależności:** `logging`, `queue`, `threading`, `time`, `weakref`, `typing`, `PyQt6.QtCore`
- **Opis problemu/potrzeby:** Ulepszony menedżer wątków, łączący funkcjonalność poprzednich implementacji. Kluczowe jest zapewnienie stabilności, wydajności, poprawnej obsługi zadań (w tym anulowania i timeoutów) oraz zarządzania zasobami (wątki, kolejka logów).
- **Analiza szczegółowa:**
  - **Błędy krytyczne:**
    - W `ThreadManager.submit_task`: Logika wyodrębniania `timeout` z `*args` (`if args and isinstance(args[0], int) and len(args) > 1:`) jest podatna na błędy. Jeśli pierwszym argumentem przekazanym do `func` ma być liczba całkowita, zostanie ona błędnie zinterpretowana jako timeout. Lepszym podejściem byłoby przekazywanie `timeout` jako dedykowanego argumentu nazwanego do `submit_task` lub jako część `kwargs` dla `func`.
    - W `ThreadManager.cancel_task`: Jak zauważono w komentarzu, anulowanie zadań po `task_id` przy użyciu `WeakSet` jest problematyczne. `WeakSet` nie wspiera bezpośredniego dostępu po kluczu. Obecna implementacja zwraca `False` i loguje ostrzeżenie. Jeśli anulowanie zadań jest wymaganą funkcjonalnością, należy to przeprojektować (np. poprzez przechowywanie mapowania `task_id -> weakref(task)`).
    - W `ThreadManager.cleanup`: Anulowanie zadań (`task.cancel()`) jest wywoływane, ale jeśli zadanie już się zakończyło lub jest w trakcie wykonywania operacji nieprzerywalnej, `cancel()` może nie mieć efektu lub efekt może być opóźniony. `wait_for_completion(10)` może nie być wystarczające, jeśli zadania wykonują długotrwałe operacje blokujące.
    - W `ThreadManager.run_in_thread` (metoda kompatybilności): Tworzenie `CompatSignalsHelper` i `worker_compat_obj` wewnątrz tej metody dla każdego wywołania może być nieefektywne. Ponadto, dodawanie `worker_compat_obj` do `self.workers` bez mechanizmu usuwania po zakończeniu zadania doprowadzi do wycieku pamięci (lista `self.workers` będzie rosła w nieskończoność).
  - **Optymalizacje:**
    - `LogQueue`: Użycie `queue.Queue` i dedykowanego wątku do przetwarzania logów jest dobrym podejściem do asynchronicznego logowania.
    - `WeakSet` dla `active_tasks`: Pomaga w automatycznym zarządzaniu pamięcią dla zakończonych zadań, do których nie ma już silnych referencji.
    - `_log_rate_limiter`: Prosty mechanizm ograniczania logowania przy dużym obciążeniu jest przydatny.
    - `QThreadPool.globalInstance()`: Użycie globalnej puli wątków Qt jest zazwyczaj dobrym rozwiązaniem dla aplikacji Qt.
  - **Refaktoryzacja:**
    - **Przekazywanie `timeout`:** Zmienić sposób przekazywania `timeout` w `submit_task` na bardziej jawny (np. dedykowany argument `task_timeout` dla `submit_task`).
    - **Anulowanie zadań:** Jeśli anulowanie jest potrzebne, zaimplementować je poprawnie, np. przez utrzymywanie słownika `task_id -> weakref(task)` obok `WeakSet` lub przez dodanie atrybutu `task_id` do `ImprovedWorkerTask` i iterowanie po `WeakSet` w celu znalezienia zadania.
    - **Metoda `run_in_thread`:** Należy ją dokładnie przemyśleć. Jeśli celem jest pełna kompatybilność, obiekt zwracany przez `run_in_thread` powinien być zarządzany (np. usuwany z `self.workers` po zakończeniu). Jeśli kompatybilność nie jest absolutnie krytyczna, można rozważyć oznaczenie tej metody jako przestarzałej i stopniowe refaktoryzowanie kodu, który jej używa.
    - **Nazewnictwo:** `ImprovedWorkerTask` – nazwa sugeruje, że istnieje też "nieulepszona" wersja. Jeśli to jedyna używana klasa zadań, można ją uprościć do `WorkerTask`.
    - **Obsługa błędów w `LogQueue._process_logs`:** Obecnie loguje błąd i kontynuuje. Warto rozważyć, czy w niektórych przypadkach nie powinny być podejmowane inne akcje.
    - **Cykliczne referencje w `_periodic_cleanup`:** Komentarz wspomina o potencjalnych cyklicznych referencjach. Jeśli `WeakSet` nie radzi sobie z jakimiś przypadkami, logika w `_periodic_cleanup` powinna aktywnie próbować je identyfikować i przerywać.
  - **Zduplikowany kod:** Brak znaczących fragmentów zduplikowanego kodu.
  - **Teksty zakodowane na stałe:** Komunikaty logów i wyjątków.
  - **Zależności zewnętrzne:** `PyQt6.QtCore`.
  - **Testowalność:** Klasa jest dość złożona. Testowanie interakcji między `ThreadManager`, `ImprovedWorkerTask` i `LogQueue` będzie wymagało starannego przygotowania testów, w tym testów wielowątkowych, które mogą być trudne do stabilnego napisania.
- **Proponowane zmiany i poprawki:**
  1.  **`submit_task` `timeout`:** Zmienić sposób przekazywania `timeout` na dedykowany argument `task_timeout_sec` lub podobny.
  2.  **Anulowanie zadań:** Zdecydować o strategii anulowania. Jeśli potrzebne, zaimplementować mapowanie `task_id -> weakref(task)` lub iterację po `WeakSet` (z dodaniem `task_id` do `ImprovedWorkerTask`).
  3.  **`run_in_thread`:**
      - Opcja 1 (preferowana, jeśli możliwa): Oznaczyć jako `@deprecated` i refaktoryzować miejsca użycia, aby korzystały z `submit_task` i nowego API sygnałów.
      - Opcja 2 (jeśli kompatybilność jest krytyczna): Poprawić zarządzanie obiektami `worker_compat_obj` w `self.workers` (np. usuwanie po sygnale `finished` lub `error`). Rozważyć, czy tworzenie `CompatSignalsHelper` dla każdego wywołania jest optymalne.
  4.  **Logika `cleanup`:** Upewnić się, że anulowanie zadań i oczekiwanie na ich zakończenie jest jak najbardziej niezawodne. Rozważyć użycie `QThreadPool.cancel()` (jeśli dostępne i odpowiednie) lub bardziej zaawansowanych mechanizmów synchronizacji.
  5.  **Nazwa `ImprovedWorkerTask`:** Zmienić na `WorkerTask`, jeśli nie ma innej klasy zadań.
- **Plan testów:**
  - Testy jednostkowe dla `ImprovedWorkerTask`: wykonanie funkcji, obsługa sukcesu, błędu, anulowania (jeśli zaimplementowane poprawnie).
  - Testy jednostkowe dla `LogQueue`: dodawanie logów, przetwarzanie, zatrzymywanie.
  - Testy jednostkowe i integracyjne dla `ThreadManager`:
    - Dodawanie zadań (`submit_task`).
    - Pobieranie informacji o puli i metryk wydajności.
    - Działanie `_periodic_cleanup`.
    - Działanie `cleanup` (zatrzymywanie zadań, kolejki logów).
    - Testowanie `run_in_thread` (jeśli pozostaje) pod kątem kompatybilności i braku wycieków pamięci.
    - Testy wielowątkowe: dodawanie wielu zadań jednocześnie, sprawdzanie poprawnego wykonania i obsługi sygnałów.
    - Testowanie timeoutów zadań.

---

## Analiza pliku: `utils/logger.py`

- **Priorytet:** 🔴 Wysoki
- **Zależności:** `logging`, `os`, `time`, `datetime`, `queue`, `threading`.
- **Opis problemu/potrzeby:** Implementacja asynchronicznego loggera aplikacji. Kluczowe jest zapewnienie poprawnego działania logowania do różnych handlerów (konsola UI, plik, konsola systemowa), zarządzanie kolejką logów i wątkiem przetwarzającym oraz poprawna konfiguracja poziomów i formatterów.
- **Analiza szczegółowa:**
  - **Błędy krytyczne:**
    - W `AsyncLogger._process_logs`: Wywołanie `self.logger.handle(record)` loguje rekord do standardowych handlerów `AppLogger` (tych skonfigurowanych w `AppLogger.setup_logger`). Następnie, jeśli `_console_widget_handler` jest ustawiony, formatuje ten sam rekord i wysyła go do widgetu UI. To oznacza, że jeśli widget UI jest podłączony, logi mogą pojawić się podwójnie w konsoli systemowej, jeśli `system_console_handler` jest również aktywny (raz przez `self.logger.handle(record)` i potencjalnie drugi raz, jeśli `_console_widget_handler` to np. `print` lub inny handler piszący do stdout/stderr).
    - W `AsyncLogger._process_logs`: `self.logger.log(logging.DEBUG, ...)` jest używane do wewnętrznego logowania działania `AsyncLogger`. Jeśli główny `AppLogger` ma ustawiony poziom wyższy niż `DEBUG` (np. `INFO`), te wewnętrzne logi `AsyncLogger` nie będą widoczne, co może utrudniać diagnozowanie problemów z samym `AsyncLogger`.
    - W `AppLogger.setup_logger`: Opcja konfiguracyjna `log_ui_to_console` jest myląca. Komentarz sugeruje, że może oznaczać logowanie do konsoli systemowej, a nie UI. Należy to ujednoznacznić. Jeśli ma to być logowanie do konsoli systemowej, nazwa powinna to odzwierciedlać (np. `log_to_system_console`). Logowanie do konsoli UI jest zarządzane przez `set_console_widget_handler`.
    - W `AppLogger.cleanup`: Istnieją dwie metody `cleanup`. Jedna w `AppLogger` i jedna w `AsyncLogger`. `AppLogger.cleanup` wywołuje `self.async_logger.stop()`. Druga metoda `cleanup` na końcu pliku `AppLogger` jest prawdopodobnie duplikatem i powinna zostać usunięta.
  - **Optymalizacje:**
    - `AsyncLogger` używa dedykowanego wątku i kolejki, co jest dobre dla wydajności i unikania blokowania głównego wątku aplikacji.
    - Tworzenie nazwy pliku logu z datą (`app_{datetime.now().strftime('%Y%m%d')}.log`) jest dobrą praktyką.
  - **Refaktoryzacja:**
    - **Podwójne logowanie:** Należy rozwiązać problem potencjalnego podwójnego logowania. `AsyncLogger` powinien być odpowiedzialny tylko za przekazywanie logów do widgetu UI. Standardowe handlery (plik, konsola systemowa) powinny być zarządzane bezpośrednio przez instancję `logging.Logger` (`self.async_logger.logger`). Alternatywnie, `AsyncLogger` mógłby być jedynym, który zarządza wszystkimi handlerami, ale obecna struktura jest nieco niejasna.
    - **Logowanie wewnętrzne `AsyncLogger`:** Rozważyć użycie osobnej instancji loggera dla wewnętrznych logów `AsyncLogger` (np. `logging.getLogger("AsyncLoggerInternal")`) lub zapewnić, że poziom logowania `AppLogger` nie ukrywa tych ważnych komunikatów diagnostycznych.
    - **Nazwa opcji `log_ui_to_console`:** Zmienić na bardziej jednoznaczną, np. `log_to_system_console` lub `enable_system_console_handler`.
    - **Formatowanie w `AsyncLogger`:** `AsyncLogger` ma swój `_formatter`, który jest używany do formatowania wiadomości dla `_console_widget_handler`. `AppLogger.setup_logger` również ustawia `self.async_logger._formatter`. Należy upewnić się, że zarządzanie formatterami jest spójne i jasne, zwłaszcza jeśli różne handlery mają mieć różne formaty.
    - **Przekazywanie `LogRecord`:** `AsyncLogger.log` akceptuje `message` lub `LogRecord`. W `_process_logs` jest logika do tworzenia `LogRecord`, jeśli przekazano string. To jest w porządku, ale warto upewnić się, że wszystkie informacje kontekstowe (jak `exc_info`, `stack_info`) są poprawnie przekazywane, jeśli logger jest wywoływany z takimi danymi.
  - **Zduplikowany kod:** Metoda `cleanup` w `AppLogger` jest zduplikowana.
  - **Teksty zakodowane na stałe:** Komunikaty logów wewnętrznych.
  - **Zależności zewnętrzne:** Standardowe moduły Python.
  - **Testowalność:** Testowanie logiki wielowątkowej i interakcji z handlerami (zwłaszcza UI) może być skomplikowane. Wymaga mockowania i sprawdzania zawartości kolejki oraz wywołań handlerów.
- **Proponowane zmiany i poprawki:**
  1.  **Usunąć zduplikowaną metodę `cleanup`** w `AppLogger`.
  2.  **Rozwiązać problem podwójnego logowania:**
      - Sugerowane podejście: `AsyncLogger` powinien skupić się wyłącznie na przekazywaniu sformatowanych logów do `_console_widget_handler`. `AppLogger.setup_logger` powinien konfigurować standardowe handlery (plik, konsola systemowa) bezpośrednio na `self.async_logger.logger` (który jest instancją `logging.getLogger("AppLogger")`). Metoda `self.logger.handle(record)` w `AsyncLogger._process_logs` powinna zostać usunięta lub jej rola dokładnie przemyślana.
  3.  **Zmienić nazwę opcji `log_ui_to_console`** na np. `log_to_system_console` i dostosować logikę w `AppLogger.setup_logger`.
  4.  **Logowanie wewnętrzne `AsyncLogger`:** Użyć dedykowanego loggera lub zapewnić widoczność logów diagnostycznych `AsyncLogger`.
  5.  **Ujednoznacznić zarządzanie formatterami** między `AsyncLogger` a `AppLogger`.
  6.  Przejrzeć logikę tworzenia `LogRecord` w `AsyncLogger._process_logs`, aby upewnić się, że wszystkie istotne informacje są zachowywane.
- **Plan testów:**
  - Testy jednostkowe dla `AsyncLogger`:
    - Dodawanie logów do kolejki.
    - Przetwarzanie logów z kolejki (w tym obsługa sygnału stop).
    - Poprawne formatowanie i przekazywanie logów do mockowanego `_console_widget_handler`.
    - Obsługa błędów w `_console_widget_handler`.
  - Testy jednostkowe dla `AppLogger`:
    - Poprawna konfiguracja loggera (`setup_logger`) na podstawie różnych ustawień (poziom, włączone/wyłączone handlery plików i konsoli systemowej).
    - Tworzenie plików logów z poprawną nazwą i w odpowiednim katalogu.
    - Poprawne przekazywanie wywołań `debug`, `info`, etc. do `AsyncLogger`.
    - Działanie `cleanup`.
  - Testy integracyjne: Sprawdzenie, czy logi z różnych części aplikacji są poprawnie przechwytywane, formatowane i kierowane do odpowiednich miejsc (plik, konsola UI, konsola systemowa) zgodnie z konfiguracją.

---

## 📝 Status Dalszych Prac (Etap 2)

Zgodnie z planem w `code_map.md`, następnym krokiem jest szczegółowa analiza plików oznaczonych jako:

- 🟡 **Średni Priorytet**
- 🟢 **Niski Priorytet**

Wnioski z analizy tych plików będą sukcesywnie dodawane do niniejszego dokumentu (`corrections.md`).
Pierwszym plikiem o średnim priorytecie do analizy jest `config.json`.

---
