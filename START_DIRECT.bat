@echo off
REM =============================================================================
REM PingMonitor Pro v2.3 - Direct Launch (Without Launcher)
REM For development and testing - always uses source code
REM =============================================================================

cd /d "%~dp0"

echo.
echo ========================================================================
echo PingMonitor Pro v2.3 - Direct Launch (Development Mode)
echo ========================================================================
echo.

REM Check if venv exists
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
    echo [OK] Launching from source code...
    echo.
    venv\Scripts\python.exe src\main.py
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

REM Exit code handling
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with errors
    pause
)
