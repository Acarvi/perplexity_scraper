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

echo Installing/Updating dependencies...
pip install -r requirements.txt

echo Running mandatory tests...
python tests/run_all_tests.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Tests failed. Aborting scrape.
    pause
    exit /b %ERRORLEVEL%
)

echo Starting scraper...
python scraper.py %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo Scraper closed with error %ERRORLEVEL%.
    pause
)

deactivate
