import asyncio
import sys
import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Local imports
from core.cli import show_banner, get_user_config, CLILogger, create_progress, save_last_run_time
from core.browser import launch_comet, check_for_challenges
from core.parser import scroll_feed, extract_links, scrape_article
from utils.text_processor import clean_noise

OUTPUT_FILE = "perplexity_discover_content.txt"
DISCOVER_URL = "https://www.perplexity.ai/discover"

async def run_scraper():
    show_banner()
    mode, last_run_time, custom_hours = get_user_config()
    
    logger = CLILogger()
    start_time = datetime.now(timezone.utc)
    
    async with async_playwright() as p:
        # Launch Browser
        browser, context, page = await launch_comet(p, headless=False, logger=logger)
        if not page:
            logger.error("Could not initialize browser.")
            return

        try:
            logger.info(f"Navigating to {DISCOVER_URL}...")
            await page.goto(DISCOVER_URL, wait_until="domcontentloaded", timeout=60000)
            await check_for_challenges(page, logger)
            
            # 1. SCROLLING PHASE
            with create_progress() as progress:
                scroll_task = progress.add_task("[cyan]Scrolling feed...", total=100)
                await scroll_feed(page, 100, last_run_time, mode, custom_hours, logger, progression=progress.tasks[0])
            
            # 2. LINK EXTRACTION
            links = await extract_links(page, last_run_time, mode, custom_hours, logger)
            logger.success(f"Detected {len(links)} new stories to process.")
            
            if not links:
                logger.info("No work to do. Exiting.")
                return

            # 3. SCRAPING PHASE
            all_content = []
            with create_progress() as progress:
                scrape_task = progress.add_task("[green]Scraping articles...", total=len(links))
                
                for i, link in enumerate(links):
                    # Open article
                    article_data = await scrape_article(page, link, last_run_time, mode, custom_hours, logger)
                    if article_data:
                        all_content.append(article_data)
                    
                    progress.update(scrape_task, advance=1)
            
            # 4. SAVE OUTPUT
            if all_content:
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    for item in all_content:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        clean_text = clean_noise(item['content'])
                        
                        f.write(f"[NOTICIA_ID: {ts}]\n")
                        f.write(f"TITULO: {item['title']}\n")
                        f.write(f"URL: {item['url']}\n")
                        f.write(f"RESUMEN_LIMPIO: {clean_text}\n")
                        f.write("--- FIN DE NOTICIA ---\n\n")
                
                logger.success(f"Saved {len(all_content)} results to {OUTPUT_FILE}")
                save_last_run_time(start_time)
            
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        finally:
            if browser:
                await browser.close()
                logger.info("Browser closed.")

if __name__ == "__main__":
    try:
        asyncio.run(run_scraper())
    except KeyboardInterrupt:
        print("\n[bold red]Interrupted by user.[/bold red]")
    except Exception as e:
        print(f"\n[bold red]Fatal error: {e}[/bold red]")
