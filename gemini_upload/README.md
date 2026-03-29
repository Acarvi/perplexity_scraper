# Perplexity Discover Scraper 🚀🛡️

An automated scraper for the Perplexity Discover feed with advanced bot detection bypass and a professional dark-mode dashboard.

## Features
- **Advanced Bot Bypass**: Uses native Comet browser launch via CDP to evade Cloudflare Turnstile detection.
- **Premium GUI**: Dark-mode dashboard built with Flet for real-time monitoring.
- **CLI Mode**: "Ultra Stable" terminal-only mode for systems with sensitive graphics hardware.
- **Precision Filtering**: Pre-navigation date filtering to capture only recent news.
- **Safe Persistence**: Saves session cookies and verification tokens locally.

## Project Structure
- `scraper.py`: The core scraping engine.
- `dashboard.py`: Flet-based GUI for monitoring and control.
- `run_scraper.bat`: Entry point script (handles venv and updates).
- `requirements.txt`: Python dependencies.
- `.gitignore`: Ensures your private session data and local paths stay private.

## How to Run
1. Execute `run_scraper.bat`.
2. Choose a mode:
   - **Option 1**: GUI Dashboard.
   - **Option 2**: Terminal Only (Safest for hardware).
3. Follow the on-screen instructions for any initial human verification.

## Note on Security
Sensitive files like `user_data/`, `config.json`, and `last_run.json` are excluded from this repository by design to protect your private browser sessions and local file paths.
