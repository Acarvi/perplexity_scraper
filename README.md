# Perplexity Scraper CLI-HighPerf

High-performance terminal tool for scraping Perplexity Discover with concurrent tabs and intelligent extraction.

## Features
- **Total CLI Architecture**: Lightweight terminal interface powered by `rich`.
- **Concurrent Scraping**: Processes up to 5 tabs simultaneously using `asyncio.Semaphore(5)`.
- **Comet Navigation Protocol**: Uses native browser launch via `.lnk` to adhere to security standards.
- **Data Enrichment**: Detects skills, technical keywords, and company entities.
- **Persistence**: 
    - Cumulative text output (Append Mode).
    - Structured JSON database (`perplexity_data.json`).
- **Safety**: Mandatory pre-run regression tests.

## Usage
Run the single-entry point script:
```powershell
./perplexity_scraper.bat
```

## Project Map
- `scraper.py`: Core CLI orchestrator.
- `core/browser.py`: Magic Command browser management.
- `utils/text_processor.py`: Regex logic and entity detection.
- `tests/run_all_tests.py`: Mandatory test suite.
