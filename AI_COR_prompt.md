# Prompt do analizy i korekcji projektu

Przeanalizuj WSZYSTKIE PLIKI zawierające kod w projekcie pod kątem błędów, poprawek, optymalizacji, usunięcia nadmiarowego kodu i duplikujących się funkcjonalności, hardkodowanych elementów tekstowych które powinny być przetłumaczone.

## Wymagania wstępne:

**KLUCZOWE:** Na początku przygotuj DOKŁADNĄ mapę projektu w formacie tekstowym/ASCII z zaznaczeniem, które pliki w tej rewizji będą wymagały poprawek. Mapa projektu musi być kompletna i precyzyjna - na jej podstawie będzie analizowany każdy pojedynczy plik w projekcie.

**BARDZO WAŻNE:** Dokument `corrections.md` MUSI być uzupełniany na bieżąco podczas całego procesu analizy! W razie przerwy czy awarii nie może zmarnować się już wykonana praca. Po każdym przeanalizowanym pliku natychmiast aktualizuj dokument wynikowy.

## Format wyniku:

Wzorzec formatowania znajduje się w pliku `_template_corrections.md` - użyj go jako szablon dla pliku `corrections.md`.

## Wymagania dotyczące poprawek:

- Wszystkie opisy poprawek w języku polskim
- Każda poprawka musi zawierać precyzyjne informacje o fragmentach kodu wymagających zmiany
- Każda poprawka musi prezentować finalne rozwiązanie z sformatowanym kodem
- Poprawki mają być podzielone na etapy
- **Jeden etap = jeden główny plik + wszystkie jego zależności**
- **Każdy plik z mapy projektu musi być przeanalizowany i udokumentowany**

## Struktura każdego etapu:

1. **Identyfikacja pliku:** Który plik jest głównym obiektem poprawek
2. **Opis zmian:** Co zostanie poprawione i dlaczego
3. **Kod finalny:** Kompletny, sformatowany kod po zmianach
4. **Checklista zależności:** Lista wszystkich plików wymagających aktualizacji
5. **Plan testów:** Jakie testy przeprowadzić dla potwierdzenia poprawności
6. **Status tracking:** Miejsce na aktualizację statusów po wykonaniu testów

## Proces wykonania:

1. **Krok 1:** Przygotuj kompletną mapę projektu
2. **Krok 2:** Rozpocznij analizę od pierwszego pliku z mapy
3. **Krok 3:** Po każdym przeanalizowanym pliku NATYCHMIAST aktualizuj `corrections.md`
4. **Krok 4:** Kontynuuj zgodnie z kolejnością w mapie projektu
5. **Krok 5:** Każdy etap zapisuj progressywnie - nie czekaj do końca

## Uwagi dodatkowe:

- Poprawki muszą uwzględniać istniejącą strukturę projektu
- Jeśli zakres poprawek wymaga zmian w innych plikach - wyraźnie to zaznacz
- Po wykonaniu testów checklista ma być aktualizowana o odpowiednie statusy
- **Mapa projektu jest fundamentem - każdy widoczny plik kodu musi być uwzględniony**
- **Ciągłe zapisywanie postępów jest priorytetem - nie można stracić pracy**

## Plik wynikowy:

Zapisz cały plan w pliku `corrections.md` w głównym folderze projektu. Plik musi być aktualizowany na bieżąco podczas całego procesu analizy. Jeśli plik już istnieje, rozwijaj jego zawartość progresywnie.