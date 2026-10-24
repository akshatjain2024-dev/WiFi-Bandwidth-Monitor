@echo off
title Wi-Fi Bandwidth Monitor
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)

if not exist .venv (
  echo Setting up virtual environment...
  %PY% -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

if not exist data\traffic_dataset.csv python dataset.py

set WIFI_MODE=simulation
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5050"
python app.py
pause
