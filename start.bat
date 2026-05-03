@echo off

if not exist "d:\myProject002\backend\venv\Scripts\activate.bat" (
    cd /d d:\myProject002\backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)

start "Backend :8001" cmd /k "cd /d d:\myProject002\backend && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --port 8001"

timeout /t 3 /nobreak >nul

start "Frontend :5174" cmd /k "cd /d d:\myProject002\frontend && npm run dev"

timeout /t 4 /nobreak >nul

start http://localhost:5174
