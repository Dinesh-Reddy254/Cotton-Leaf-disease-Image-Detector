@echo off
title CottonGreen AI — Production Server
echo.
echo  ============================================
echo   🌿 CottonGreen AI — PRODUCTION Server
echo  ============================================
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo  [OK] Virtual environment activated
) else (
    echo  [!] No .venv found, using system Python
)

set FLASK_ENV=production
set TF_CPP_MIN_LOG_LEVEL=2
set TF_ENABLE_ONEDNN_OPTS=0

echo  [..] Starting production server (Waitress)...
echo  [..] Visit: http://localhost:5000
echo.

python app.py

pause
