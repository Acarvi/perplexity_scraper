import asyncio
from bs4 import BeautifulSoup
import re
from utils.text_processor import is_recent_enough, clean_noise

ARTICLE_WAIT = 3
BASE_URL = "https://www.perplexity.ai"

async def scrape_article(context, page, url, last_run_time, mode, custom_hours, logger, category="Uncategorized"):
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
                date_elem = meta_area.find(string=re.compile(r"(ago|hace|minutes|hours|days|ayer|yesterday|minuto|hora|día|Published)", re.I))
        if date_elem:
            date_text = date_elem.get_text().strip()
            
        is_ok, p_time = is_recent_enough(date_text, last_run_time, mode=mode, custom_hours=custom_hours)
        if not is_ok:
            if p_time == "UNKNOWN_DATE":
                logger.error(f"FAILURE: Could not extract date for '{title_text}'. Skipping to avoid filter bypass.")
            else:
                logger.warning(f"SKIPPING: '{title_text}' is outside range ({p_time}).")
            return "TOO_OLD" if p_time != "UNKNOWN_DATE" else None

        content_loc = page.locator('.prose, [dir="auto"], article, main').first
        content_text = await (content_loc.inner_text() if await content_loc.count() > 0 else page.evaluate("() => document.body.innerText"))
        content_text = clean_noise(content_text)
        
        # Deep Extraction: Related Stories Summarization
        related_links = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href*="/discover/"]'));
            return links.map(a => ({
                title: a.innerText.trim(),
                url: a.href
            })).filter(l => l.title.length > 5 && !l.url.endsWith('/discover'));
        }""")
        
        deep_related = []
        # Support deep scraping of related stories in new tabs
        for rel in related_links[:3]:
            rel_page = None
            try:
                logger.info(f"  -> Deep Related Scraping: {rel['title']}")
                rel_page = await context.new_page()
                await rel_page.goto(rel['url'], wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                rel_content_loc = rel_page.locator('.prose, [dir="auto"], article, main').first
                rel_text = await (rel_content_loc.inner_text() if await rel_content_loc.count() > 0 else "No content.")
                rel_text = clean_noise(rel_text)
                
                deep_related.append({
                    "title": rel['title'], 
                    "url": rel['url'], 
                    "content": rel_text.strip()
                })
            except Exception as e:
                logger.warning(f"Failed to deep scrape related story: {e}")
            finally:
                if rel_page:
                    await rel_page.close()
        
        # 4. External Sources Discovery (Reuters, Bloomberg, etc.)
        external_links = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href^="http"]'));
            return links
                .map(a => ({ title: a.innerText.trim(), url: a.href }))
                .filter(l => !l.url.includes('perplexity.ai') && l.url.length > 20)
                .slice(0, 2); // Limit to top 2 for deep scraping
        }""")
        
        external_sources = []
        for ext in external_links:
            ext_page = None
            try:
                logger.info(f"  -> Deep External Scraping: {ext['url']}")
                ext_page = await context.new_page()
                await ext_page.goto(ext['url'], wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(2)
                
                # Robust paragraph extraction
                ext_content = await ext_page.evaluate("""() => {
                    const article = document.querySelector('article') || document.body;
                    const paras = Array.from(article.querySelectorAll('p'));
                    return paras.map(p => p.innerText.trim()).filter(t => t.length > 30).join('\\n\\n');
                }""")
                
                if ext_content:
                    external_sources.append({
                        "title": ext['title'] or "External Source",
                        "url": ext['url'],
                        "content": clean_noise(ext_content[:4000])
                    })
            except Exception as e:
                logger.warning(f"Failed to scrape external: {ext['url']}")
            finally:
                if ext_page: await ext_page.close()

        return {
            "url": url, 
            "title": title_text, 
            "content": content_text, 
            "date": p_time if p_time != "UNKNOWN_DATE" else date_text,
            "category": category,
            "related_stories": deep_related,
            "external_sources": external_sources
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
