@echo off
cd /d "C:\Users\Administrator\Desktop\trae\基石\基石\backend"
start "Backend" py -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
timeout /t 3 /nobreak >nul
cd /d "C:\Users\Administrator\Desktop\trae\基石\基石\frontend"
start "Frontend" npm run dev
echo Services started!