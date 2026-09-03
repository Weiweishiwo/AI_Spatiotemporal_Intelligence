@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================
echo  AI Spatiotemporal Intelligence - Launcher
echo ==============================================
echo.

REM --- 1. Check Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo IMPORTANT: check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM --- 2. Create virtual environment if missing ---
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment already exists.
)

REM --- 3. Install dependencies if not done yet ---
if not exist ".venv\.deps_installed" (
    echo [2/3] Installing dependencies, first time may take a few minutes...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        echo Tip: delete the .venv folder and run this script again.
        pause
        exit /b 1
    )
    echo installed > ".venv\.deps_installed"
) else (
    echo [2/3] Dependencies already installed.
)

REM --- 4. Run the app ---
echo [3/3] Starting backend API ...
echo     API contract: http://127.0.0.1:8000/docs
echo.
".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause
