@echo off
title CottonGreen AI — Dev Server
cd /d "%~dp0"

echo ================================================
echo   CottonGreen AI v2.0  ^|  Development Server
echo ================================================

:: Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Copy model if needed
if not exist "model\final_model.keras" (
    if exist "best_model.keras" (
        echo [INFO] Copying best_model.keras to model\final_model.keras ...
        if not exist "model" mkdir model
        copy /Y "best_model.keras" "model\final_model.keras" >nul
        echo [OK]   Model ready.
    )
)

set FLASK_ENV=development
set FLASK_DEBUG=1

echo [*] Starting Flask dev server on http://localhost:5000
python app.py
pause
