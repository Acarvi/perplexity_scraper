import sys
import os
import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeout, Error as PlaywrightError

# Force the current directory into the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

# Local imports
from core.cli import show_banner, get_user_config, CLILogger, create_progress, save_last_run_time
from core.browser import launch_comet, check_for_challenges
from core.parser import scroll_feed, extract_links, scrape_article
from core.notebooklm import upload_to_notebooklm
from utils.text_processor import clean_noise, extract_entities
from utils.formatter import format_to_markdown

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
            # Combined Page Scraping Handshake (Phase 4 Sync)
            article_data = await scrape_article(
                context=context, 
                page=page, 
                url=link, 
                last_run_time=last_run_time, 
                mode=mode, 
                custom_hours=custom_hours, 
                logger=logger, 
                semaphore=semaphore, 
                category=category
            )
            if isinstance(article_data, dict):
                # Entity Extraction (Data Enrichment)
                article_data["entities"] = extract_entities(article_data["content"])
                return article_data
            return article_data # Could be "TOO_OLD"
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            logger.warning(f"Página omitida por timeout o cierre inesperado: {link}")
            log_debug(f"ARTICLE_ERROR: {str(e)[:100]}")
            return None
        except Exception as e:
            logger.error(f"Error procesando artículo {link}: {e}")
            return None
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
            print("\n[!] AVISO: No se pudo conectar a la sesión de Comet.")
            print("[!] El navegador está abierto pero la automatización está 'bloqueada'.")
            print("[!] SOLUCIÓN: Cierra Comet y ábrelo usando una 'tecla' o acceso directo")
            print("[!] que incluya el argumento: --remote-debugging-port=9222")
            raise RuntimeError("Browser initialization failed. Handshake refused on port 9222.")

        try:
            for cat in categories:
                cat_name = cat["name"]
                cat_url = f"https://www.perplexity.ai/discover/{cat.get('path', 'top')}"
                
                try:
                    await page.goto(cat_url, wait_until="domcontentloaded", timeout=60000)
                    await check_for_challenges(page, logger)
                except (PlaywrightTimeout, PlaywrightError) as e:
                    logger.warning(f"Warning: Página omitida por timeout (Categoría {cat_name}): {str(e)[:50]}")
                    continue

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
                            logger.info(f"Reached strict date threshold in {cat_name}. STOPPING category.")
                            break
                        if result and isinstance(result, dict):
                            cat_results.append(result)
                            # INCREMENTAL SAVING (Markdown - Per Article)
                            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                                f.write(format_to_markdown(
                                    result['category'], 
                                    result['title'], 
                                    result['date'], 
                                    result['url'], 
                                    result['content'], 
                                    result['external_sources'],
                                    result['related_stories']
                                ))
                    
                    if cat_results:
                        all_content.extend(cat_results)
                        # INCREMENTAL SAVING (JSON - Per Category)
                        existing_data = []
                        if os.path.exists(JSON_OUTPUT):
                            try:
                                with open(JSON_OUTPUT, "r", encoding="utf-8") as f:
                                    existing_data = json.load(f)
                            except: pass
                        
                        existing_data.extend(cat_results)
                        with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
                            json.dump(existing_data, f, indent=4, ensure_ascii=False)
                        
                        logger.success(f"Saved {len(cat_results)} stories from {cat_name}.")
            
            if all_content:
                logger.success(f"Total Stories Scraped: {len(all_content)}")
                save_last_run_time(start_time)
                
                # 4. NotebookLM Automation
                try:
                    success = await upload_to_notebooklm(context, os.path.abspath(OUTPUT_FILE), logger)
                    if success:
                        logger.success("NotebookLM Automation: Upload successful.")
                    else:
                        logger.warning("NotebookLM Automation: Completed with warnings.")
                except Exception as e:
                    logger.error(f"NotebookLM Automation failed: {e}")
            
            print("\n" + "="*40)
            print("MULTICATEGORY SCRAPE COMPLETE!")
            print("="*40)
            input("Press Enter to close results...")
            logger.info("Scraping and automation sequence complete.")
            
        except Exception as e:
            logger.error(f"Global Loop Error: {e}")
            log_debug(f"CRASH: {e}")
        finally:
            print("Limpiando sesión y cerrando ventanas temporales...")
            try:
                if browser_running: 
                    try: await browser_running.disconnect()
                    except: pass
                elif context:
                    try: await context.close()
                    except: pass
            except Exception as e: 
                log_debug(f"Error during final cleanup: {e}")
            
            log_debug("STEP: Comet Browser session disconnected safely.")

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
