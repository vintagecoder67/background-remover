@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Vintage Background Remover

set "VENV_PY=.venv\Scripts\python.exe"
set "MARKER=.venv\vintage-remover-ready-2.0.83-py314"
set "PY_CMD="

echo ============================================================
echo   VINTAGE BACKGROUND REMOVER - Python 3.14
echo ============================================================
echo.

rem Bevorzuge den Windows Python Launcher mit Python 3.14.
where py >nul 2>nul
if not errorlevel 1 (
    py -3.14 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,14) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3.14"
)

rem Fallback: normales python, falls exakt Python 3.14 dahinterliegt.
if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,14) else 1)" >nul 2>nul
        if not errorlevel 1 set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    echo FEHLER: Python 3.14.x wurde nicht gefunden.
    echo.
    echo Installiere die aktuelle Python-3.14-Version von python.org.
    echo Beim Installer am besten "Install launcher for all users" und
    echo "Add python.exe to PATH" aktivieren.
    echo.
    echo Danach START_HIER.bat erneut starten.
    pause
    exit /b 1
)

echo Gefunden:
%PY_CMD% --version
echo.

if not exist "%VENV_PY%" (
    echo [1/4] Erstelle lokale Python-3.14-Umgebung ...
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

"%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,14) else 1)" >nul 2>nul
if errorlevel 1 (
    echo Alte virtuelle Umgebung mit anderer Python-Version gefunden.
    echo Sie wird neu mit Python 3.14 erstellt ...
    rmdir /s /q ".venv"
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

if not exist "%MARKER%" (
    echo [2/4] Installiere Python-3.14-Abhaengigkeiten ...
    "%VENV_PY%" -m pip install --upgrade pip setuptools wheel
    if errorlevel 1 goto :error
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto :error

    echo [3/4] Lade BiRefNet-Modell einmalig herunter ...
    "%VENV_PY%" -c "import onnxruntime, rembg; from rembg import new_session; print('Python/ONNX bereit:', onnxruntime.__version__); new_session('birefnet-general'); print('BiRefNet bereit.')"
    if errorlevel 1 goto :error

    type nul > "%MARKER%"
) else (
    echo [1/4] Python-3.14-Umgebung: bereit
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

"%VENV_PY%" background_remover.py "REIN_HIER" "FREIGESTELLT" --watch --recursive --canvas 1600 --margin 0.06 --background white --overwrite
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo FEHLER: Einrichtung oder Verarbeitung ist fehlgeschlagen.
echo Starte bei Bedarf INSTALLIEREN_ODER_REPARIEREN.bat.
pause
exit /b 1
