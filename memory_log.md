### Status: STRICT REFACTOR COMPLETED (100% Stable)

## 2026-04-01: Strict CLI-HighPerf Implementation

### Changes Made
1. **Total GUI Eradication**: Deleted `dashboard.py` and purged `flet` from `requirements.txt`.
2. **Mandatory Comet Protocol**: Replaced standard browser launch with the **Magic Command** shortcut launch (`os.system`) and CDP connection on port 9222.
3. **High Concurrency**: Implemented `asyncio.Semaphore(5)` to handle 5 tabs simultaneously via `asyncio.gather`.
4. **Data Enrichment**: Integrated entity extraction for tech stacks and companies. Outputs structured JSON.
5. **Bug Resolution**: Re-architected date parsing regex to capture units correctly (e.g., `14m`) and enforced **Append Mode** for all data persistence.
6. **Automation**: `perplexity_scraper.bat` now forces a mandatory regression test pass before execution.

## 2026-04-02: Modular Stability & App-Mode Protocol

### Changes Made
1. **Modular Consistency**: Injected root path into `scraper.py` and `tests/run_all_tests.py` using `sys.path` injection. Added `__init__.py` to all sub-packages.
2. **Comet App-Mode**: Restored `core/browser.py` to launch `comet.exe` with the `--app` flag specifically for the Perplexity Discover feed, ensuring a clean, dedicated UX.
3. **Regression Pass**: Mandatory 6/6 test pass confirmed for the new modular structure.

## 2026-04-02: Multi-Category & Deep Scraping Logic

### Changes Made
1. **Multi-Category Loop**: Refactored `scraper.py` to iterate through 'Tech', 'Business', 'Science', 'Sports', and 'Entertainment' using direct URL navigation.
2. **Tab Memory Fix**: Implemented strict `try/finally` blocks in `core/parser.py` to ensure `await page.close()` is called for every article, preventing memory leaks.
3. **NotebookLM Optimization**: Enhanced `scrape_article` to extract "Related Stories" and updated TXT/JSON output with Markdown headers for better ingestion.
4. **CLI Upgrades**: Defaulted scrape window to 24h and added support for the `--since Xh` flag for custom historical ranges.

### Status: MISSION SUCCESSFUL (Powerful & Memory-Efficient)
