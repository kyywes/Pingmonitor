@echo off
REM =============================================================================
REM PingMonitor Pro - GitHub Setup Automatico (con GitHub Desktop)
REM Configura tutto automaticamente usando credenziali GitHub Desktop
REM =============================================================================

cd /d "%~dp0"

echo.
echo ========================================================================
echo PingMonitor Pro - GitHub Setup Automatico
echo ========================================================================
echo.

REM Check if Git is installed
where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git non trovato!
    echo.
    echo Hai installato GitHub Desktop?
    echo Se si, riavvia questo script.
    echo Se no, scarica GitHub Desktop da: https://desktop.github.com/
    echo.
    pause
    exit /b 1
)

echo [OK] Git trovato
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment non trovato!
    echo.
    echo Esegui prima:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] Virtual environment trovato
echo.

REM Launch Python script for automatic setup
echo Avvio setup automatico...
echo.
venv\Scripts\python.exe setup_github_auto.py

if errorlevel 1 (
    echo.
    echo [ERROR] Setup fallito!
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo Setup GitHub completato con successo!
echo ========================================================================
echo.
pause
