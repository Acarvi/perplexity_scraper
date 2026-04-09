import sys
import os
from datetime import datetime, timezone
sys.path.insert(0, os.path.abspath('.'))
from utils.text_processor import parse_any_date

test_cases = [
    "6 abr 2026",
    "Publicado el 6 de abril de 2026",
    "6 mayo",
    "Publicado\n6 abr 2026",
    "April 4, 2026",
    "14m ago"
]

for tc in test_cases:
    try:
        res = parse_any_date(tc)
        print(f"Input: {tc} -> Output: {res}")
    except Exception as e:
        print(f"Input: {tc} -> Error: {e}")
