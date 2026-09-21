@echo off
cd /d %~dp0
call .venv\Scripts\activate
echo Starting Tracker Backend API...
start "Tracker API" .venv\Scripts\python.exe server.py
echo Starting Tracker Frontend UI...
cd frontend
start "Tracker UI" npm run dev -- --port 3000
timeout /t 3 /nobreak >nul
start http://127.0.0.1:3000
