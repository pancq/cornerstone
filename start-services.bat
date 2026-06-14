@echo off
echo Starting Backend...
cd /d "%~dp0backend"
start "Backend-Server" cmd /k "py -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting Frontend...
cd /d "%~dp0frontend"
start "Frontend-Dev" cmd /k "npm run dev"

echo Services started! Press any key to exit...
pause >nul
