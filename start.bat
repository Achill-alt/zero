@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Contract Management System v1.2

set "ROOT=%~dp0"

echo.
echo ============================================================
echo   Contract Management System  v1.2
echo ============================================================
echo.

REM ---- Clean up stale processes on target ports ----
echo [INFO] Cleaning up stale processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM ---- Check Python (prefer python over python3 to avoid Windows Store stub) ----
set "PYTHON_CMD="
where python >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
) else (
    where python3 >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python3"
    )
)
if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python not found. Install Python 3.11+ first.
    echo         If Python is installed but not found, try:
    echo         1. Run: python --version  in a new terminal
    echo         2. Reinstall Python with "Add to PATH" checked
    echo         3. Disable "App Execution Aliases" for python3.exe in Windows Settings
    pause
    exit /b 1
)
REM Verify the python command actually works (some Windows Store stubs hang)
%PYTHON_CMD% --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Found %PYTHON_CMD% but it cannot run. It may be a Windows Store stub.
    echo         Disable "App Execution Aliases" for python/python3 in Windows Settings
    echo         Settings ^> Apps ^> Advanced app settings ^> App execution aliases
    pause
    exit /b 1
)
%PYTHON_CMD% --version 2>&1

REM ---- Check Node.js ----
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 18+ first.
    pause
    exit /b 1
)
node --version 2>&1

REM ---- Copy .env if not present ----
if not exist "%ROOT%backend\.env" (
    copy "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
    echo [INFO] Created backend\.env from .env.example
)
if not exist "%ROOT%frontend\.env" (
    copy "%ROOT%frontend\.env.example" "%ROOT%frontend\.env" >nul
    echo [INFO] Created frontend\.env from .env.example
)

REM ---- Install backend deps if missing ----
%PYTHON_CMD% -c "import fastapi, uvicorn, sqlalchemy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing backend dependencies...
    %PYTHON_CMD% -m pip install -r "%ROOT%backend\requirements.txt" -q
)

REM ---- Install frontend deps if missing ----
if not exist "%ROOT%frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    cd /d "%ROOT%frontend"
    call npm install --silent
    cd /d "%ROOT%"
)

REM ---- Init database if missing ----
if not exist "%ROOT%backend\app.db" (
    echo [INFO] Initializing database and seed data...
    cd /d "%ROOT%backend"
    %PYTHON_CMD% seed.py
    cd /d "%ROOT%"
)

REM ---- Create logs directory ----
if not exist "%ROOT%logs" mkdir "%ROOT%logs"

REM ---- Start backend ----
echo.
echo [INFO] Starting backend on port 8000...
cd /d "%ROOT%backend"
start /b "" cmd /c "%PYTHON_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > %ROOT%logs\backend.log 2>&1"
cd /d "%ROOT%"

REM ---- Start frontend ----
echo [INFO] Starting frontend on port 5173...
cd /d "%ROOT%frontend"
start /b "" cmd /c "npx vite --host 127.0.0.1 > %ROOT%logs\frontend.log 2>&1"
cd /d "%ROOT%"

REM ---- Wait for services ----
echo [INFO] Waiting for services to start...
ping -n 7 127.0.0.1 > nul

REM ---- Open browser ----
echo [INFO] Opening browser...
start http://localhost:5173

echo.
echo ============================================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo   Login:    admin / admin123
echo ============================================================
echo.
echo   [Q] Quit (stop all services and close)
echo.

:wait_q
choice /c q /n > nul 2>&1
if errorlevel 1 goto cleanup
goto wait_q

:cleanup
echo.
echo Stopping services...
taskkill /f /im python.exe > nul 2>&1
taskkill /f /im node.exe > nul 2>&1
echo All services stopped.
exit
