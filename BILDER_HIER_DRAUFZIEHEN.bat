@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Noch nicht eingerichtet. Starte zuerst START_HIER.bat.
    pause
    exit /b 1
)

if "%~1"=="" (
    echo Ziehe ein oder mehrere Bilder mit der Maus auf diese BAT-Datei.
    pause
    exit /b 0
)

if not exist "FREIGESTELLT" mkdir "FREIGESTELLT"

:loop
if "%~1"=="" goto :done
.venv\Scripts\python.exe background_remover.py "%~1" "FREIGESTELLT"
shift
goto :loop

:done
echo Fertig. Ergebnisse liegen in FREIGESTELLT.
pause
