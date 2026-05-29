@echo off
REM Use ASCII-only batch file (no UTF-8 Chinese) to avoid CMD parse errors on Windows.
cd /d "%~dp0"

set "PY="
if exist "venv310\Scripts\python.exe" set "PY=venv310\Scripts\python.exe"
if not defined PY if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

if not defined PY (
    echo [ERROR] Virtual environment not found.
    echo Run setup.bat first, then run this file again.
    pause
    exit /b 1
)

echo ========================================
echo   SignTranslate local server
echo ========================================
echo.
echo Port: 8001
echo Stop: press Ctrl+C in this window
echo.
echo Open in browser:
echo   http://127.0.0.1:8001/xh/stream/
echo   http://127.0.0.1:8001/xh/isolated/
echo.
echo Using: %PY%
echo.

"%PY%" manage.py runserver 127.0.0.1:8001
set "EXITCODE=%ERRORLEVEL%"

echo.
if not "%EXITCODE%"=="0" echo [ERROR] Server exited with code %EXITCODE%
echo Server stopped.
pause
exit /b %EXITCODE%
