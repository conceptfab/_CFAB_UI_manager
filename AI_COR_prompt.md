Przeanalizuj wszystkie pliki kodu w projekcie pod kątem błędów, poprawek, optymalizacji, usunięcia nadmiarowego kodu i duplikujących się funkcjonalności.

## Wymagania wstępne:

Na początku przygotuj schemat drzewa projektu w formacie tekstowym/ASCII z zaznaczeniem, które pliki w tej rewizji będą wymagały poprawek.

## Format wyniku:

Wzorzec formatowania znajduje się w pliku `_template_corrections.md` - użyj go jako szablon dla pliku `corrections.md`.

## Wymagania dotyczące poprawek:

- Wszystkie opisy poprawek w języku polskim
- Każda poprawka musi zawierać precyzyjne informacje o fragmentach kodu wymagających zmiany
- Każda poprawka musi prezentować finalne rozwiązanie z sformatowanym kodem
- Poprawki mają być podzielone na etapy
- **Jeden etap = jeden główny plik + wszystkie jego zależności**

## Struktura każdego etapu:

1. **Identyfikacja pliku:** Który plik jest głównym obiektem poprawek
2. **Opis zmian:** Co zostanie poprawione i dlaczego
3. **Kod finalny:** Kompletny, sformatowany kod po zmianach
4. **Checklista zależności:** Lista wszystkich plików wymagających aktualizacji
5. **Plan testów:** Jakie testy przeprowadzić dla potwierdzenia poprawności
6. **Status tracking:** Miejsce na aktualizację statusów po wykonaniu testów

## Uwagi dodatkowe:

- Poprawki muszą uwzględniać istniejącą strukturę projektu
- Jeśli zakres poprawek wymaga zmian w innych plikach - wyraźnie to zaznacz
- Po wykonaniu testów checklista ma być aktualizowana o odpowiednie statusy

## Plik wynikowy:

Zapisz cały plan w pliku `corrections.md` w głównym folderze projektu. Jeśli plik już istnieje, nadpisz jego zawartość.
