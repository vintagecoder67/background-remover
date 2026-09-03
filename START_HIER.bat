@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Vintage Background Remover

set "PYTHON=.venv\Scripts\python.exe"
set "MARKER=.venv\vintage-remover-ready-2.0.83"

echo ============================================================
echo   VINTAGE BACKGROUND REMOVER
echo ============================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo Installiere Python 3.11, 3.12 oder 3.13 von python.org.
    echo Beim Installer "Add Python to PATH" aktivieren.
    echo.
    pause
    exit /b 1
)

py -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)"
if errorlevel 1 (
    echo FEHLER: Benoetigt wird Python 3.11 bis 3.13.
    py --version
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    echo [1/4] Erstelle lokale Python-Umgebung ...
    py -m venv .venv
    if errorlevel 1 goto :error
)

if not exist "%MARKER%" (
    echo [2/4] Installiere Abhaengigkeiten ...
    "%PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :error
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto :error

    echo [3/4] Lade BiRefNet-Modell einmalig herunter ...
    "%PYTHON%" -c "from rembg import new_session; new_session('birefnet-general'); print('Modell bereit.')"
    if errorlevel 1 goto :error

    type nul > "%MARKER%"
) else (
    echo [1/4] Python-Umgebung: bereit
    echo [2/4] Abhaengigkeiten: bereit
    echo [3/4] Modell: bereits eingerichtet
)

if not exist "REIN_HIER" mkdir "REIN_HIER"
if not exist "FREIGESTELLT" mkdir "FREIGESTELLT"

echo [4/4] Starte Sofort-Verarbeitung ...
echo.
echo Lege Bilder jetzt in REIN_HIER.
echo Die PNG-Dateien erscheinen automatisch in FREIGESTELLT.
echo Dieses Fenster offen lassen.
echo.

"%PYTHON%" background_remover.py "REIN_HIER" "FREIGESTELLT" --watch --recursive
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo FEHLER: Einrichtung oder Verarbeitung ist fehlgeschlagen.
echo Starte bei Bedarf INSTALLIEREN_ODER_REPARIEREN.bat.
pause
exit /b 1
