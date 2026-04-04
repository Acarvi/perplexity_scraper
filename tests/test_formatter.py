import pytest
from utils.formatter import generate_premium_markdown

def test_generate_premium_markdown_full_data():
    category = 'Tech'
    real_title = 'AI Breakthrough'
    parsed_date = '2026-04-04 10:00:00'
    url = 'https://www.perplexity.ai/page/ai-breakthrough'
    main_content = 'This is the main content.'
    external_sources = [
        {'title': 'Reuters', 'url': 'https://reuters.com/ai', 'content': 'Reuters content.'}
    ]
    
    result = generate_premium_markdown(
        category, real_title, parsed_date, url, main_content, external_sources
    )
    
    assert "# 📂 CATEGORÍA: Tech" in result
    assert "## 📰 AI Breakthrough" in result
    assert "> 🕒 **Publicado:** 2026-04-04 10:00:00" in result
    assert "### 📝 Resumen Ejecutivo (Perplexity)" in result
    assert "This is the main content." in result
    assert "#### 📌 FUENTE: Reuters" in result
    assert "Reuters content." in result

def test_generate_premium_markdown_missing_sources():
    result = generate_premium_markdown(
        'Business', 'Market Surge', '1h ago', 'https://url.com', 'Market is up.', []
    )
    
    assert "### 🔍 PROFUNDIZACIÓN" in result
    # In the new forced version, it just doesn't add any source blocks if empty.
    assert "#### 📌 FUENTE:" not in result

def test_generate_premium_markdown_defaults():
    result = generate_premium_markdown(
        'Uncategorized', 'Sin Título', 'Desconocida', '#', '', []
    )
    
    assert "# 📂 CATEGORÍA: Uncategorized" in result
    assert "## 📰 Sin Título" in result
    assert "> 🕒 **Publicado:** Desconocida" in result
