import re
from datetime import datetime, timedelta, timezone

def parse_any_date(date_text):
    """
    UNIVERSAL DATE ENGINE (Phase 2)
    Supports:
    - Relative: '14m ago', '2h ago', '1 day ago'
    - Semantic: 'yesterday', 'ayer', 'today', 'hoy'
    - Absolute: 'April 4, 2026', 'Mar 25, 2026', 'Jan 10'
    Returns None if unparseable (contract respected by tests).
    """
    now = datetime.now(timezone.utc)
    if not date_text: return None
    
    text = date_text.lower().strip()
    # Clean noise like 'Published' or line breaks
    text = re.sub(r'(?i)published|[:\n\r]', ' ', text).strip()
    text = re.sub(r'\s+', ' ', text)
    
    # 1. Handle Semantic Dates
    if "yesterday" in text or "ayer" in text:
        return now - timedelta(days=1)
    if "today" in text or "hoy" in text or "just now" in text:
        return now

    # 2. Handle Absolute Dates (e.g. 'April 4, 2026')
    months_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "ene": 1, "abr": 4, "ago": 8, "dic": 12  # Spanish support
    }
    
    # Pattern: Month Day, Year (optional)
    abs_pattern = r'([a-z]{3,10})\s+(\d{1,2}),?\s*(\d{4})?'
    abs_match = re.search(abs_pattern, text, re.I)
    if abs_match:
        m_str = abs_match.group(1).lower()[:3]
        month = months_map.get(m_str)
        if month:
            day = int(abs_match.group(2))
            year = int(abs_match.group(3)) if abs_match.group(3) else now.year
            try:
                return datetime(year, month, day, tzinfo=timezone.utc)
            except: pass

    # 3. Handle Relative Dates - RIGOROUS REGEX
    rel_pattern = r'(\d+)\s*(minute|min|mins|m|hour|hr|hrs|h|day|d|d\xeda)s?\s*ago'
    rel_match = re.search(rel_pattern, text, re.I)
    if not rel_match:
        # Fallback for shorthand units
        rel_match = re.search(r'(\d+)\s*(min|m|hr|h|d|day)s?\b', text, re.I)

    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2).lower()
        if unit in ["m", "min", "mins", "minute"]:
            return now - timedelta(minutes=val)
        if unit in ["h", "hr", "hrs", "hour"]:
            return now - timedelta(hours=val)
        if unit in ["d", "day", "days", "d\xeda"]:
            return now - timedelta(days=val)

    # Unparseable: return None (contract honored by tests)
    return None

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
        r"(?i)Copy\b",
        r"(?i)Share\b",
        r"(?i)Model\b",
        r"(?i)Back to Discover\b",
        r"(?i)View original\b",
        r"(?i)Read more\b",
        r"^\s*\+\d+\s*$",
        r"^\s*\d+\s*source(s)?\s*$",
        r"^\s*\d+\s*$",
        r"(?i)Published\n.*",
        r"(?i)Search for anything\b",
        r"(?i)Explore Discover\b",
        r"(?i)Ask anything\.\.\.\b"
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
    When parse_any_date returns None (unparseable), this function
    applies the STRICT SAFETY NET: reject with 'Unknown' message.
    This means unparseable dates NEVER pass the recency filter.
    """
    if not date_text or "search" in date_text.lower() or "buscar" in date_text.lower():
        return True, "No date/Search"
        
    pub_time = parse_any_date(date_text)
    # STRICT SAFETY NET: None means unparseable -> always reject
    if pub_time is None:
        return False, "Unknown"
        
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
