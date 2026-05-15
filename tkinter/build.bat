@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: PockiTrack — Build Script
:: Just double-click this file to build!
:: ─────────────────────────────────────────────────────────────────────────────

:: Auto-navigate to the folder where this .bat file is located
cd /d "%~dp0"

echo.
echo  PockiTrack Desktop App Builder
echo  ─────────────────────────────────────────────────────────────────────────────
echo  Working folder: %cd%
echo.

:: ── Check if .env exists ──────────────────────────────────────────────────────
if not exist ".env" (
    echo  [ERROR] .env file not found!
    echo  Please copy .env.example to .env and fill in your credentials.
    echo.
    pause
    exit /b 1
)
echo  [OK] .env found

:: ── Check if PyInstaller is installed ────────────────────────────────────────
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo  [INFO] PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo  [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)
echo  [OK] PyInstaller ready

:: ── Install dependencies ──────────────────────────────────────────────────────
echo  [INFO] Installing/verifying dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [WARN] Some packages may have failed. Continuing anyway...
)
echo  [OK] Dependencies ready

:: ── Clean old build ───────────────────────────────────────────────────────────
echo  [INFO] Cleaning old build files...
if exist "dist\PockiTrack" rmdir /s /q "dist\PockiTrack"
if exist "build\PockiTrack" rmdir /s /q "build\PockiTrack"
echo  [OK] Clean done

:: ── Run PyInstaller ───────────────────────────────────────────────────────────
echo.
echo  [INFO] Building PockiTrack... (this may take a few minutes)
echo.
pyinstaller PockiTrack.spec

if errorlevel 1 (
    echo.
    echo  [ERROR] Build FAILED. Check the errors above.
    pause
    exit /b 1
)

:: ── Done ─────────────────────────────────────────────────────────────────────
echo.
echo  ─────────────────────────────────────────────────────────────────────────────
echo  [SUCCESS] Build complete!
echo  Your app is at:  dist\PockiTrack\PockiTrack.exe
echo  ─────────────────────────────────────────────────────────────────────────────
echo.
pause