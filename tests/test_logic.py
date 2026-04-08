import pytest
from datetime import datetime, timedelta, timezone
from utils.text_processor import parse_any_date, clean_noise, is_recent_enough

def test_parse_relative_dates():
    now = datetime.now(timezone.utc)
    
    # Test minutes
    d = parse_any_date("14m ago")
    assert d is not None
    diff = (now - d).total_seconds()
    assert 13.5 * 60 < diff < 14.5 * 60
    
    # Test hours
    d = parse_any_date("2 hours ago")
    assert d is not None
    diff = (now - d).total_seconds()
    assert 1.9 * 3600 < diff < 2.1 * 3600
    
    # Test days
    d = parse_any_date("3 days ago")
    assert d is not None
    diff = (now - d).total_seconds()
    assert 2.9 * 86400 < diff < 3.1 * 86400

    # Test yesterday
    d = parse_any_date("yesterday")
    assert d is not None
    diff = (now - d).total_seconds()
    assert 23 * 3600 < diff < 25 * 3600

def test_parse_absolute_dates():
    # Test with year
    d = parse_any_date("Mar 25, 2026")
    assert d is not None
    assert d.year == 2026
    assert d.month == 3
    assert d.day == 25
    
    # Test with FULL month name
    d = parse_any_date("April 4, 2026")
    assert d is not None
    assert d.year == 2026
    assert d.month == 4
    assert d.day == 4
    
    # Test without year (assume current year)
    now = datetime.now(timezone.utc)
    d = parse_any_date("Jan 10")
    assert d is not None
    assert d.year == now.year
    assert d.month == 1
    assert d.day == 10

def test_parse_unknown():
    # Should return None for garbage
    d = parse_any_date("Some garbage text")
    assert d is None

def test_clean_noise():
    text = """
    Sources
    Ask follow-up
    14 sources
    Related stories
    This is the real content.
    View more
    Share
    Model
    Back to Discover
    +123
    """
    cleaned = clean_noise(text)
    assert "Sources" not in cleaned
    assert "Ask follow-up" not in cleaned
    assert "This is the real content." in cleaned
    assert "View more" not in cleaned
    assert "+123" not in cleaned

def test_is_recent_enough():
    last_run = datetime.now(timezone.utc) - timedelta(hours=1)
    
    # Recent
    is_ok, _ = is_recent_enough("10m ago", last_run)
    assert is_ok is True
    
    # Old
    is_ok, _ = is_recent_enough("2 hours ago", last_run)
    assert is_ok is False
    
    # Unknown (Strict Abort)
    is_ok, msg = is_recent_enough("Unknown date text", last_run)
    assert is_ok is False
    assert msg == "Unknown"

def test_premium_newsletter_output():
    from utils.formatter import format_to_markdown
    category = 'Tech'
    title = 'Test Story'
    date = 'Recent'
    url = 'https://test.com'
    content = 'Main text.'
    external_sources = [{'title': 'Ref', 'url': 'https://ref.com'}]
    related_news = [{'title': 'Rel Story', 'url': 'https://rel.com', 'content': 'Rel content.', 'date': 'Today'}]
    
    result = format_to_markdown(category, title, date, url, content, external_sources, related_news)
    
    assert "ESTA NOTICIA [REL STORY] ES NOTICIA AUXILIAR PARA LA NOTICIA PRINCIPAL [TEST STORY]" in result.upper()
    assert "### 🌐 LINKS EXTERNOS Y FUENTES DE CONTEXTO" in result
    assert "Recent" in result
