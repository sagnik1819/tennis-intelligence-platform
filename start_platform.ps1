# Tennis Intelligence Platform - PowerShell Launcher
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "      [TIP] TENNIS INTELLIGENCE PLATFORM - LOCAL LAUNCHER            " -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan

# 1. Start Backend in separate window
Write-Host "`n[1/2] Launching FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Yellow
$BackendCmd = "`$env:PYTHONPATH = '$ProjectRoot\backend;$ProjectRoot;$ProjectRoot\machine-learning\models'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; $BackendCmd"

# 2. Start Frontend in separate window
Write-Host "[2/2] Launching React Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\frontend'; npm run dev"

Write-Host "`n=====================================================================" -ForegroundColor Green
Write-Host "Both servers started in independent PowerShell windows!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Green
