@echo off
:: PingMonitor Pro v2.0 - Installer Builder
:: This script builds the Windows installer using Inno Setup

title PingMonitor Pro v2.0 - Building Installer
color 0A

echo.
echo ================================================================================
echo   PingMonitor Pro v2.0 - Installer Builder
echo   Building Professional Windows Installer
echo ================================================================================
echo.

:: Check if Inno Setup is installed
echo [1/4] Checking for Inno Setup...
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %INNO_SETUP% (
    echo.
    echo ERROR: Inno Setup 6 not found!
    echo.
    echo Please download and install Inno Setup 6 from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo After installation, run this script again.
    echo.
    pause
    exit /b 1
)

echo    [OK] Inno Setup found
echo.

:: Verify required files
echo [2/4] Verifying project files...

if not exist "..\PingMonitorPro.pyw" (
    echo    [ERROR] PingMonitorPro.pyw not found!
    pause
    exit /b 1
)

if not exist "..\icon.ico" (
    echo    [ERROR] icon.ico not found!
    pause
    exit /b 1
)

if not exist "..\src" (
    echo    [ERROR] src folder not found!
    pause
    exit /b 1
)

echo    [OK] All required files found
echo.

:: Create dist directory if it doesn't exist
echo [3/4] Preparing output directory...
if not exist "..\dist" mkdir "..\dist"
echo    [OK] Output directory ready
echo.

:: Build installer
echo [4/4] Building installer with Inno Setup...
echo.

%INNO_SETUP% "setup_script.iss"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo   SUCCESS! Installer built successfully!
    echo ================================================================================
    echo.
    echo   Installer location: ..\dist\PingMonitorPro_v2_Setup.exe
    echo.
    echo   You can now distribute this installer to install PingMonitor Pro on any
    echo   Windows computer with Python 3.8+ installed.
    echo.
    echo ================================================================================
    echo.

    :: Ask if user wants to open the dist folder
    choice /C YN /M "Do you want to open the dist folder"
    if %ERRORLEVEL% EQU 1 (
        explorer "..\dist"
    )
) else (
    echo.
    echo ================================================================================
    echo   ERROR: Installer build failed!
    echo ================================================================================
    echo.
    echo   Please check the error messages above and try again.
    echo.
    pause
    exit /b 1
)

echo.
pause
