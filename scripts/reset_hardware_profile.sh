#!/bin/bash
# Skrypt do wyczyszczenia i odbudowania hardware.json
# Ten skrypt usuwa istniejący plik hardware.json, co zmusza aplikację
# do utworzenia nowego pliku przy następnym uruchomieniu

echo "Resetowanie profilu sprzętowego..."

# Sprawdź czy plik istnieje
if [ -f "hardware.json" ]; then
    echo "Tworzenie kopii zapasowej hardware.json jako hardware.json.bak"
    cp hardware.json hardware.json.bak
    
    echo "Usuwanie hardware.json..."
    rm hardware.json
    
    echo "Profil sprzętowy został usunięty. Nowy profil zostanie utworzony przy następnym uruchomieniu aplikacji."
else
    echo "Plik hardware.json nie istnieje. Nie ma potrzeby go resetować."
fi

echo "Gotowe!"
