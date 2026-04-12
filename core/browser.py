import os
import json
import asyncio
import subprocess
from playwright_stealth import Stealth
from playwright.async_api import Error as PlaywrightError

user_home = os.path.expanduser("~")
DEFAULT_COMET_PATH = os.path.join(user_home, "AppData", "Local", "Perplexity", "Comet", "Application", "comet.exe")
COMET_LNK = r"C:\Users\Acarvi\Desktop\Comet.lnk"
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")
USER_DATA_DIR = os.path.join(os.getcwd(), "user_data")
USER_DATA_SCRAPER = os.path.join(os.getcwd(), "user_data_scraper")

async def is_comet_running():
    try:
        output = subprocess.check_output('tasklist /FI "IMAGENAME eq comet.exe" /NH', shell=True).decode('utf-8', 'ignore')
        return "comet.exe" in output.lower()
    except:
        return False

def cleanup_port(port):
    """Kills any process using the specified port on Windows."""
    try:
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True).decode('utf-8', 'ignore')
        for line in output.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid and pid != "0":
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
    except:
        pass
    return False

async def launch_comet(p, port=9222, headless=False, logger=None):
    browser_running = None
    browser_context = None
    discover_url = "https://www.perplexity.ai/discover"
    
    logger.info(f"Connecting to Comet via Shared Session (Port {port})...")
    
    # 1. Try Shared Session connection (Preferred)
    try:
        browser_running = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=3000)
        browser_context = browser_running.contexts[0]
        logger.success("Connected to active Comet session.")
    except Exception:
        # Check if already running but refused connection (locked)
        if await is_comet_running():
            logger.warning("Main Comet is open but 'locked' (no debugging port).")
            logger.info("Entering Parallel Mode: Launching a dedicated scraper window...")
            
            # 🧹 LIMPIEZA DE ZOMBIS: Nos aseguramos de que el puerto 9223 esté libre
            cleanup_port(9223)
            
            try:
                # OPTION C: Isolated Parallel Launch (Robust Persistent Context)
                browser_context = await p.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_SCRAPER,
                    executable_path=DEFAULT_COMET_PATH,
                    headless=headless,
                    # ✅ MODO SÚPER SIGILO: Eliminamos rastro de automatización y avisos feos
                    ignore_default_args=["--enable-automation", "--no-sandbox"],
                    args=[
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--skip-first-run-ui",
                        "--disable-search-engine-choice-screen",
                        "--disable-sync",
                        "--remote-debugging-port=9223",
                        "--disable-blink-features=AutomationControlled",
                        "--test-type",
                        f"--app={discover_url}"
                    ],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                )
                logger.success("Dedicated Scraper Window launched (Parallel Mode).")
            except Exception as e:
                logger.error(f"Failed to launch parallel window: {e}")
                return None, None, None, None
        else:
            # Not running, launch standard persistent context
            cleanup_port(port)
            logger.info("Launching Comet with debugging port enabled...")
            try:
                browser_context = await p.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_SCRAPER,
                    executable_path=DEFAULT_COMET_PATH,
                    headless=headless,
                    # ✅ MODO SÚPER SIGILO
                    ignore_default_args=["--enable-automation", "--no-sandbox"],
                    args=[
                        f"--remote-debugging-port={port}",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--skip-first-run-ui",
                        "--disable-search-engine-choice-screen",
                        "--disable-blink-features=AutomationControlled",
                        "--test-type",
                        f"--app={discover_url}"
                    ],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                )
                logger.success("Comet launched successfully.")
            except Exception as e:
                logger.error(f"Failed to launch Comet: {e}")
                return None, None, None, None

    # 2. Scraper Isolation & Setup
    try:
        stealth = Stealth()
        
        async def abort_route(route):
            try: await route.abort()
            except: pass

        async def setup_page(page):
            try:
                if page.is_closed(): return
                await stealth.apply_stealth_async(page)
                await page.set_extra_http_headers({
                    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                })
                # ✅ VISUALES PREMIUM: Permitimos CSS e imágenes para que se vea "bonito"
                # (Se ha eliminado el bloqueo de recursos como pidió el usuario)
                pass
            except: pass

        # Reutilizamos la pestaña existente de forma inteligente
        if browser_context.pages:
            page = browser_context.pages[0]
            curr_url = page.url
            if "perplexity.ai/discover" not in curr_url:
                logger.info(f"Navigating the main tab to {discover_url}...")
                await page.goto(discover_url, wait_until="domcontentloaded", timeout=45000)
        else:
            page = await browser_context.new_page()
            await page.goto(discover_url, wait_until="domcontentloaded", timeout=45000)
            
        await setup_page(page)
        
        browser_context.on("page", setup_page)
        return browser_running, browser_context, page, None
    except Exception as e:
        logger.error(f"Failed to setup context: {e}")
        return None, None, None, None


async def check_for_challenges(page, logger):
    try:
        title = await page.title()
        content = await page.content()
        if "Just a moment..." in title or "Verify you are human" in content or "cf-challenge" in content:
            logger.warning("Bot challenge detected. Please verify humanity in the browser.")
            while "Just a moment..." in title or "Verify you are human" in content:
                await asyncio.sleep(5)
                title = await page.title()
                content = await page.content()
    except: pass
