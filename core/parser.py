import asyncio
from bs4 import BeautifulSoup
import re
from utils.text_processor import is_recent_enough, clean_noise

ARTICLE_WAIT = 3
BASE_URL = "https://www.perplexity.ai"

async def scrape_article(page, url, last_run_time, mode, custom_hours, logger):
    logger.info(f"Scraping: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(ARTICLE_WAIT) 
        
        title_text = await page.title()
        title_text = title_text.replace(" - Perplexity", "").strip() if title_text else "Untitled"
        
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        date_text = "Unknown"
        date_elem = soup.find("time")
        if not date_elem:
            meta_area = soup.find(class_=lambda x: x and ("meta" in x or "header" in x or "title" in x))
            if meta_area:
                date_elem = meta_area.find(string=re.compile(r"(ago|hace|minutes|hours|days|ayer|yesterday|minuto|hora|día)", re.I))
        if date_elem:
            date_text = date_elem.strip()
            
        is_ok, p_time = is_recent_enough(date_text, last_run_time, mode=mode, custom_hours=custom_hours)
        if not is_ok:
            logger.warning(f"SKIPPING: '{title_text}' is outside range ({p_time}).")
            return None

        content_loc = page.locator('.prose, [dir="auto"], article, main').first
        content_text = await (content_loc.inner_text() if await content_loc.count() > 0 else page.evaluate("() => document.body.innerText"))
            
        return {"url": url, "title": title_text, "content": content_text}
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None

async def scroll_feed(page, max_scrolls, last_run_time, mode, custom_hours, logger, progression):
    # progression is a rich Progress task
    logger.info("Discovering new stories...")
    scroll_count = 0
    stuck_count = 0
    last_timestamp = None
    reached_end = False
    
    while scroll_count < max_scrolls and not reached_end:
        scroll_count += 1
        progression.update(total=max_scrolls, completed=scroll_count, description=f"Scrolling ({scroll_count}/{max_scrolls})")
        
        await page.evaluate("window.scrollBy(0, 1000)")
        await asyncio.sleep(1.5)
        
        current_timestamp = await page.evaluate("""() => {
            const elements = Array.from(document.querySelectorAll('span, time'));
            const timePattern = /\\d+\\s*(m|h|d|min|hour|day|seg|sec|hora|día)|yesterday|ayer|ago|hace/i;
            const matches = elements.filter(el => timePattern.test(el.innerText));
            return matches.length > 0 ? matches[matches.length - 1].innerText.trim() : null;
        }""")
        
        if current_timestamp:
            if current_timestamp == last_timestamp:
                stuck_count += 1
                if stuck_count >= 5: break
            else:
                stuck_count = 0
                last_timestamp = current_timestamp
                
            is_rec, t_str = is_recent_enough(current_timestamp, last_run_time, mode=mode, custom_hours=custom_hours)
            if not is_rec:
                reached_end = True
        else:
            stuck_count += 1
            if stuck_count >= 5: break

async def extract_links(page, last_run_time, mode, custom_hours, logger):
    story_data = await page.evaluate("""() => {
        const results = [];
        const cards = Array.from(document.querySelectorAll('a[href*="/page/"], a[href*="/discover/"]'));
        cards.forEach(card => {
            const href = card.getAttribute('href');
            const timeElem = card.querySelector('span.truncate') || card.querySelector('time');
            results.push({ href, timestamp: timeElem ? timeElem.innerText.trim() : null });
        });
        return results;
    }""")
    
    links = []
    seen = set()
    for item in story_data:
        full_url = item['href'] if item['href'].startswith("http") else f"https://www.perplexity.ai{item['href']}"
        if full_url in seen: continue
        if "/page/" not in full_url and "/discover/" not in full_url: continue
        
        if item['timestamp']:
            is_rec, _ = is_recent_enough(item['timestamp'], last_run_time, mode=mode, custom_hours=custom_hours)
            if not is_rec: continue
            
        seen.add(full_url)
        links.append(full_url)
    return links
