@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Noch nicht eingerichtet. Starte zuerst START_HIER.bat.
    pause
    exit /b 1
)

if not exist "REIN_HIER" mkdir "REIN_HIER"
if not exist "FREIGESTELLT" mkdir "FREIGESTELLT"
.venv\Scripts\python.exe background_remover.py "REIN_HIER" "FREIGESTELLT" --recursive
pause
