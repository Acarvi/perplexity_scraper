import pytest
from datetime import datetime, timedelta, timezone
from utils.text_processor import is_recent_enough, parse_any_date

def test_parse_spanish_absolute_dates():
    now = datetime.now(timezone.utc)
    
    # Test '6 abr 2026'
    d = parse_any_date("6 abr 2026")
    assert d.year == 2026
    assert d.month == 4
    assert d.day == 6
    
    # Test 'Publicado el 6 de abril de 2026'
    d = parse_any_date("Publicado el 6 de abril de 2026")
    assert d.year == 2026
    assert d.month == 4
    assert d.day == 6

    # Test '6 mayo' (assuming current year)
    d = parse_any_date("6 mayo")
    assert d.year == now.year
    assert d.month == 5
    assert d.day == 6

def test_parse_detailed_relative_dates():
    now = datetime.now(timezone.utc)
    
    # Test '11 hours ago'
    d = parse_any_date("11 hours ago")
    diff = (now - d).total_seconds()
    assert 10.9 * 3600 < diff < 11.1 * 3600
    
    # Test '2 days ago'
    d = parse_any_date("2 days ago")
    diff = (now - d).total_seconds()
    assert 1.9 * 86400 < diff < 2.1 * 86400

def test_filtering_modes():
    last_run = datetime.now(timezone.utc) - timedelta(hours=5)
    
    # Mode: since_last
    # Recent (2h ago)
    is_ok, _ = is_recent_enough("2 hours ago", last_run, mode="since_last")
    assert is_ok is True
    
    # Old (10h ago)
    is_ok, _ = is_recent_enough("10 hours ago", last_run, mode="since_last")
    assert is_ok is False
