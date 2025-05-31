@echo off
REM Skrypt do wyczyszczenia i odbudowania hardware.json
REM Ten skrypt usuwa istniejący plik hardware.json, co zmusza aplikację
REM do utworzenia nowego pliku przy następnym uruchomieniu

echo Resetowanie profilu sprzętowego...

REM Sprawdź czy plik istnieje
if exist hardware.json (
    echo Tworzenie kopii zapasowej hardware.json jako hardware.json.bak
    copy hardware.json hardware.json.bak
    
    echo Usuwanie hardware.json...
    del hardware.json
    
    echo Profil sprzętowy został usunięty. Nowy profil zostanie utworzony przy następnym uruchomieniu aplikacji.
) else (
    echo Plik hardware.json nie istnieje. Nie ma potrzeby go resetować.
)

echo Gotowe!
pause
