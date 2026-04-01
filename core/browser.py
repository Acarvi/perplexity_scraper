import os
import json
import asyncio
import subprocess
from playwright_stealth import Stealth

user_home = os.path.expanduser("~")
DEFAULT_COMET_PATH = os.path.join(user_home, "AppData", "Local", "Comet", "Application", "comet.exe")
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")
USER_DATA_DIR = os.path.join(os.getcwd(), "user_data")

def get_real_browser_path():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                if "browser_path" in cfg and os.path.exists(cfg["browser_path"]):
                    return cfg["browser_path"]
        except Exception: pass
    return DEFAULT_COMET_PATH if os.path.exists(DEFAULT_COMET_PATH) else None

async def launch_comet(p, port=9222, headless=False, logger=None):
    browser_running = None
    try:
        browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=5000)
        logger.info("Connected to existing Comet session.")
        context = browser_running.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        return browser_running, context, page
    except Exception:
        actual_browser_path = get_real_browser_path()
        if not actual_browser_path:
            logger.error("Comet Browser execution path not found.")
            return None, None, None
            
        logger.info(f"Launching Browser with minimal resources...")
        cmd = [
            actual_browser_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={USER_DATA_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-gpu-compositing",
            "--disable-gpu-sandbox",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--js-flags=\"--max-old-space-size=2048\"",
            "--window-size=1280,720",
            "--disable-background-networking",
            "--disable-sync",
            "--mute-audio"
        ]
        if headless:
            cmd.append("--headless=new")
            
        subprocess.Popen(cmd)
        await asyncio.sleep(4)
        
        try:
            browser_running = await p.chromium.connect_over_cdp(f"http://localhost:{port}", timeout=10000)
            logger.info("Successfully connected to CDP.")
            context = browser_running.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            # Ultra strict resource blocking
            await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf,ico,css,mp4,webm}", lambda route: route.abort())
            
            return browser_running, context, page
        except Exception as e:
            logger.error(f"CDP connection failed: {e}")
            return None, None, None

async def check_for_challenges(page, logger):
    title = await page.title()
    content = await page.content()
    if "Just a moment..." in title or "Verify you are human" in content or "cf-challenge" in content:
        logger.warning("Bot challenge detected. Please verify humanity in the browser.")
        while "Just a moment..." in title or "Verify you are human" in content:
            await asyncio.sleep(5)
            title = await page.title()
            content = await page.content()
