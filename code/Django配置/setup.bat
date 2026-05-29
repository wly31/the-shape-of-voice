@echo off
REM One-time install: create venv and install dependencies.
cd /d "%~dp0"

set "PY=venv310\Scripts\python.exe"
set "PIP=venv310\Scripts\pip.exe"

echo ========================================
echo   SignTranslate - setup
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Install Python 3.10+ first.
    pause
    exit /b 1
)

if not exist "venv310\Scripts\python.exe" (
    echo Creating venv310 ...
    python -m venv venv310
    if errorlevel 1 (
        echo [ERROR] Failed to create venv310
        pause
        exit /b 1
    )
)

echo Installing packages from requirements.txt ...
"%PIP%" install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)

echo.
echo Setup OK. Now double-click run.bat to start the server.
pause
exit /b 0
