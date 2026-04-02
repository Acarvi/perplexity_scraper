import asyncio
import sys
import os
import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Local imports
from core.cli import show_banner, get_user_config, CLILogger, create_progress, save_last_run_time
from core.browser import launch_comet, check_for_challenges, open_url_in_comet
from core.parser import scroll_feed, extract_links, scrape_article
from utils.text_processor import clean_noise, extract_entities

OUTPUT_FILE = "perplexity_discover_content.txt"
JSON_OUTPUT = "perplexity_data.json"
DISCOVER_URL = "https://www.perplexity.ai/discover"
CONFIG_FILE = "config.json"

async def process_article(context, link, last_run_time, mode, custom_hours, logger, semaphore, progress, task_id):
    async with semaphore:
        # Mandatory Comet Navigation protocol: open via Magic Command
        open_url_in_comet(link)
        await asyncio.sleep(3) # Wait for tab activation
        
        # Find the page in the context
        page = None
        for p in context.pages:
            if link in p.url:
                page = p
                break
        
        if not page:
            # Fallback for robustness
            page = await context.new_page()
            await page.goto(link, wait_until="domcontentloaded")
            
        try:
            article_data = await scrape_article(page, link, last_run_time, mode, custom_hours, logger)
            if article_data:
                # Entity Extraction (Data Enrichment)
                article_data["entities"] = extract_entities(article_data["content"])
                return article_data
        finally:
            if page: await page.close()
            progress.update(task_id, advance=1)
        return None

async def run_scraper():
    # Flag --set-path handled here
    if "--set-path" in sys.argv:
        try:
            path_idx = sys.argv.index("--set-path") + 1
            new_path = sys.argv[path_idx]
            with open(CONFIG_FILE, "w") as f:
                json.dump({"browser_path": new_path}, f)
            print(f"Path saved: {new_path}")
            return
        except Exception: return

    show_banner()
    mode, last_run_time, custom_hours = get_user_config()
    
    logger = CLILogger()
    start_time = datetime.now(timezone.utc)
    semaphore = asyncio.Semaphore(5)
    
    async with async_playwright() as p:
        browser, context, page = await launch_comet(p, headless=False, logger=logger)
        if not page:
            logger.error("Could not initialize browser.")
            return

        try:
            logger.info(f"Navigating to {DISCOVER_URL}...")
            await page.goto(DISCOVER_URL, wait_until="domcontentloaded", timeout=60000)
            await check_for_challenges(page, logger)
            
            with create_progress() as progress:
                scroll_task = progress.add_task("[cyan]Scrolling feed...", total=100)
                await scroll_feed(page, 100, last_run_time, mode, custom_hours, logger, progression=progress.tasks[0])
            
            links = await extract_links(page, last_run_time, mode, custom_hours, logger)
            logger.success(f"Detected {len(links)} stories.")
            
            if not links: return

            # Concurrency Phase
            all_content = []
            with create_progress() as progress:
                scrape_task = progress.add_task("[green]Scraping articles...", total=len(links))
                tasks = [process_article(context, link, last_run_time, mode, custom_hours, logger, semaphore, progress, scrape_task) for link in links]
                results = await asyncio.gather(*tasks)
                all_content = [r for r in results if r]
            
            if all_content:
                # Append Mode persistence
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    for item in all_content:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[NOTICIA_ID: {ts}]\nTITULO: {item['title']}\nURL: {item['url']}\n\n")
                
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
                
                logger.success(f"Saved to {OUTPUT_FILE} and {JSON_OUTPUT}")
                save_last_run_time(start_time)
            
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            if browser: await browser.close()

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
