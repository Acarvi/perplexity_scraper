@echo off
setlocal
echo ==========================================
echo    Perplexity Discover Scraper (HighPerf)
echo ==========================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate
set PYTHONPATH=%~dp0

echo Installing/Updating dependencies...
pip install -r requirements.txt
python -m playwright install chromium

echo Running tests...
python tests\run_all_tests.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Tests failed.
    pause
    exit /b %ERRORLEVEL%
)

echo Starting scraper...
python scraper.py %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Scraper crashed.
) else (
    echo.
    echo Scraper finished successfully.
)

deactivate
pause
