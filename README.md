# Perplexity Discover Scraper 🚀🛡️

An automated scraper for the Perplexity Discover feed with advanced bot detection bypass and a professional dark-mode dashboard.

## Features
- **High-Performance CLI (HighPerf)**: Replaces GUI for maximum stability and speed.
- **Comet Optimization (Magic Command)**: Uses native `cmd /c start` for seamless tab management in the existing Comet session.
- **Concurrent Scraping**: `asyncio.Semaphore(5)` handles 5 articles simultaneously, drastically reducing execution time.
- **Entity Extraction**: Automatically identifies `skills`, `companies`, and `technical keywords` in news content.
- **Structured Output**: Multi-format persistence with cumulative text (`.txt` append mode) and structured `.json`.
- **Advanced UI**: `rich`-powered progress bars with `[X/Y]` tracking and professional color-coded logging.

## Project Structure
- `scraper.py`: CLI entry point with concurrency and `--set-path` support.
- `core/`:
    - `cli.py`: Terminal interface and progress tracking.
    - `browser.py`: Comet management via Magic Commands.
    - `parser.py`: Article and feed parsing logic.
- `utils/text_processor.py`: Regex-hardened date parsing and entity extraction.
- `tests/run_all_tests.py`: Global regression suite.

## How to Run
1. Configure Comet path: `python scraper.py --set-path "C:\Path\To\Comet.exe"` (Optional, defaults to standard path).
2. Execute: `perplexity_scraper.bat`.
3. Select your time range and monitor progress in real-time.

## Note on Security
Sensitive files like `user_data/`, `config.json`, and `last_run.json` are excluded from this repository by design to protect your private browser sessions and local file paths.
