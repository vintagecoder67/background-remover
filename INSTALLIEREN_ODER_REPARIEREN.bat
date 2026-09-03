@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Vintage Background Remover - Reparatur

where py >nul 2>nul
if errorlevel 1 (
    echo FEHLER: Python Launcher fehlt.
    pause
    exit /b 1
)

if exist ".venv" rmdir /s /q ".venv"
py -m venv .venv
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error
.venv\Scripts\python.exe -c "from rembg import new_session; new_session('birefnet-general'); print('BiRefNet bereit.')"
if errorlevel 1 goto :error

type nul > ".venv\vintage-remover-ready-2.0.83"
if not exist "REIN_HIER" mkdir "REIN_HIER"
if not exist "FREIGESTELLT" mkdir "FREIGESTELLT"

echo Installation/Reparatur abgeschlossen.
echo Starte jetzt START_HIER.bat.
pause
exit /b 0

:error
echo Installation fehlgeschlagen.
pause
exit /b 1
