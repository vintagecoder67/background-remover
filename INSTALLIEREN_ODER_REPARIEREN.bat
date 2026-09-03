@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Vintage Background Remover - Reparatur Python 3.14

set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 (
    py -3.14 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,14) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3.14"
)

if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,14) else 1)" >nul 2>nul
        if not errorlevel 1 set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    echo FEHLER: Python 3.14.x wurde nicht gefunden.
    echo Installiere Python 3.14.x von python.org und starte diese Datei erneut.
    pause
    exit /b 1
)

echo Verwende:
%PY_CMD% --version

echo Entferne alte virtuelle Umgebung ...
if exist ".venv" rmdir /s /q ".venv"

%PY_CMD% -m venv .venv
if errorlevel 1 goto :error

.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error
.venv\Scripts\python.exe -c "import sys, onnxruntime, rembg; assert sys.version_info[:2] == (3,14); from rembg import new_session; print('Python:', sys.version.split()[0]); print('ONNX Runtime:', onnxruntime.__version__); new_session('birefnet-general'); print('BiRefNet bereit.')"
if errorlevel 1 goto :error

type nul > ".venv\vintage-remover-ready-2.0.83-py314"
if not exist "REIN_HIER" mkdir "REIN_HIER"
if not exist "FREIGESTELLT" mkdir "FREIGESTELLT"

echo.
echo Installation/Reparatur fuer Python 3.14 abgeschlossen.
echo Starte jetzt START_HIER.bat.
pause
exit /b 0

:error
echo.
echo Installation fehlgeschlagen.
echo Pruefe, ob Python 3.14.x korrekt installiert ist und Internetzugriff besteht.
pause
exit /b 1
