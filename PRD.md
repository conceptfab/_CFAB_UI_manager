# Dokument PRD (Product Requirements Document)

## 1. Cel projektu

Aplikacja "ConceptFab NeuroSorter" to zaawansowane narzędzie desktopowe (PyQt6), służące do zarządzania, profilowania i optymalizacji środowiska sprzętowego oraz konfiguracji użytkownika. Projekt kładzie nacisk na wysoką wydajność, modularność, łatwość utrzymania i pełną internacjonalizację (PL/EN).

## 2. Użytkownicy docelowi

- Zaawansowani użytkownicy komputerów
- Inżynierowie i naukowcy pracujący z danymi
- Administratorzy systemów
- Deweloperzy/testerzy oprogramowania

## 3. Główne funkcjonalności

- Profilowanie sprzętu (CPU, RAM, GPU, biblioteki, benchmarki)
- Zarządzanie konfiguracją aplikacji i preferencjami użytkownika
- Zaawansowany system logowania i konsola logów
- Wielojęzyczny interfejs użytkownika (PL/EN)
- Edytor stylów QSS (podgląd i modyfikacja stylów UI)
- Modułowe zakładki z możliwością rozbudowy
- System testów wydajnościowych i diagnostycznych

## 4. Wymagania funkcjonalne

- Aplikacja uruchamia się bez błędów na Windows 10/11
- Profilowanie sprzętu działa automatycznie i na żądanie
- Użytkownik może zmieniać preferencje (język, logowanie, rozmiar okna)
- Konsola logów obsługuje duże ilości danych i pozwala na eksport
- Wszystkie teksty UI obsługiwane przez system tłumaczeń
- Możliwość rozbudowy o kolejne zakładki i narzędzia

## 5. Wymagania niefunkcjonalne

- Wysoka wydajność (uruchomienie < 2s, niskie zużycie RAM)
- Modularna architektura (MVVM, DI, separacja logiki)
- Pokrycie testami jednostkowymi >80% dla kluczowych modułów
- Spójny styl kodu (PEP8, black, mypy, flake8)
- Dokumentacja kodu i użytkownika

## 6. Architektura i technologie

- Python 3.11+, PyQt6
- MVVM, Dependency Injection
- Pliki konfiguracyjne JSON (config.json, hardware.json)
- System tłumaczeń (pl.json, en.json)
- Benchmarki: pyperformance, cupy, numpy
- System logowania z obsługą wielu handlerów

## 7. Interfejs użytkownika (UI)

- Główne okno z zakładkami (Tab1, Tab2, Tab3, Konsola)
- Pasek menu: Plik, Edycja, Pomoc, Preferencje, Profil sprzętu
- Dialogi: Preferencje, O programie, Profiler sprzętu
- Konsola logów z możliwością czyszczenia i eksportu
- Edytor stylów QSS (podgląd na żywo)

## 8. Kryteria akceptacji

- Wszystkie funkcje działają zgodnie z opisem
- Brak krytycznych błędów po uruchomieniu
- Wydajność i zużycie pamięci zgodne z wymaganiami
- UI w pełni przetłumaczone (PL/EN)
- Testy automatyczne przechodzą bez błędów

## 9. Ryzyka i łagodzenie

- Złożoność zarządzania wątkami i profilowaniem sprzętu (testy, monitoring)
- Możliwe regresje wydajności (ciągłe testy wydajnościowe)
- Spójność tłumaczeń (automatyczne testy i walidacja plików JSON)

## 10. Załączniki

- Struktura projektu (code_map.md)
- Szczegółowy plan poprawek (\_template_corrections.md)
- Lista testów i pokrycia (tests/)
- Wymagania środowiskowe (requirements.txt)

---

Wersja: 1.0
Data: 2025-06-02
Autor: AI/Team
