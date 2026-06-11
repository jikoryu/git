@echo off
title Link Safe

echo.
echo   Link Safe
echo.

cd /d "%~dp0backend"

echo   Installing dependencies...
pip install -q -r requirements.txt

echo   Starting server at http://localhost:8000
echo   Press Ctrl+C to stop
echo.

start http://localhost:8000

python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
