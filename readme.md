# CFAB UI Manager

## Identyfikacja sprzętowa (UUID)

Aplikacja używa stabilnych identyfikatorów UUID do identyfikacji sprzętu. Identyfikatory te są generowane na podstawie unikalnych cech fizycznych komputera.

### Generowanie UUID

Do generowania stabilnych UUID należy używać funkcji `get_stable_uuid()` z modułu `utils.system_info`:

```python
from utils.system_info import get_stable_uuid

# Generowanie stabilnego UUID
uuid_value = get_stable_uuid()
```

Funkcja ta używa mechanizmu cache, dzięki czemu kolejne wywołania są szybsze i zawsze zwracają tą samą wartość UUID w ramach jednego uruchomienia aplikacji.

### Czyszczenie cache UUID

W przypadku konieczności wygenerowania UUID ponownie (np. w testach), można użyć funkcji `clear_uuid_cache()`:

```python
from utils.system_info import clear_uuid_cache, get_stable_uuid

# Wyczyszczenie cache UUID
clear_uuid_cache()

# Ponowne wygenerowanie UUID (będzie trwało dłużej)
uuid_value = get_stable_uuid()
```

### Dodatkowe informacje

Moduł `utils.system_info` zawiera również inne przydatne funkcje do pracy z informacjami o systemie.

---

https://github.com/coltongriffith/fluenticons
