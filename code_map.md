<!-- filepath: c:\_cloud\_CFAB_UI_manager\code_map.md -->

\_CFAB_UI_manager/
├── **clean_code.md
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Dokumentacja, weryfikacja aktualności.
│ ├── Funkcjonalność: Plik Markdown zawierający wytyczne dotyczące czystości kodu i standardów kodowania w projekcie.
│ ├── Stan obecny: Wymaga przeglądu pod kątem aktualności i kompletności zawartych informacji.
│ └── Zależności: Brak bezpośrednich zależności kodu; odnosi się do praktyk stosowanych w całym projekcie.
├── \_template_corrections.md
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Szablon, weryfikacja przydatności.
│ ├── Funkcjonalność: Plik Markdown służący jako szablon do dokumentowania poprawek lub analizy.
│ ├── Stan obecny: Należy zweryfikować, czy format szablonu jest nadal adekwatny i użyteczny.
│ └── Zależności: Brak zależności kodu.
├── AI_auto.md
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Notatki AI, weryfikacja treści.
│ ├── Funkcjonalność: Plik Markdown zawierający automatycznie generowane notatki lub sugestie przez narzędzia AI.
│ ├── Stan obecny: Wymaga weryfikacji merytorycznej i przydatności zawartych informacji.
│ └── Zależności: Brak zależności kodu.
├── config.json
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Konfiguracja globalna, weryfikacja kompletności i poprawności.
│ ├── Funkcjonalność: Przechowuje globalne ustawienia aplikacji w formacie JSON.
│ ├── Stan obecny: Wymaga sprawdzenia kompletności kluczy konfiguracyjnych, poprawności typów danych oraz wartości domyślnych.
│ └── Zależności: Odczytywany przez `architecture/config_management.py`, wpływa na działanie `main_app.py` i innych modułów.
├── hardware.json
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Konfiguracja sprzętu, weryfikacja struktury i danych.
│ ├── Funkcjonalność: Przechowuje konfigurację specyficzną dla sprzętu lub profili sprzętowych w formacie JSON.
│ ├── Stan obecny: Wymaga weryfikacji struktury danych, adekwatności przechowywanych informacji oraz mechanizmów aktualizacji.
│ └── Zależności: Odczytywany przez `architecture/config_management.py`, wykorzystywany przez `UI/hardware_profiler.py`.
├── main_app.py
│ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ ├── Opis problemu/potrzeby: Główny plik aplikacji, analiza krytycznych funkcji i potencjalnych błędów.
│ ├── Funkcjonalność: Główny punkt wejścia aplikacji. Inicjalizuje UI, system logowania, zarządzanie konfiguracją, wątkami oraz główną pętlę zdarzeń.
│ ├── Stan obecny: Kluczowy plik wymagający szczegółowej analizy pod kątem stabilności, obsługi błędów, wydajności i poprawnej integracji modułów. Potencjalne obszary do refaktoryzacji w celu zwiększenia modularności i testowalności.
│ └── Zależności: `UI/main_window.py`, `architecture/*`, `utils/*`, `config.json`, `hardware.json`.
├── readme.md
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Dokumentacja projektu, weryfikacja aktualności.
│ ├── Funkcjonalność: Główny plik dokumentacji projektu, zawiera opis, instrukcje instalacji, uruchomienia.
│ ├── Stan obecny: Wymaga przeglądu i aktualizacji, aby odzwierciedlał obecny stan projektu.
│ └── Zależności: Brak zależności kodu.
├── requirements.txt
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Zależności projektu, weryfikacja i aktualizacja.
│ ├── Funkcjonalność: Lista zewnętrznych bibliotek Python wymaganych przez projekt.
│ ├── Stan obecny: Należy zweryfikować wersje bibliotek pod kątem aktualności, bezpieczeństwa i kompatybilności. Rozważyć usunięcie nieużywanych zależności.
│ └── Zależności: Wpływa na środowisko uruchomieniowe całego projektu.
├── TODO.md
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Lista zadań, weryfikacja statusu.
│ ├── Funkcjonalność: Plik Markdown z listą zadań do wykonania w projekcie.
│ ├── Stan obecny: Wymaga przeglądu, aktualizacji statusów zadań i ewentualnego dodania nowych.
│ └── Zależności: Brak zależności kodu.
├── architecture/
│ ├── **init**.py
│ │ ├── Priorytet: 🟢 NISKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Inicjalizator pakietu, standardowa weryfikacja.
│ │ ├── Funkcjonalność: Inicjalizuje pakiet `architecture`, umożliwiając import jego modułów.
│ │ ├── Stan obecny: Standardowy plik, zazwyczaj nie wymaga zmian, chyba że potrzebne są specyficzne akcje inicjalizacyjne dla pakietu.
│ │ └── Zależności: Wykorzystywany przez mechanizm importu Pythona.
│ ├── config_management.py
│ │ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Zarządzanie konfiguracją, kluczowe dla działania, analiza pod kątem błędów i optymalizacji.
│ │ ├── Funkcjonalność: Odpowiada za wczytywanie, walidację i dostarczanie konfiguracji z plików `config.json` i `hardware.json`. Może zawierać logikę łączenia konfiguracji, obsługi wartości domyślnych.
│ │ ├── Stan obecny: Krytyczny komponent. Należy zbadać odporność na błędy (np. brakujące pliki, niepoprawny format), wydajność oraz łatwość rozszerzania konfiguracji.
│ │ └── Zależności: `config.json`, `hardware.json`, `utils/logger.py`. Używany przez `main_app.py` i inne moduły wymagające dostępu do konfiguracji.
│ ├── dependency_injection.py
│ │ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Wstrzykiwanie zależności, kluczowe dla architektury, analiza pod kątem poprawności implementacji.
│ │ ├── Funkcjonalność: Implementuje mechanizm wstrzykiwania zależności, zarządzając tworzeniem i dostarczaniem instancji obiektów (serwisów, managerów).
│ │ ├── Stan obecny: Kluczowy dla utrzymania luźnych powiązań i testowalności. Wymaga analizy poprawności implementacji wzorca DI, konfiguracji kontenera DI oraz sposobu rozwiązywania zależności.
│ │ └── Zależności: Wykorzystywany w całym projekcie do zarządzania obiektami, np. w `main_app.py` do inicjalizacji serwisów.
│ ├── mvvm.py
│ │ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Implementacja wzorca MVVM, kluczowe dla struktury UI, analiza spójności i efektywności.
│ │ ├── Funkcjonalność: Zawiera bazowe klasy lub narzędzia wspierające implementację wzorca Model-View-ViewModel dla komponentów UI.
│ │ ├── Stan obecny: Fundamentalny dla organizacji kodu UI. Należy ocenić spójność implementacji MVVM, mechanizmy bindowania danych, obsługę komend oraz separację odpowiedzialności.
│ │ └── Zależności: Wykorzystywany przez komponenty w `UI/` i `UI/components/`. Może zależeć od `architecture/state_management.py`.
│ └── state_management.py
│ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ ├── Opis problemu/potrzeby: Zarządzanie stanem, kluczowe dla logiki aplikacji, analiza pod kątem błędów i wydajności.
│ ├── Funkcjonalność: Implementuje globalne zarządzanie stanem aplikacji lub stanem poszczególnych modułów. Może wykorzystywać wzorce takie jak Redux, Flux lub własne rozwiązania.
│ ├── Stan obecny: Ważny dla spójności danych i przewidywalności zachowania aplikacji. Analiza powinna objąć sposób propagacji zmian stanu, obsługę akcji, mutacji oraz potencjalne problemy z wydajnością przy dużej liczbie aktualizacji.
│ └── Zależności: Wykorzystywany przez różne części aplikacji, które współdzielą stan, np. `UI/*`, `main_app.py`.
├── benchmarks/
│ └── performance_benchmark.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Skrypt benchmarkowy, analiza poprawności testów i wyników.
│ ├── Funkcjonalność: Skrypt do przeprowadzania testów wydajności kluczowych części aplikacji.
│ ├── Stan obecny: Wymaga weryfikacji, czy testy są adekwatne, czy poprawnie mierzą wydajność i czy wyniki są wiarygodne. Należy rozważyć automatyzację uruchamiania benchmarków.
│ └── Zależności: Może importować moduły aplikacji w celu ich testowania, np. `utils/performance_optimizer.py` lub konkretne algorytmy.
├── resources/
│ ├── styles.qss
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Arkusz stylów QSS, weryfikacja poprawności składni i stosowania stylów.
│ │ ├── Funkcjonalność: Definiuje wygląd i styl komponentów UI aplikacji przy użyciu składni Qt Style Sheets.
│ │ ├── Stan obecny: Wymaga sprawdzenia poprawności składni, optymalizacji selektorów oraz spójności stosowanych stylów. Możliwe konflikty stylów.
│ │ └── Zależności: Ładowany przez `utils/resource_manager.py` lub bezpośrednio w `UI/main_window.py`. Wpływa na wszystkie komponenty UI.
│ └── img/ (Katalog zasobów, pominięto pliki binarne w analizie kodu)
├── scripts/
│ ├── cleanup.py
│ │ ├── Priorytet: 🟢 NISKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Skrypt czyszczący, weryfikacja funkcjonalności i bezpieczeństwa.
│ │ ├── Funkcjonalność: Skrypt do usuwania plików tymczasowych, cache, logów lub innych artefaktów deweloperskich/buildów.
│ │ ├── Stan obecny: Wymaga weryfikacji, czy skrypt działa poprawnie, czy nie usuwa istotnych plików i czy jest bezpieczny w użyciu.
│ │ └── Zależności: Operuje na strukturze plików projektu.
│ ├── README.md
│ │ ├── Priorytet: 🟢 NISKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Dokumentacja skryptów, weryfikacja aktualności.
│ │ ├── Funkcjonalność: Opisuje dostępne skrypty w katalogu `scripts/`, ich przeznaczenie i sposób użycia.
│ │ ├── Stan obecny: Wymaga sprawdzenia, czy dokumentacja jest aktualna i kompletna.
│ │ └── Zależności: Brak zależności kodu.
│ └── setup_dev.py
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Skrypt konfiguracyjny DEV, weryfikacja poprawności działania.
│ ├── Funkcjonalność: Skrypt pomocniczy do konfiguracji środowiska deweloperskiego (np. instalacja dodatkowych narzędzi, konfiguracja hooków gita).
│ ├── Stan obecny: Wymaga weryfikacji poprawności działania i adekwatności do obecnych potrzeb deweloperskich.
│ └── Zależności: Może zależeć od `requirements.txt` lub narzędzi systemowych.
├── translations/
│ ├── en.json
│ │ ├── Priorytet: 🟢 NISKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Plik tłumaczeń (EN), weryfikacja kompletności i poprawności tłumaczeń.
│ │ ├── Funkcjonalność: Zawiera tłumaczenia tekstów interfejsu użytkownika na język angielski.
│ │ ├── Stan obecny: Wymaga sprawdzenia kompletności (czy wszystkie teksty są przetłumaczone) i poprawności tłumaczeń.
│ │ └── Zależności: Wykorzystywany przez `utils/translation_manager.py`.
│ ├── pl.json
│ │ ├── Priorytet: 🟢 NISKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Plik tłumaczeń (PL), weryfikacja kompletności i poprawności tłumaczeń.
│ │ ├── Funkcjonalność: Zawiera tłumaczenia tekstów interfejsu użytkownika na język polski.
│ │ ├── Stan obecny: Wymaga sprawdzenia kompletności i poprawności tłumaczeń.
│ │ └── Zależności: Wykorzystywany przez `utils/translation_manager.py`.
│ └── texts.md
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Źródło tekstów do tłumaczeń, weryfikacja spójności.
│ ├── Funkcjonalność: Może zawierać listę wszystkich tekstów używanych w aplikacji, które podlegają tłumaczeniu, jako centralne miejsce referencyjne.
│ ├── Stan obecny: Wymaga weryfikacji spójności z kluczami w plikach `.json` oraz aktualności.
│ └── Zależności: Powiązany z `en.json`, `pl.json` i `utils/translation_manager.py`.
├── UI/
│ ├── about_dialog.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Dialog "O programie", weryfikacja UI i logiki.
│ │ ├── Funkcjonalność: Implementuje okno dialogowe wyświetlające informacje o aplikacji (wersja, autorzy, licencja).
│ │ ├── Stan obecny: Weryfikacja poprawności wyświetlanych informacji, wyglądu UI oraz obsługi zdarzeń (np. zamknięcie okna).
│ │ └── Zależności: `UI/main_window.py` (wywołuje dialog), `utils/resource_manager.py` (dla ikon/obrazów).
│ ├── hardware_profiler.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Profiler sprzętu UI, weryfikacja UI i interakcji.
│ │ ├── Funkcjonalność: Komponent UI do wyświetlania informacji o sprzęcie i zarządzania profilami sprzętowymi.
│ │ ├── Stan obecny: Weryfikacja poprawności odczytu i wyświetlania danych z `hardware.json`, interakcji użytkownika (np. wybór profilu).
│ │ └── Zależności: `hardware.json`, `architecture/config_management.py`, `UI/main_window.py`.
│ ├── main_window.py
│ │ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Główne okno aplikacji, kluczowe UI, analiza logiki, wydajności i błędów.
│ │ ├── Funkcjonalność: Definiuje strukturę i logikę głównego okna aplikacji, w tym menu, paski narzędzi, obszar roboczy, integrację komponentów.
│ │ ├── Stan obecny: Jeden z najważniejszych plików. Wymaga analizy pod kątem organizacji kodu (np. separacja logiki od widoku, jeśli nie użyto MVVM w pełni), obsługi zdarzeń, wydajności renderowania, responsywności oraz integracji z `main_app.py` i innymi modułami.
│ │ └── Zależności: `main_app.py` (tworzy instancję), `UI/components/*`, `UI/style_editor/*`, `architecture/mvvm.py`, `architecture/state_management.py`, `utils/logger.py`, `utils/resource_manager.py`, `styles.qss`.
│ ├── preferences_dialog.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Dialog preferencji, weryfikacja UI i obsługi ustawień.
│ │ ├── Funkcjonalność: Implementuje okno dialogowe pozwalające użytkownikowi na konfigurację ustawień aplikacji.
│ │ ├── Stan obecny: Weryfikacja UI, poprawnego wczytywania i zapisywania ustawień (interakcja z `architecture/config_management.py`), walidacji wprowadzanych danych.
│ │ └── Zależności: `UI/main_window.py`, `architecture/config_management.py`, `config.json`.
│ ├── progress_controller.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Kontroler postępu UI, weryfikacja logiki i wyświetlania.
│ │ ├── Funkcjonalność: Zarządza wyświetlaniem informacji o postępie długotrwałych operacji (np. paski postępu, komunikaty).
│ │ ├── Stan obecny: Weryfikacja poprawności aktualizacji UI, obsługi anulowania operacji, integracji z operacjami w tle (np. przez `utils/improved_thread_manager.py`).
│ │ └── Zależności: `UI/main_window.py` (lub inne komponenty UI), `utils/improved_thread_manager.py`.
│ ├── splash_screen.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Ekran powitalny, weryfikacja UI i logiki startowej.
│ │ ├── Funkcjonalność: Wyświetla ekran powitalny podczas ładowania aplikacji.
│ │ ├── Stan obecny: Weryfikacja wyglądu, czasu wyświetlania, płynności przejścia do głównego okna. Może być połączony z `utils/enhanced_splash.py`.
│ │ └── Zależności: `main_app.py` (wyświetla go na starcie), `utils/resource_manager.py` (dla obrazu tła).
│ ├── components/
│ │ ├── base_tab_widget.py
│ │ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ │ ├── Opis problemu/potrzeby: Bazowy widget zakładek, analiza reużywalności i poprawności.
│ │ │ ├── Funkcjonalność: Abstrakcyjna klasa bazowa lub wspólny komponent dla różnych zakładek w interfejsie.
│ │ │ ├── Stan obecny: Analiza pod kątem reużywalności kodu, elastyczności konfiguracji i spójności interfejsu zakładek.
│ │ │ └── Zależności: Wykorzystywany przez `tab_one_widget.py`, `tab_two_widget.py`, `tab_three_widget.py`. Może zależeć od `architecture/mvvm.py`.
│ │ ├── console_widget.py
│ │ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ │ ├── Opis problemu/potrzeby: Widget konsoli, analiza funkcjonalności i wydajności.
│ │ │ ├── Funkcjonalność: Komponent UI wyświetlający logi aplikacji lub umożliwiający wprowadzanie komend.
│ │ │ ├── Stan obecny: Weryfikacja wydajności przy dużej ilości logów, filtrowania, kolorowania składni, obsługi komend.
│ │ │ └── Zależności: `UI/main_window.py`, `utils/logger.py` (jako źródło logów).
│ │ ├── menu_bar.py
│ │ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ │ ├── Opis problemu/potrzeby: Pasek menu, analiza konfiguracji i obsługi akcji.
│ │ │ ├── Funkcjonalność: Tworzy i zarządza głównym paskiem menu aplikacji.
│ │ │ ├── Stan obecny: Weryfikacja poprawnej konfiguracji menu (elementy, skróty klawiszowe), obsługi akcji, dynamicznego włączania/wyłączania opcji.
│ │ │ └── Zależności: `UI/main_window.py`.
│ │ ├── status_bar_manager.py
│ │ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ │ ├── Opis problemu/potrzeby: Menedżer paska stanu, analiza logiki i wyświetlania.
│ │ │ ├── Funkcjonalność: Zarządza informacjami wyświetlanymi na pasku stanu aplikacji.
│ │ │ ├── Stan obecny: Weryfikacja logiki aktualizacji komunikatów, wyświetlania ikon stanu, obsługi różnych sekcji paska stanu.
│ │ │ └── Zależności: `UI/main_window.py`.
│ │ ├── tab_one_widget.py
│ │ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ │ ├── Opis problemu/potrzeby: Widget zakładki 1, analiza specyficznej funkcjonalności.
│ │ │ ├── Funkcjonalność: Implementuje zawartość i logikę pierwszej zakładki w interfejsie użytkownika.
│ │ │ ├── Stan obecny: Analiza specyficznej funkcjonalności tej zakładki, jej UI, interakcji i zależności.
│ │ │ └── Zależności: `UI/main_window.py`, `UI/components/base_tab_widget.py`, potencjalnie `architecture/mvvm.py` i `architecture/state_management.py`.
│ │ ├── tab_three_widget.py
│ │ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ │ ├── Opis problemu/potrzeby: Widget zakładki 3, analiza specyficznej funkcjonalności.
│ │ │ ├── Funkcjonalność: Implementuje zawartość i logikę trzeciej zakładki w interfejsie użytkownika.
│ │ │ ├── Stan obecny: Analiza specyficznej funkcjonalności tej zakładki, jej UI, interakcji i zależności.
│ │ │ └── Zależności: `UI/main_window.py`, `UI/components/base_tab_widget.py`, potencjalnie `architecture/mvvm.py` i `architecture/state_management.py`.
│ │ └── tab_two_widget.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Widget zakładki 2, analiza specyficznej funkcjonalności.
│ │ ├── Funkcjonalność: Implementuje zawartość i logikę drugiej zakładki w interfejsie użytkownika.
│ │ ├── Stan obecny: Analiza specyficznej funkcjonalności tej zakładki, jej UI, interakcji i zależności.
│ │ └── Zależności: `UI/main_window.py`, `UI/components/base_tab_widget.py`, potencjalnie `architecture/mvvm.py` i `architecture/state_management.py`.
│ └── style_editor/
│ ├── style_editor_app.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Aplikacja edytora stylów, analiza funkcjonalności.
│ │ ├── Funkcjonalność: Może być osobną, małą aplikacją lub modułem do edycji stylów QSS na żywo.
│ │ ├── Stan obecny: Analiza funkcjonalności edytora, podglądu zmian, zapisu/odczytu stylów.
│ │ └── Zależności: `UI/style_editor/style_editor_window.py`, `resources/styles.qss`.
│ ├── style_editor_window.py
│ │ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ │ ├── Opis problemu/potrzeby: Okno edytora stylów, analiza UI i logiki.
│ │ ├── Funkcjonalność: Główne okno lub komponent UI dla edytora stylów.
│ │ ├── Stan obecny: Weryfikacja UI edytora, interakcji, integracji z `style_editor_app.py`.
│ │ └── Zależności: `UI/style_editor/style_editor_app.py`, `UI/style_editor/ui_showcase_widget.py`.
│ └── ui_showcase_widget.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Widget prezentacji UI, analiza komponentów.
│ ├── Funkcjonalność: Widget wyświetlający różne komponenty UI w celu demonstracji i testowania stylów QSS.
│ ├── Stan obecny: Weryfikacja kompletności prezentowanych komponentów, poprawności ich renderowania.
│ └── Zależności: Wykorzystywany przez `UI/style_editor/style_editor_window.py`.
└── utils/
├── **init\_\_.py
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Inicjalizator pakietu, standardowa weryfikacja.
│ ├── Funkcjonalność: Inicjalizuje pakiet `utils`, umożliwiając import jego modułów.
│ ├── Stan obecny: Standardowy plik, zazwyczaj nie wymaga zmian.
│ └── Zależności: Wykorzystywany przez mechanizm importu Pythona.
├── application_startup.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Logika startu aplikacji, analiza poprawności i kompletności.
│ ├── Funkcjonalność: Zawiera logikę wykonywaną podczas uruchamiania aplikacji, np. sprawdzanie warunków wstępnych, inicjalizacja zasobów.
│ ├── Stan obecny: Weryfikacja kompletności kroków startowych, obsługi błędów podczas startu.
│ └── Zależności: `main_app.py`.
├── config_cache.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Cache konfiguracji, analiza logiki i wydajności.
│ ├── Funkcjonalność: Implementuje mechanizm buforowania konfiguracji w celu przyspieszenia dostępu.
│ ├── Stan obecny: Analiza logiki cache'owania, strategii unieważniania cache, potencjalnych problemów z nieaktualnymi danymi.
│ └── Zależności: `architecture/config_management.py`.
├── enhanced_splash.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Ulepszony ekran powitalny, analiza funkcjonalności.
│ ├── Funkcjonalność: Może dostarczać bardziej zaawansowane funkcje dla ekranu powitalnego (np. animacje, komunikaty o postępie ładowania).
│ ├── Stan obecny: Weryfikacja dodatkowych funkcjonalności i ich integracji z `UI/splash_screen.py`.
│ └── Zależności: `UI/splash_screen.py`, `main_app.py`.
├── exceptions.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Definicje wyjątków, analiza kompletności i użycia.
│ ├── Funkcjonalność: Definiuje niestandardowe klasy wyjątków używane w aplikacji.
│ ├── Stan obecny: Weryfikacja, czy wyjątki są odpowiednio szczegółowe, czy pokrywają wszystkie specyficzne przypadki błędów w aplikacji i czy są poprawnie używane.
│ └── Zależności: Importowany przez różne moduły, które mogą rzucać lub przechwytywać te wyjątki.
├── improved_thread_manager.py
│ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ ├── Opis problemu/potrzeby: Menedżer wątków, kluczowy dla stabilności i wydajności, analiza pod kątem błędów i wycieków.
│ ├── Funkcjonalność: Zarządza tworzeniem, wykonywaniem i monitorowaniem wątków w aplikacji. Może implementować pulę wątków, mechanizmy komunikacji międzywątkowej.
│ ├── Stan obecny: Krytyczny dla responsywności i stabilności aplikacji. Analiza pod kątem poprawnej obsługi cyklu życia wątków, unikania zakleszczeń, wycieków zasobów oraz bezpieczeństwa operacji współbieżnych.
│ └── Zależności: Wykorzystywany przez moduły wykonujące operacje w tle, np. `UI/progress_controller.py`, `main_app.py`.
├── logger.py
│ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ ├── Opis problemu/potrzeby: Logger aplikacji, kluczowy dla diagnostyki, analiza konfiguracji i użycia.
│ ├── Funkcjonalność: Konfiguruje i dostarcza instancję loggera do zapisu zdarzeń i błędów aplikacji. Może obsługiwać różne poziomy logowania, formaty i miejsca docelowe (plik, konsola).
│ ├── Stan obecny: Niezbędny do monitorowania i debugowania. Analiza konfiguracji (poziomy, formaty, rotacja plików), spójności użycia w całym projekcie oraz kompletności logowanych informacji.
│ └── Zależności: Używany przez większość modułów .py w projekcie.
├── performance_optimizer.py
│ ├── Priorytet: 🔴 WYSOKI PRIORYTET
│ ├── Opis problemu/potrzeby: Optymalizator wydajności, analiza implementacji i efektów.
│ ├── Funkcjonalność: Może zawierać narzędzia, dekoratory lub techniki służące do profilowania i optymalizacji wydajności krytycznych fragmentów kodu.
│ ├── Stan obecny: Wymaga analizy zastosowanych technik optymalizacyjnych, ich wpływu na wydajność oraz potencjalnych skutków ubocznych (np. zwiększona złożoność kodu).
│ └── Zależności: Może być używany w różnych częściach aplikacji, np. w `main_app.py` lub przez `benchmarks/performance_benchmark.py`.
├── resource_manager.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Menedżer zasobów, analiza logiki ładowania i dostępu.
│ ├── Funkcjonalność: Zarządza dostępem do zasobów aplikacji (obrazy, ikony, pliki stylów, pliki tłumaczeń). Może implementować mechanizmy ładowania z systemu plików lub zasobów Qt.
│ ├── Stan obecny: Weryfikacja poprawności ścieżek do zasobów, obsługi błędów (brakujące zasoby), wydajności ładowania.
│ └── Zależności: `UI/*`, `resources/*`, `translations/*`.
├── secure_commands.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Bezpieczne wykonywanie komend, analiza bezpieczeństwa i poprawności.
│ ├── Funkcjonalność: Moduł do bezpiecznego wykonywania komend systemowych lub skryptów zewnętrznych.
│ ├── Stan obecny: Analiza pod kątem bezpieczeństwa (np. unikanie podatności na wstrzykiwanie komend), poprawnej obsługi wyników i błędów wykonania.
│ └── Zależności: Może być używany przez `scripts/*` lub inne moduły wymagające interakcji z systemem.
├── system_info.py
│ ├── Priorytet: 🟢 NISKI PRIORYTET
│ ├── Opis problemu/potrzeby: Informacje o systemie, weryfikacja zbieranych danych.
│ ├── Funkcjonalność: Gromadzi informacje o systemie operacyjnym, sprzęcie, wersji Pythona itp.
│ ├── Stan obecny: Weryfikacja poprawności i kompletności zbieranych informacji, potencjalne problemy z prywatnością.
│ └── Zależności: Może być używany przez `utils/logger.py` (dołączanie info do logów) lub `UI/about_dialog.py`.
├── translation_manager.py
│ ├── Priorytet: 🟡 ŚREDNI PRIORYTET
│ ├── Opis problemu/potrzeby: Menedżer tłumaczeń, analiza logiki ładowania i dostarczania tłumaczeń.
│ ├── Funkcjonalność: Odpowiada za ładowanie plików tłumaczeń (`.json`) i dostarczanie przetłumaczonych tekstów do interfejsu użytkownika.
│ ├── Stan obecny: Analiza mechanizmu przełączania języków, obsługi brakujących tłumaczeń (fallback), wydajności.
│ └── Zależności: `translations/*.json`, `texts.md`. Używany przez komponenty UI.
└── validators.py
├── Priorytet: 🟡 ŚREDNI PRIORYTET
├── Opis problemu/potrzeby: Walidatory danych, analiza kompletności i poprawności.
├── Funkcjonalność: Zawiera funkcje lub klasy do walidacji danych wejściowych (np. z formularzy UI, plików konfiguracyjnych).
├── Stan obecny: Weryfikacja kompletności reguł walidacyjnych, poprawności ich implementacji oraz obsługi błędów walidacji.
└── Zależności: Używany przez `UI/*` (np. `UI/preferences_dialog.py`), `architecture/config_management.py`.

---

## PLAN ETAPU 2

### Kolejność analizy plików (wg priorytetów):

1.  **🔴 WYSOKI PRIORYTET:**
    - `main_app.py`
    - `architecture/config_management.py`
    - `architecture/dependency_injection.py`
    - `architecture/mvvm.py`
    - `architecture/state_management.py`
    - `UI/main_window.py`
    - `utils/improved_thread_manager.py`
    - `utils/logger.py`
    - `utils/performance_optimizer.py`
2.  **🟡 ŚREDNI PRIORYTET:**
    - `config.json`
    - `hardware.json`
    - `requirements.txt`
    - `benchmarks/performance_benchmark.py`
    - `resources/styles.qss`
    - `UI/about_dialog.py`
    - `UI/hardware_profiler.py`
    - `UI/preferences_dialog.py`
    - `UI/progress_controller.py`
    - `UI/splash_screen.py`
    - `UI/components/base_tab_widget.py`
    - `UI/components/console_widget.py`
    - `UI/components/menu_bar.py`
    - `UI/components/status_bar_manager.py`
    - `UI/components/tab_one_widget.py`
    - `UI/components/tab_three_widget.py`
    - `UI/components/tab_two_widget.py`
    - `UI/style_editor/style_editor_app.py`
    - `UI/style_editor/style_editor_window.py`
    - `UI/style_editor/ui_showcase_widget.py`
    - `utils/application_startup.py`
    - `utils/config_cache.py`
    - `utils/enhanced_splash.py`
    - `utils/exceptions.py`
    - `utils/resource_manager.py`
    - `utils/secure_commands.py`
    - `utils/translation_manager.py`
    - `utils/validators.py`
3.  **🟢 NISKI PRIORYTET:**
    - `__clean_code.md`
    - `_template_corrections.md`
    - `AI_auto.md`
    - `readme.md`
    - `TODO.md`
    - `architecture/__init__.py`
    - `scripts/cleanup.py`
    - `scripts/README.md`
    - `scripts/setup_dev.py`
    - `translations/en.json`
    - `translations/pl.json`
    - `translations/texts.md`
    - `utils/__init__.py`
    - `utils/system_info.py`

### Grupowanie plików do analizy:

Analiza będzie prowadzona plik po pliku zgodnie z powyższą kolejnością. W przypadku plików o wysokim priorytecie, szczególnie `main_app.py` oraz komponentów architektury i głównego UI, analiza będzie uwzględniać ich bezpośrednie zależności w celu zapewnienia spójności.

- **Grupa 1 (Krytyczne - Rdzeń Aplikacji):** `main_app.py`, `architecture/config_management.py`, `architecture/dependency_injection.py`, `architecture/mvvm.py`, `architecture/state_management.py`, `UI/main_window.py`, `utils/logger.py`, `utils/improved_thread_manager.py`, `utils/performance_optimizer.py`. Analiza tych plików powinna być przeprowadzona jako pierwsza, z uwzględnieniem ich wzajemnych interakcji.
- **Grupa 2 (Konfiguracja i Główne Komponenty UI):** `config.json`, `hardware.json`, `requirements.txt`, pozostałe pliki z `UI/` (dialogi, ekrany), `UI/components/*`. Te pliki będą analizowane po ustabilizowaniu rdzenia aplikacji.
- **Grupa 3 (Narzędzia Pomocnicze i Skrypty):** Pozostałe pliki z `utils/*`, `benchmarks/*`, `scripts/*`, `resources/styles.qss`.
- **Grupa 4 (Dokumentacja i Tłumaczenia):** Pliki `.md` (`__clean_code.md`, `_template_corrections.md`, `AI_auto.md`, `readme.md`, `TODO.md`), pliki z `translations/*`. Te elementy będą analizowane na końcu, po zakończeniu prac nad kodem.

### Szacowany zakres zmian (typy poprawek):

- **Refaktoryzacja kodu:** Poprawa struktury klas i funkcji, zwiększenie czytelności, usunięcie duplikacji kodu (DRY), zastosowanie odpowiednich wzorców projektowych.
- **Optymalizacja wydajności:** Identyfikacja i eliminacja wąskich gardeł, optymalizacja algorytmów, zarządzania pamięcią i operacji I/O.
- **Poprawki błędów:** Naprawa zidentyfikowanych błędów logicznych, wykonawczych oraz obsługa przypadków brzegowych.
- **Ulepszenia architektury:** Wzmocnienie implementacji wzorców (np. MVVM, DI), poprawa separacji odpowiedzialności (SoC), zwiększenie modularności i testowalności.
- **Zarządzanie zależnościami:** Weryfikacja, aktualizacja i ewentualne usunięcie nieużywanych zależności w `requirements.txt`.
- **Poprawa obsługi błędów:** Implementacja bardziej szczegółowego i spójnego logowania, wprowadzenie hierarchii wyjątków (`exceptions.py`), zapewnienie odporności na błędy.
- **Standaryzacja konfiguracji:** Ujednolicenie dostępu do konfiguracji, walidacja, obsługa wartości domyślnych.
- **Poprawa UI/UX:** Drobne korekty w interfejsie użytkownika w celu zwiększenia intuicyjności i spójności. Weryfikacja responsywności.
- **Aktualizacja dokumentacji:** Uzupełnienie i poprawa istniejącej dokumentacji (readme, komentarze w kodzie).
- **Internacjonalizacja (i18n):** Weryfikacja kompletności tłumaczeń, poprawności działania mechanizmu przełączania języków, obsługa tekstów nieprzetłumaczonych.
- **Bezpieczeństwo:** Analiza potencjalnych luk bezpieczeństwa, szczególnie w modułach takich jak `utils/secure_commands.py`.
