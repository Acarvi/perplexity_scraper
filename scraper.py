import asyncio
import sys
import os

# Force the current directory into the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Local imports
from core.cli import show_banner, get_user_config, CLILogger, create_progress, save_last_run_time
from core.browser import launch_comet, check_for_challenges, open_url_in_comet
from core.parser import scroll_feed, extract_links, scrape_article
from core.notebooklm import automate_notebooklm_upload
from utils.text_processor import clean_noise, extract_entities
from utils.formatter import format_premium_markdown

DEBUG_LOG = "debug_scraper.log"

def log_debug(msg):
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")

OUTPUT_FILE = "perplexity_discover_content.md"
JSON_OUTPUT = "perplexity_data.json"
DISCOVER_URL = "https://www.perplexity.ai/discover"
CONFIG_FILE = "config.json"

async def process_article(context, link, last_run_time, mode, custom_hours, logger, semaphore, progress, task_id, category):
    async with semaphore:
        # Open internal tab for stability
        page = await context.new_page()
        
        try:
            # Combined Page Scraping Handshake
            article_data = await scrape_article(context, page, link, last_run_time, mode, custom_hours, logger, category=category)
            if article_data:
                # Entity Extraction (Data Enrichment)
                article_data["entities"] = extract_entities(article_data["content"])
                return article_data
        finally:
            progress.update(task_id, advance=1)
            # Mandatory closure for memory health
            try:
                await page.close()
            except: pass
        return None

async def run_scraper():
    show_banner()
    mode, start_date, custom_hours = get_user_config()
    
    logger = CLILogger()
    start_time = datetime.now(timezone.utc)
    semaphore = asyncio.Semaphore(5)
    
    categories = [
        {"name": "General", "path": "top"},
        {"name": "Tech", "path": "tech"},
        {"name": "Business", "path": "business"},
        {"name": "Science", "path": "science"},
        {"name": "Sports", "path": "sports"},
        {"name": "Entertainment", "path": "entertainment"}
    ]
    
    all_content = []
    
    async with async_playwright() as p:
        browser_running, context, page, comet_proc = await launch_comet(p, headless=False, logger=logger)
        if not page:
            raise RuntimeError("Browser initialization failed. Check comet.exe path.")

        try:
            for cat in categories:
                cat_name = cat["name"]
                cat_url = f"https://www.perplexity.ai/discover/{cat.get('path', 'top')}"
                
                logger.info(f"--- SCRAPING CATEGORY: {cat_name} ---")
                log_debug(f"STEP: Navigating to {cat_url}")
                
                await page.goto(cat_url, wait_until="domcontentloaded", timeout=60000)
                await check_for_challenges(page, logger)
                
                with create_progress() as progress:
                    scroll_task = progress.add_task(f"[cyan]Scrolling {cat_name}...", total=100)
                    await scroll_feed(page, 30, start_date, mode, custom_hours, logger, progress=progress, task_id=scroll_task)
                
                links = await extract_links(page, start_date, mode, custom_hours, logger)
                logger.success(f"Found {len(links)} links in {cat_name}.")
                
                if not links: continue

                with create_progress() as progress:
                    scrape_task = progress.add_task(f"[green]Scraping {cat_name}...", total=len(links))
                    cat_results = []
                    for link in links:
                        result = await process_article(context, link, start_date, mode, custom_hours, logger, semaphore, progress, scrape_task, cat_name)
                        if result == "TOO_OLD":
                            logger.info(f"Reached old content threshold in {cat_name}. Stopping category.")
                            break
                        if result:
                            cat_results.append(result)
                    
                    all_content.extend(cat_results)
            
            if all_content:
                # NotebookLM Structured Markdown Export
                # Premium Editorial Markdown Edition
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    for item in all_content:
                        f.write(format_premium_markdown(item))
                
                # Structured JSON Export
                existing_data = []
                if os.path.exists(JSON_OUTPUT):
                    try:
                        with open(JSON_OUTPUT, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                    except: pass
                
                existing_data.extend(all_content)
                with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=4, ensure_ascii=False)
                
                logger.success(f"Total Stories Scraped: {len(all_content)}")
                save_last_run_time(start_time)
                
                # Phase 4: NotebookLM Automation (Paso 2)
                # This opens a new tab in the same CDP session to automate the upload
                try:
                    success = await automate_notebooklm_upload(context, os.path.abspath(OUTPUT_FILE), logger)
                    if success:
                        logger.success("NotebookLM Automation: Upload successful.")
                    else:
                        logger.warning("NotebookLM Automation: Completed with warnings (check browser).")
                except Exception as e:
                    logger.error(f"NotebookLM Automation failed: {e}")
            
            print("\n" + "="*40)
            print("MULTICATEGORY SCRAPE COMPLETE!")
            print("="*40)
            input("Press Enter to close results...")
            
        except Exception as e:
            logger.error(f"Global Loop Error: {e}")
            log_debug(f"CRASH: {e}")
        finally:
            log_debug("STEP: Enforcing absolute window cleanup")
            try:
                if context: await context.close()
                if browser_running: await browser_running.close()
            except: pass
            
            # Persistent cleanup for comet process
            if comet_proc:
                try:
                    if comet_proc.poll() is None:
                        logger.info("Forcing termination of Comet process...")
                        comet_proc.terminate()
                        await asyncio.sleep(2)
                        if comet_proc.poll() is None:
                            comet_proc.kill()
                except: pass
            
            log_debug("STEP: Comet Browser session terminated.")

if __name__ == "__main__":
    import traceback
    import sys
    try:
        asyncio.run(run_scraper())
    except KeyboardInterrupt:
        pass
    except Exception:
        print("\n" + "="*60)
        print("!!! FATAL CRASH REPORT !!!")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        input("Press Enter to exit and check the logs...")
        sys.exit(1)
