import re
from datetime import datetime, timedelta, timezone

def parse_any_date(date_text):
    """
    Parses both relative (e.g. '14m', '14m ago', 'yesterday') and absolute dates.
    Improved regex for units attached to numbers.
    """
    now = datetime.now(timezone.utc)
    if not date_text: return now
    
    text = date_text.lower().strip()
    
    # 1. Handle Absolute Dates (e.g. 'mar 25, 2026')
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    for i, month in enumerate(months):
        if month in text:
            try:
                if "," in text or len(re.findall(r'\d{4}', text)) > 0:
                    match = re.search(fr'{month}\s+(\d+),?\s+(\d{{4}})', text)
                    if match:
                        day, year = int(match.group(1)), int(match.group(2))
                        return datetime(year, i+1, day, tzinfo=timezone.utc)
                else:
                    match = re.search(fr'{month}\s+(\d+)', text)
                    if match:
                        day = int(match.group(1))
                        return datetime(now.year, i+1, day, tzinfo=timezone.utc)
            except Exception: pass
            break

    # 2. Handle Relative Dates - Improved Regex
    match = re.search(r'(\d+)\s*(m|min|mins|h|hr|d|day|hour|hours|day|days|seg|sec|hora|día)', text)
    if not match:
        if "yesterday" in text or "ayer" in text:
            return now - timedelta(days=1)
        return now
        
    val = int(match.group(1))
    unit = match.group(2)
    
    if unit in ["m", "min", "mins", "minutos"]:
        return now - timedelta(minutes=val)
    if unit in ["h", "hr", "hrs", "hour", "hours", "hora", "horas"]:
        return now - timedelta(hours=val)
    if unit in ["d", "day", "days", "día", "días"]:
        return now - timedelta(days=val)
    if unit in ["seg", "sec", "secs"]:
        return now - timedelta(seconds=val)
        
    return now

def extract_entities(text):
    """
    Extracts skills, companies, and technical keywords from text.
    """
    if not text: return {"skills": [], "companies": [], "keywords": []}
    
    # Basic keyword-based extraction (can be enhanced with NLP)
    keywords = {
        "skills": ["python", "javascript", "react", "playwright", "scraping", "ai", "ml", "automation", "api", "cloud"],
        "companies": ["google", "perplexity", "microsoft", "openai", "meta", "apple", "nvidia", "amazon"],
        "keywords": ["gpu", "cdp", "browser", "stable", "cli", "concurrency", "performance"]
    }
    
    entities = {"skills": [], "companies": [], "keywords": []}
    text_lower = text.lower()
    
    for category, terms in keywords.items():
        for term in terms:
            if re.search(fr'\b{term}\b', text_lower):
                entities[category].append(term)
    
    return entities

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
        r"(?i)Back to Discover\b",
        r"^\s*\+\d+\s*$",
        r"^\s*\d+\s*source(s)?\s*$",
        r"^\s*\d+\s*$",
        r"(?i)Published\n.*"
    ]
    
    cleaned = text
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)
    
    # Remove multiple newlines and extra spaces
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def is_recent_enough(date_text, last_run_time, mode="since_last", custom_hours=24):
    """
    Decides if a story is recent enough based on the selected mode.
    Modes: 'since_last', 'last_24h', 'custom'
    """
    if not date_text or "search" in date_text.lower() or "buscar" in date_text.lower():
        return True, "No date/Search"
        
    pub_time = parse_any_date(date_text)
    now = datetime.now(timezone.utc)
    
    if mode == "since_last":
        target_time = last_run_time
    elif mode == "last_24h":
        target_time = now - timedelta(hours=24)
    elif mode == "custom":
        target_time = now - timedelta(hours=custom_hours)
    else:
        target_time = last_run_time

    # Add a small 5min buffer to avoid missing stories during the scroll
    is_reached = pub_time > (target_time - timedelta(minutes=5))
    return is_reached, pub_time.strftime('%Y-%m-%d %H:%M:%S')
