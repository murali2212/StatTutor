@echo off
cd /d "%~dp0"
echo Installing what StatTutor needs (first time takes a minute)...
python -m pip install -r requirements.txt
echo.
echo Open http://localhost:8000 in your browser. Keep this window open while you use the app.
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8000"
python -m uvicorn backend.main:app --port 8000
pause
