# Moduł System Info - Dokumentacja

## Wprowadzenie

Moduł `utils.system_info` został wprowadzony jako część optymalizacji zarządzania identyfikatorami sprzętu w aplikacji.
Zapewnia on spójny i wydajny sposób generowania stabilnych identyfikatorów UUID, które są używane do identyfikacji
sprzętu użytkownika.

## Architektura

### Główne komponenty

1. **Funkcja `get_stable_uuid()`**

   - Zapewnia stabilny identyfikator UUID oparty na stałych parametrach sprzętowych
   - Wykorzystuje dekorator `@lru_cache` dla optymalizacji wydajności
   - Wspiera różne systemy operacyjne (Windows, Linux, macOS)

2. **Globalny cache UUID**

   - Przechowuje wygenerowany UUID w pamięci aplikacji
   - Zapewnia szybki dostęp w wielu częściach aplikacji

3. **Funkcja `clear_uuid_cache()`**

   - Umożliwia wyczyszczenie cache, co jest przydatne w testach

4. **Funkcja `get_system_info()`**
   - Dostarcza słownik z podstawowymi informacjami o systemie

## Schemat działania

```
┌────────────────────┐      ┌─────────────────────┐
│    main_app.py     │      │  hardware_profiler  │
└────────────────────┘      └─────────────────────┘
         │                             │
         └─────────────┬───────────────┘
                       ▼
              ┌─────────────────┐
              │  system_info.py │
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
```

## Optymalizacje

1. **Pamięć podręczna LRU**

   - Funkcja `get_stable_uuid()` używa dekoratora `@lru_cache` z Python'a, co pozwala na zapamiętanie wyniku
   - Kolejne wywołania funkcji zwracają zapisaną wartość bez ponownego wykonywania kosztownych operacji

2. **Globalny cache UUID**
   - Dodatkowo wprowadzono globalną zmienną `_UUID_CACHE`, która przechowuje UUID
   - Jest to dodatkowe zabezpieczenie, gdyby cache LRU został wyłączony

## Zalety rozwiązania

1. **Wydajność**

   - Znaczne przyspieszenie dostępu do UUID po pierwszym wygenerowaniu
   - Redukcja liczby operacji I/O i wywołań systemowych

2. **Spójność**

   - Gwarancja, że wszystkie komponenty aplikacji używają tego samego UUID
   - Eliminacja problemu z wielokrotnym generowaniem różnych UUID

3. **Utrzymywalność**
   - Centralna lokalizacja kodu generującego UUID
   - Łatwiejsze wprowadzanie zmian w przyszłości
