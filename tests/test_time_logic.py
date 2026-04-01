import pytest
from datetime import datetime, timedelta, timezone
from utils.text_processor import is_recent_enough, parse_any_date

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
    
    # Mode: last_24h
    # Recent (20h ago)
    is_ok, _ = is_recent_enough("20 hours ago", last_run, mode="last_24h")
    assert is_ok is True
    
    # Old (2 days ago)
    is_ok, _ = is_recent_enough("2 days ago", last_run, mode="last_24h")
    assert is_ok is False
    
    # Mode: custom
    # Within 48h
    is_ok, _ = is_recent_enough("30 hours ago", last_run, mode="custom", custom_hours=48)
    assert is_ok is True
    
    # Outside 48h
    is_ok, _ = is_recent_enough("60 hours ago", last_run, mode="custom", custom_hours=48)
    assert is_ok is False
