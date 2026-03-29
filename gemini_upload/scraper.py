import asyncio
import os
import sys
import subprocess
import time
import re
import json
import queue
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BASE_URL = "https://www.perplexity.ai"
DISCOVER_URL = f"{BASE_URL}/discover"
OUTPUT_FILE = "perplexity_discover_content.txt"
MAX_ARTICLES = 10000 
MAX_SCROLLS = 100   
INITIAL_WAIT = 5  
ARTICLE_WAIT = 3  

# Detect Comet Browser path
user_home = os.path.expanduser("~")
DEFAULT_COMET_PATH = os.path.join(user_home, "AppData", "Local", "Comet", "Application", "comet.exe")
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")

def get_real_browser_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
            if "browser_path" in cfg and os.path.exists(cfg["browser_path"]):
                return cfg["browser_path"]
            elif "comet_path" in cfg and os.path.exists(cfg["comet_path"]):
                return cfg["comet_path"]
    
    # Priority 1: Default Comet
    if os.path.exists(DEFAULT_COMET_PATH):
        return DEFAULT_COMET_PATH
        
    # Priority 2: System-wide Comet
    sys_comet = r"C:\Program Files\Comet\Application\comet.exe"
    if os.path.exists(sys_comet):
        return sys_comet
            
    return None

COMET_PATH = get_real_browser_path()
USER_DATA_DIR = os.path.join(os.getcwd(), "user_data")
LAST_RUN_FILE = os.path.join(os.getcwd(), "last_run.json")

# Global thread-safe queue for logs
log_queue = queue.Queue()

async def log(message):
    try:
        print(message)
        # Only put in queue if not in CLI mode to avoid hangs
        if "--cli" not in sys.argv:
            log_queue.put(str(message))
    except Exception: pass

async def check_for_challenges(page):
    """
    Detects if the page is currently showing a Cloudflare/Bot challenge.
    Waits and alerts the user if needed.
    """
    while True:
        title = await page.title()
        content = await page.content()
        is_blocked = "Just a moment..." in title or "Verify you are human" in content or "cf-challenge" in content
        
        if is_blocked:
            await log("⚠️ BLOQUEO DE SEGURIDAD: Cloudflare detectado.")
            await log("👉 POR FAVOR, haz clic en el botón de 'Verify you are human' en el navegador Comet.")
            # Wait a few seconds and check again
            await asyncio.sleep(5)
        else:
            break

def get_last_run_time():
    """Loads the last run time from a JSON file."""
    if os.path.exists(LAST_RUN_FILE):
        try:
            with open(LAST_RUN_FILE, "r") as f:
                data = json.load(f)
                return datetime.fromisoformat(data["last_run"]).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc) - timedelta(hours=24)

def save_last_run_time(timestamp):
    """Saves the current run time to a JSON file."""
    with open(LAST_RUN_FILE, "w") as f:
        json.dump({"last_run": timestamp.isoformat()}, f)

def parse_any_date(date_text):
    """
    Parses both relative (e.g. '14m ago', 'yesterday') and absolute (e.g. 'Mar 25, 2026') dates.
    """
    now = datetime.now(timezone.utc)
    if not date_text: return now
    
    text = date_text.lower().strip()
    
    # 1. Handle Absolute Dates (e.g. 'mar 25, 2026' or 'mar 25')
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    for i, month in enumerate(months):
        if month in text:
            try:
                # Try with year first
                if "," in text or len(re.findall(r'\d{4}', text)) > 0:
                    # 'mar 25, 2026'
                    match = re.search(fr'{month}\s+(\d+),?\s+(\d{{4}})', text)
                    if match:
                        day, year = int(match.group(1)), int(match.group(2))
                        return datetime(year, i+1, day, tzinfo=timezone.utc)
                else:
                    # 'mar 25' (Assume current year)
                    match = re.search(fr'{month}\s+(\d+)', text)
                    if match:
                        day = int(match.group(1))
                        return datetime(now.year, i+1, day, tzinfo=timezone.utc)
            except Exception: pass
            break

    # 2. Handle Relative Dates
    match = re.search(r'(\d+)', text)
    if not match:
        if "yesterday" in text or "ayer" in text:
            return now - timedelta(days=1)
        return now
        
    val = int(match.group(1))
    
    if any(re.search(fr'\b{s}\b', text) for s in ["min", "m", "mins", "minutos"]):
        return now - timedelta(minutes=val)
    if any(re.search(fr'\b{s}\b', text) for s in ["h", "hr", "hrs", "hour", "hours", "hora", "horas"]):
        return now - timedelta(hours=val)
    if any(re.search(fr'\b{s}\b', text) for s in ["d", "day", "days", "día", "días"]):
        return now - timedelta(days=val)
        
    return now

def clean_noise(text):
    """
    Removes web noise and repetitive elements for cleaner NotebookLM input.
    """
    if not text: return ""
    
    # Remove common Perplexity UI noise
    noise_patterns = [
        r"(?i)Ask follow[- ]*up\b",
        r"(?i)Sources\b",
        r"(?i)View more\b",
        r"(?i)Discover more\b",
        r"(?i)Related stories\b",
        r"(?i)Copy link\b",
        r"(?i)Share\b",
        r"(?i)Model\b",
        r"(?i)Back to Discover\b"
    ]
    
    cleaned = text
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, "", cleaned)
    
    # Remove multiple newlines and extra spaces
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def is_recent_enough(date_text, last_run_time):
    if not date_text or "search" in date_text.lower() or "buscar" in date_text.lower():
        return True, "No date/Search"
    pub_time = parse_any_date(date_text)
    is_reached = pub_time > (last_run_time - timedelta(minutes=5))
    return is_reached, pub_time.strftime('%Y-%m-%d')

async def scrape_article(page, url, last_run_time):
    await log(f"Scraping: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await check_for_challenges(page)
        try:
            await page.wait_for_selector('h1, .prose, [dir="auto"]', timeout=10000)
        except Exception: pass
        await asyncio.sleep(ARTICLE_WAIT) 
        
        title_text = await page.title()
        title_text = title_text.replace(" - Perplexity", "").strip() if title_text else "Untitled"
        h1 = page.locator('h1').first
        if await h1.count() > 0:
            h1_txt = await h1.inner_text()
            if h1_txt: title_text = h1_txt
            
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        date_text = "Unknown"
        date_elem = soup.find("time")
        if not date_elem:
            meta_area = soup.find(class_=lambda x: x and ("meta" in x or "header" in x or "title" in x))
            if meta_area:
                date_elem = meta_area.find(string=re.compile(r"(ago|hace|minutes|hours|days|ayer|yesterday|minuto|hora|día)", re.I))
        if not date_elem:
            date_candidates = soup.find_all(string=re.compile(r"(ago|hace|minutes|hours|days|ayer|yesterday|minuto|hora|día)", re.I))
            for cand in date_candidates:
                txt = cand.strip()
                if 2 < len(txt) < 30:
                    date_elem = cand
                    break
        if date_elem:
            date_text = date_elem.strip()
            
        is_ok, p_time = is_recent_enough(date_text, last_run_time)
        if not is_ok:
            await log(f"SKIPPING: '{title_text}' is old.")
            return None

        content_loc = page.locator('.prose, [dir="auto"], article, main').first
        if await content_loc.count() > 0:
            content_text = await content_loc.inner_text()
        else:
            content_text = await page.evaluate("""() => {
                const clone = document.body.cloneNode(true);
                clone.querySelectorAll('nav, aside, header').forEach(el => el.remove());
                return clone.innerText.trim();
            }""")
            
        return {"url": url, "title": title_text, "content": content_text}
    except Exception as e:
        await log(f"Error scraping {url}: {e}")
        return None

async def main(full_run=False, headless=False):
    async with async_playwright() as p:
        start_time = datetime.now(timezone.utc)
        
        if full_run:
            last_run_time = datetime.now(timezone.utc) - timedelta(days=3650) # 10 years
            await log("🚀 FULL SCRAPE MODE: Ignoring last run timestamp.")
        else:
            last_run_time = get_last_run_time()
            await log(f"Last run: {last_run_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        port = 9222
        browser_running = None
        await log(f"Connecting to Comet Browser (CDP {port})...")
        try:
            browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=5000)
            await log("Connected to existing Comet session.")
            context = browser_running.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
        except Exception:
            # Check COMET_PATH again
            actual_browser_path = get_real_browser_path()
            if not actual_browser_path:
                await log("⚠️ COMET BROWSER NOT FOUND.")
                await log("Por favor, introduce la ruta COMPLETA del ejecutable comet.exe (ej: C:\\Program Files\\Comet\\Application\\comet.exe)")
                if "--cli" in sys.argv:
                    new_path = input("Ruta a comet.exe: ").strip().replace('"', '')
                    if os.path.exists(new_path):
                        with open(CONFIG_FILE, "w") as f:
                            json.dump({"browser_path": new_path}, f)
                        actual_browser_path = new_path
                else:
                    await log("❌ Modo GUI: No se encontro Comet. Usa la Opción 2 (CLI) para configurarlo.")
            
            await log(f"Launching Browser natively via subprocess: {actual_browser_path or 'Cannot launch'}")
            if not actual_browser_path:
                await log("❌ Fatal: Need a real browser path to launch natively.")
                return
                
            cmd = [
                actual_browser_path,
                f"--remote-debugging-port={port}",
                f"--user-data-dir={USER_DATA_DIR}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--js-flags=\"--max-old-space-size=2048\"",
                "--window-size=1280,720"
            ]
            if headless:
                # Use new headless mode which acts more like a real browser
                cmd.append("--headless=new")
                
            subprocess.Popen(cmd)
            await log("Waiting 4 seconds for browser to start...")
            await asyncio.sleep(4)
            
            try:
                browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=10000)
                await log("Successfully connected to native browser via CDP.")
                context = browser_running.contexts[0]
                page = context.pages[0] if context.pages else await context.new_page()
            except Exception as e:
                await log(f"Failed to connect to CDP after native launch: {e}")
                return
        
        # Block heavy resources to save CPU/GPU
        await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf}", lambda route: route.abort())
        
        await page.bring_to_front()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        await log(f"Navigating to {DISCOVER_URL}...")
        
        # 1. INITIAL CHALLENGE CHECK
        await page.goto(DISCOVER_URL, wait_until="domcontentloaded", timeout=45000)
        await check_for_challenges(page)
        
        await asyncio.sleep(2)
        await page.reload(wait_until="domcontentloaded")
        await check_for_challenges(page)
        await asyncio.sleep(INITIAL_WAIT)

        # --- SCROLL LOOP ---
        await log("Scrolling feed for new stories...")
        scroll_count = 0
        stuck_count = 0
        null_timestamp_count = 0
        last_timestamp = None
        reached_end = False
        
        while scroll_count < MAX_SCROLLS and not reached_end:
            scroll_count += 1
            try:
                await page.keyboard.press("End")
                await asyncio.sleep(1)
                # Smooth scroll: window.scrollBy(0, 300) -> Wait 500ms -> Repeat
                for _ in range(10): # Scroll 3000px in total but smoothly
                    await page.evaluate("window.scrollBy(0, 300)")
                    await asyncio.sleep(0.5)
                
                await page.evaluate("""() => {
                    const cards = Array.from(document.querySelectorAll('a.group\\\\/card'));
                    if (cards.length > 0) cards[cards.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                }""")
                await asyncio.sleep(1)
                
                current_timestamp = await page.evaluate("""() => {
                    const mainContainer = document.querySelector('[scrollable="true"]') || document.querySelector('main') || document.body;
                    const elements = Array.from(mainContainer.querySelectorAll('span, div, p, time, small'));
                    const timePattern = /\\d+\\s*(m|h|d|min|hour|day|seg|sec|hora|día)|yesterday|ayer|ago|hace/i;
                    const matches = elements.filter(el => {
                        const text = el.innerText.trim();
                        return text.length > 0 && text.length < 35 && timePattern.test(text);
                    });
                    return matches.length > 0 ? matches[matches.length - 1].innerText.trim() : null;
                }""")
                
                if current_timestamp:
                    if current_timestamp == last_timestamp:
                        stuck_count += 1
                        if stuck_count >= 5: break
                    else:
                        stuck_count = 0
                        last_timestamp = current_timestamp
                        
                    is_rec, t_str = is_recent_enough(current_timestamp, last_run_time)
                    await log(f"Scroll {scroll_count}: {current_timestamp} (Calc: {t_str})")
                    if not is_rec:
                        reached_end = True
                else:
                    null_timestamp_count += 1
                    if null_timestamp_count >= 5: break
            except Exception as e:
                await log(f"Scroll error: {e}")
                break

        # --- LINK EXTRACTION (REFINED) ---
        await log("Extracting story links with timestamps...")
        
        # Check if we are even logged in
        if await page.locator('button:has-text("Sign Up"), button:has-text("Sign In")').count() > 0:
            await log("⚠️ WARNING: You appear to be logged out. Please log in in the Comet browser for best results.")

        # This JS script extracts both the link and the nested timestamp from each card
        story_data = await page.evaluate("""() => {
            const results = [];
            const cards = Array.from(document.querySelectorAll('a[href*="/page/"], a[href*="/discover/"], a.group\\\\/card'));
            
            cards.forEach(card => {
                const href = card.getAttribute('href');
                if (!href || href.includes('auth') || href.includes('library') || href.strip === 'discover') return;
                
                // Find timestamp in this card
                // Current selector: div.gap-x-xs.items-center span.truncate
                const timeElem = card.querySelector('div.gap-x-xs.items-center span.truncate') || 
                                 card.querySelector('span.truncate') || 
                                 card.querySelector('time');
                
                const timestamp = timeElem ? timeElem.innerText.trim() : null;
                results.push({ href, timestamp });
            });
            return results;
        }""")
        
        await log(f"Total potential links detected on page: {len(story_data)}")
        
        links_to_scrape = []
        seen_urls = set()
        
        for item in story_data:
            href = item['href']
            timestamp = item['timestamp']
            
            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            if full_url in seen_urls: continue
            
            # 1. Path Filtering
            if not any(x in href for x in ["/page/", "/discover/"]): continue
            if any(x in href for x in ["/auth", "/login", "/privacy", "/terms", "/settings", "/library", "/pro", "/download", "/collections"]): continue
            
            # 2. Date Filtering (PRE-NAVIGATION)
            if timestamp and not full_run:
                is_rec, t_str = is_recent_enough(timestamp, last_run_time)
                if not is_rec:
                    # Optional: await log(f"Skipping old story: {href} ({timestamp})")
                    continue
            
            seen_urls.add(full_url)
            links_to_scrape.append(full_url)

        await log(f"Filtered down to {len(links_to_scrape)} new stories. Processing...")
        
        all_content = []
        for link in links_to_scrape[:MAX_ARTICLES]:
            # We already checked the date, so we can scrape directly (with a quick re-check if needed)
            article_data = await scrape_article(page, link, last_run_time)
            if article_data: all_content.append(article_data)
        
        if all_content:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for item in all_content:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    clean_text = clean_noise(item['content'])
                    
                    f.write(f"[NOTICIA_ID: {timestamp}]\n")
                    f.write(f"TITULO: {item['title']}\n")
                    f.write(f"URL: {item['url']}\n")
                    f.write(f"RESUMEN_LIMPIO: {clean_text}\n")
                    f.write("--- FIN DE NOTICIA ---\n\n")
                    
            await log(f"SAVED: {len(all_content)} results to {OUTPUT_FILE}")
            save_last_run_time(start_time)
        else:
            await log("Finished: No new stories found.")
        
        # Keep browser open for a few seconds so user sees it
        await asyncio.sleep(5)
        if browser_running:
            await browser_running.close()

if __name__ == "__main__":
    import sys
    if "--cli" in sys.argv:
        print("--- RUNNING IN CLI MODE (ULTRA STABLE) ---")
        is_full = "--full" in sys.argv
        is_headless = "--headless" in sys.argv
        asyncio.run(main(full_run=is_full, headless=is_headless))
    else:
        asyncio.run(main())
