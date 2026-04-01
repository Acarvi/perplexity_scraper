@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    Perplexity Discover Scraper Runner
echo ==========================================

:: Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate

:: Install/Update dependencies
echo Installing/Updating dependencies...
python -m pip install --upgrade pip
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    pip install playwright playwright-stealth beautifulsoup4 flet
)

:: Ensure Playwright browsers are installed
echo Installing Playwright browsers (Chromium)...
playwright install chromium

:: Mode Selection
echo.
echo ------------------------------------------
echo CHOOSE LAUNCH MODE:
echo 1. GUI Dashboard (Material 3 Dark Mode)
echo 2. Terminal Only (Ultra Stable / No-GPU / Safe)
echo ------------------------------------------
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="2" (
    echo.
    echo Running in TERMINAL ONLY mode...
    python scraper.py --cli
) else (
    echo.
    echo Starting dashboard GUI...
    python dashboard.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo Scraper closed with an error (Code: %ERRORLEVEL%).
    pause
)

deactivate
