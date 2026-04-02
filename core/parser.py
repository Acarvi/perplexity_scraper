import asyncio
from bs4 import BeautifulSoup
import re
from utils.text_processor import is_recent_enough, clean_noise

ARTICLE_WAIT = 3
BASE_URL = "https://www.perplexity.ai"

async def scrape_article(page, url, last_run_time, mode, custom_hours, logger, category="Uncategorized"):
    logger.info(f"Deep Scraping [{category}]: {url}")
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
            date_text = date_elem.get_text().strip()
            
        is_ok, p_time = is_recent_enough(date_text, last_run_time, mode=mode, custom_hours=custom_hours)
        if not is_ok:
            logger.warning(f"SKIPPING: '{title_text}' is outside range ({p_time}).")
            return None

        # Content extraction
        content_loc = page.locator('.prose, [dir="auto"], article, main').first
        content_text = await (content_loc.inner_text() if await content_loc.count() > 0 else page.evaluate("() => document.body.innerText"))
        
        # Deep Extraction: Related Stories Summarization
        related_links = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href*="/discover/"]'));
            return links.map(a => ({
                title: a.innerText.trim(),
                url: a.href
            })).filter(l => l.title.length > 5 && !l.url.endsWith('/discover'));
        }""")
        
        deep_related = []
        # Limit to top 3 related for performance
        for rel in related_links[:3]:
            try:
                # Navigate in SAME tab to save memory (we already have parent content)
                logger.info(f"  -> Deep Dive: {rel['title']}")
                await page.goto(rel['url'], wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2)
                rel_content_loc = page.locator('.prose, [dir="auto"], article, main').first
                rel_text = await (rel_content_loc.inner_text() if await rel_content_loc.count() > 0 else "No content.")
                # Basic summarization: take first 2 paragraphs or 500 chars
                summary = rel_text[:500].strip() + "..."
                deep_related.append({"title": rel['title'], "url": rel['url'], "summary": summary})
            except: pass
        
        return {
            "url": url, 
            "title": title_text, 
            "content": content_text, 
            "date": date_text,
            "category": category,
            "related_stories": deep_related
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None
    finally:
        # Crucial Memory Fix: Ensure tab closes no matter what
        try:
            await page.close()
        except: pass

async def scroll_feed(page, max_scrolls, last_run_time, mode, custom_hours, logger, progress, task_id):
    logger.info("Deep Discovering new stories...")
    scroll_count = 0
    stuck_count = 0
    last_timestamp = None
    reached_end = False
    
    while scroll_count < max_scrolls and not reached_end:
        scroll_count += 1
        progress.update(task_id, total=max_scrolls, completed=scroll_count, description=f"Scrolling ({scroll_count}/{max_scrolls})")
        
        await page.evaluate("window.scrollBy(0, 2000)") # Increased scroll jump
        await asyncio.sleep(2)
        
        # Date Check Logic
        current_timestamp = await page.evaluate("""() => {
            const elements = Array.from(document.querySelectorAll('span, time, div'));
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
                logger.info(f"Reached date threshold: {t_str}")
                reached_end = True
        else:
            stuck_count += 1
            if stuck_count >= 5: break
    
    return reached_end

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
