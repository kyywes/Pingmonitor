@echo off
REM =============================================================================
REM PingMonitor Pro v2.3 - Smart Launcher
REM Auto-patching enabled: Le modifiche al codice vengono applicate automaticamente
REM =============================================================================

cd /d "%~dp0"

echo.
echo ========================================================================
echo PingMonitor Pro v2.3 - Smart Launcher with Auto-Patching
echo ========================================================================
echo.
echo Controllo modifiche al codice sorgente...
echo.

REM Check if venv exists
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
    echo [OK] Launching with auto-patch detection...
    echo.
    venv\Scripts\python.exe smart_launcher.py
) else (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run setup first or use the compiled exe.
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
