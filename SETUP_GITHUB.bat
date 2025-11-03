@echo off
REM =============================================================================
REM PingMonitor Pro - GitHub Auto-Update Setup
REM Configura repository GitHub per aggiornamenti automatici
REM =============================================================================

cd /d "%~dp0"

echo.
echo ========================================================================
echo PingMonitor Pro - GitHub Auto-Update Setup
echo ========================================================================
echo.

REM Check if venv exists
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
    echo [OK] Launching setup wizard...
    echo.
    venv\Scripts\python.exe setup_github.py
) else (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please install dependencies first:
    echo   1. python -m venv venv
    echo   2. venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo Setup completato!
echo.
pause
