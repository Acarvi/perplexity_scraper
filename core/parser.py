import asyncio
import re
import random
from playwright.async_api import TimeoutError as PlaywrightTimeout, Error as PlaywrightError
from utils.text_processor import is_recent_enough, clean_noise

ARTICLE_WAIT = 3
BASE_URL = "https://www.perplexity.ai"

async def extract_date_from_page(page, logger=None):
    """
    Robust date extraction using specific selectors and scoped brute-force.
    """
    try:
        # 1. Try specific semantic selectors first
        date_selectors = [
            'time', 
            'span.truncate', 
            '[class*="date"]', 
            '[class*="published"]',
            'div.flex.items-center.gap-x-2 span'
        ]
        
        for selector in date_selectors:
            elements = await page.locator(selector).all()
            for el in elements:
                text = await el.inner_text()
                if any(re.search(p, text, re.I) for p in [r'\d+\s*(m|h|d|min|hour|day|ago)', r'\d{4}']):
                    # Check if it's not a stock widget (usually stock widgets have currency or % near)
                    parent_text = await el.evaluate("el => el.parentElement.innerText")
                    if "$" not in parent_text and "%" not in parent_text:
                        return text.strip()

        # 2. Targeted brute force: first 5000 chars of innerText
        raw_body_text = await page.evaluate("() => document.body.innerText.substring(0, 5000)")
        patterns = [
            r'Published\s*\n\s*(\d+)\s*(minute|min|mins|hour|hr|hrs|day|d)s?\s*ago',
            r'Publicado\s*\n\s*(\d+)\s*abr',
            r'Publicado\s*el\s*(\d+.*202\d)',
            r'(\d+)\s*(minute|min|mins|hour|hr|hrs|day|d)s?\s*ago',
            r'(\d+)(min|h|d|m|hr)s?\s*ago'
        ]
        
        for p in patterns:
            match = re.search(p, raw_body_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # 3. Absolute date fallback
        abs_date_match = re.search(r'\d{1,2}\s+(?:de\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|ene|abr|ago|dic|[a-z]{4,10})\s+(?:de\s+)?202\d', raw_body_text, re.I)
        if abs_date_match:
            return abs_date_match.group(0)
            
    except Exception as e:
        if logger: logger.error(f"Error in extract_date_from_page: {e}")
    return "Unknown"

async def scrape_article(context, page, url, last_run_time, mode, custom_hours, logger, semaphore, category="Uncategorized"):
    # Human-like delay before deep scraping
    await asyncio.sleep(random.uniform(1.5, 3.5))
    logger.info(f"Deep Scraping [{category}]: {url}")
    try:
        try:
            # Randomize referer or extra headers could be added here too
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(ARTICLE_WAIT + random.uniform(0.5, 1.5))
        except (PlaywrightTimeout, PlaywrightError) as e:
            logger.warning(f"Warning: Página omitida por timeout (Main): {url}")
            return None
        
        # 1. TÍTULO REAL
        # 1. TÍTULO REAL (Improved Selectors)
        try:
            # Prioritize semantic headers or large text near the top
            title_selectors = [
                 "h1", 
                 "h1.prose-h1", 
                 'div[data-testid="article-title"]',
                 '[class*="title"] h1',
                 '.prose h1'
            ]
            real_title = None
            for selector in title_selectors:
                el = page.locator(selector).first
                if await el.count() > 0:
                    text = await el.inner_text(timeout=2000)
                    if text and len(text.strip()) > 5:
                        real_title = text.strip()
                        break
            
            if not real_title:
                raw_title = await page.title()
                real_title = raw_title.replace(" - Perplexity", "").replace("Perplexity", "").strip()
                if not real_title: real_title = "Noticia Sin Título"
        except:
            real_title = "Noticia Sin Título"
        
        # 2. FECHA REAL (Main Article)
        date_text = await extract_date_from_page(page, logger)
        is_ok, p_time = is_recent_enough(date_text, last_run_time, mode=mode, custom_hours=custom_hours)
        
        logger.info(f"   [TIME-DEBUG] Texto encontrado: \"{date_text}\"")
        logger.info(f"   [TIME-DEBUG] Parsed como: {p_time}")
        
        # LOGGING Y CORTE OBLIGATORIO (Main Article Only)
        if not is_ok:
            if p_time == "Unknown" or date_text == "Unknown":
                logger.error(f"FAILURE: Could not extract date (Unknown). Strict Cutoff Triggered.")
                return "TOO_OLD"
            else:
                logger.warning(f"   [FILTRO] [X] Noticia fuera de rango ({p_time}). Deteniendo categoría.")
                return "TOO_OLD"
        
        logger.info(f"   [FILTRO] [OK] Dentro de rango. Procediendo al Deep Scraping...")

        # 3. CONTENT SCRAPING (Enhanced for Logos/Icons)
        content_loc = page.locator('.prose, [dir="auto"], article, main').first
        if await content_loc.count() > 0:
            content_text = await page.evaluate("""(selector) => {
                const el = document.querySelector(selector);
                if (!el) return "";
                
                // Function to process nodes and preserve alt text for icons/logos
                const processNode = (node) => {
                    if (node.nodeType === Node.TEXT_NODE) {
                        return node.textContent;
                    }
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Skip hidden elements
                        const style = window.getComputedStyle(node);
                        if (style.display === 'none' || style.visibility === 'hidden') return "";

                        // Handle images/icons that might be logos/names
                        if (node.tagName === 'IMG' || node.tagName === 'SVG') {
                            const alt = node.getAttribute('alt') || node.getAttribute('aria-label');
                            return alt ? ` ${alt} ` : "";
                        }
                        
                        let text = "";
                        for (const child of node.childNodes) {
                            text += processNode(child);
                        }
                        
                        // Preserve some structure
                        if (['P', 'DIV', 'H1', 'H2', 'H3', 'LI'].includes(node.tagName)) {
                            text += "\\n";
                        }
                        return text;
                    }
                    return "";
                };
                return processNode(el).replace(/\\n\\s*\\n/g, '\\n\\n');
            }""", '.prose, [dir="auto"], article, main')
        else:
            content_text = await page.evaluate("() => document.body.innerText")
            
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
        for rel in related_links[:3]:
            rel_page = None
            try:
                logger.info(f"  -> Deep Related Scraping: {rel['title']}")
                rel_page = await context.new_page()
                async with semaphore:
                    try:
                        await rel_page.goto(rel['url'], wait_until="domcontentloaded", timeout=30000)
                        await asyncio.sleep(2)
                    except (PlaywrightTimeout, PlaywrightError):
                        logger.warning(f"Warning: Página omitida por timeout (Related): {rel['url']}")
                        continue
                
                # Extract related date without blocking if too old
                rel_date_text = await extract_date_from_page(rel_page, logger)
                _, rel_p_time = is_recent_enough(rel_date_text, last_run_time, mode=mode, custom_hours=custom_hours)
                
                rel_content_loc = rel_page.locator('.prose, [dir="auto"], article, main').first
                rel_text = await (rel_content_loc.inner_text() if await rel_content_loc.count() > 0 else "No content.")
                rel_text = clean_noise(rel_text)
                
                deep_related.append({
                    "title": rel['title'], 
                    "url": rel['url'], 
                    "content": rel_text.strip(),
                    "date": rel_p_time if rel_p_time != "Unknown" else rel_date_text
                })
            except Exception as e:
                logger.warning(f"  [WARN] Skip related story: {str(e)[:50]}...")
            finally:
                if rel_page:
                    try:
                        await rel_page.close()
                    except: pass
        
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
                async with semaphore:
                    try:
                        await ext_page.goto(ext['url'], wait_until="domcontentloaded", timeout=25000)
                        await asyncio.sleep(2)
                    except (PlaywrightTimeout, PlaywrightError):
                        logger.warning(f"Warning: Página omitida por timeout (External): {ext['url']}")
                        continue
                
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
                logger.warning(f"  [WARN] Skip external: {str(e)[:50]}...")
            finally:
                if ext_page: 
                    try:
                        await ext_page.close()
                    except: pass

        return {
            "url": url, 
            "title": real_title, 
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
        
        await page.evaluate("window.scrollBy(0, 2000)") 
        await asyncio.sleep(2 + random.uniform(0.1, 1.0))
        
        try:
            current_timestamp = await page.evaluate("""() => {
                const elements = Array.from(document.querySelectorAll('span, time, div'));
                const timePattern = /\\d+\\s*(m|h|d|min|hour|day|seg|sec|hora|día)|yesterday|ayer|ago|hace/i;
                const matches = elements.filter(el => timePattern.test(el.innerText));
                return matches.length > 0 ? matches[matches.length - 1].innerText.trim() : null;
            }""")
        except:
            logger.warning("  [WARN] Lost context during scroll. Attempting recovery...")
            break 
        
        if current_timestamp:
            if current_timestamp == last_timestamp:
                stuck_count += 1
                if stuck_count >= 5: break
            else:
                stuck_count = 0
                last_timestamp = current_timestamp
                
            is_rec, t_str = is_recent_enough(current_timestamp, last_run_time, mode=mode, custom_hours=custom_hours)
            if not is_rec:
                if t_str == "Unknown":
                    logger.warning(f"  [WARN] Unparseable date in feed ({current_timestamp}). Skipping element...")
                else:
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
