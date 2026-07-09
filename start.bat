@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Contract Management System v1.1

set "ROOT=%~dp0"

echo.
echo ============================================================
echo   Contract Management System  v1.1
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

REM ---- Check Python ----
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)
python --version 2>&1

REM ---- Check Node.js ----
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 18+ first.
    pause
    exit /b 1
)
node --version 2>&1

REM ---- Install backend deps if missing ----
python -c "import fastapi, uvicorn, sqlalchemy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing backend dependencies...
    pip install -r "%ROOT%backend\requirements.txt" -q
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
    echo [INFO] Initializing database...
    cd /d "%ROOT%backend"
    python seed.py
    cd /d "%ROOT%"
)

REM ---- Create logs directory ----
if not exist "%ROOT%logs" mkdir "%ROOT%logs"

REM ---- Start backend ----
echo.
echo [INFO] Starting backend on port 8000...
cd /d "%ROOT%backend"
start /b "" cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > %ROOT%logs\backend.log 2>&1"
cd /d "%ROOT%"

REM ---- Start frontend (node directly, not npm) ----
echo [INFO] Starting frontend on port 5173...
cd /d "%ROOT%frontend"
start /b "" cmd /c "node %ROOT%frontend\node_modules\vite\bin\vite.js --host 127.0.0.1 > %ROOT%logs\frontend.log 2>&1"
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
