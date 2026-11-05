@echo off
title Tennis Intelligence Platform - Launcher
echo =====================================================================
echo       [TIP] TENNIS INTELLIGENCE PLATFORM - LOCAL LAUNCHER
echo =====================================================================
echo.
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

echo [1/2] Launching FastAPI Backend on http://localhost:8000 ...
start "TIP Backend (FastAPI :8000)" cmd /k "cd /d %PROJECT_ROOT% && set PYTHONPATH=%PROJECT_ROOT%backend;%PROJECT_ROOT%;%PROJECT_ROOT%machine-learning\models && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend"

echo [2/2] Launching React Frontend on http://localhost:5173 ...
start "TIP Frontend (Vite :5173)" cmd /k "cd /d %PROJECT_ROOT%frontend && npm run dev"

echo.
echo =====================================================================
echo Both servers are launching in separate windows!
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000/docs
echo.
echo Demo Analyst Login: analyst@tennisintel.com / Analyst@123
echo Demo Admin Login:   admin@tennisintel.com / Admin@123
echo =====================================================================
pause
