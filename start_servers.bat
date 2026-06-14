@echo off
cd /d C:\Users\Administrator\Desktop\trae\基石\基石\frontend
start "Frontend" cmd.exe /k "npm.cmd run dev"
cd /d C:\Users\Administrator\Desktop\trae\基石\基石\backend
start "Backend" cmd.exe /k "py.cmd -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
