@echo off
REM PingMonitor Pro v2.2 - Silent Launcher
REM Launches the application without showing console window

cd /d "%~dp0"

REM Try to find pythonw
where pythonw >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" pythonw PingMonitorPro.pyw
    exit
)

REM Try common Python locations
if exist "C:\Python312\pythonw.exe" (
    start "" "C:\Python312\pythonw.exe" PingMonitorPro.pyw
    exit
)

if exist "C:\Python311\pythonw.exe" (
    start "" "C:\Python311\pythonw.exe" PingMonitorPro.pyw
    exit
)

if exist "C:\Python310\pythonw.exe" (
    start "" "C:\Python310\pythonw.exe" PingMonitorPro.pyw
    exit
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" PingMonitorPro.pyw
    exit
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" PingMonitorPro.pyw
    exit
)

REM Python not found
msg "%username%" "Python not found! Please install Python 3.8 or later from https://www.python.org/downloads/"
exit /b 1
