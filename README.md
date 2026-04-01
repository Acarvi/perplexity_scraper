# Perplexity Discover Scraper 🚀🛡️

An automated scraper for the Perplexity Discover feed with advanced bot detection bypass and a professional dark-mode dashboard.

## Features
- **High-Performance CLI**: Extremely lightweight terminal interface with professional logs via `rich`.
- **Advanced Time Filtering**:
    - `Since Last Run`: Uses `data/last_run.json` to scrape only new content.
    - `Last 24 Hours`: Fixed daily window.
    - `Custom Window`: User-defined hours back.
- **Resource Optimization**: Strict blocking of CSS, images, and fonts to save CPU/GPU. Hardware acceleration disabled by default.
- **Progress Tracking**: Real-time progress bars for scrolling and article processing.

## Project Structure
- `scraper.py`: New CLI entry point.
- `core/`:
    - `cli.py`: Terminal UI, interactive menus, and logging.
    - `browser.py`: Optimized Comet management.
    - `parser.py`: Link extraction and article parsing.
- `utils/text_processor.py`: Advanced date parsing and noise cleaning.
- `data/`: Persistence for execution timestamps.
- `tests/`: Comprehensive unit tests for logic and time.

## How to Run
1. Ensure `rich` is installed: `pip install rich`.
2. Run `python scraper.py`.
3. Select your desired time range from the interactive menu.

## Note on Security
Sensitive files like `user_data/`, `config.json`, and `last_run.json` are excluded from this repository by design to protect your private browser sessions and local file paths.
