import pytest
from utils.formatter import format_premium_markdown

def test_format_premium_markdown_full_data():
    item = {
        'category': 'Tech',
        'title': 'AI Breakthrough',
        'date': '2026-04-04 10:00:00',
        'url': 'https://www.perplexity.ai/page/ai-breakthrough',
        'content': 'This is the main content.',
        'external_sources': [
            {'title': 'Reuters', 'url': 'https://reuters.com/ai', 'content': 'Reuters content.'}
        ],
        'related_stories': [
            {'title': 'OpenAI Update', 'url': 'https://perplexity.ai/openai', 'content': 'Related content.'}
        ]
    }
    
    result = format_premium_markdown(item)
    
    assert "# 📂 CATEGORÍA: Tech" in result
    assert "## 📰 AI Breakthrough" in result
    assert "> 🕒 **Publicado:** 2026-04-04 10:00:00" in result
    assert "### 📝 Resumen Ejecutivo (Perplexity)" in result
    assert "This is the main content." in result
    assert "#### 📌 FUENTE: Reuters" in result
    assert "Reuters content." in result
    assert "#### 🔗 OpenAI Update" in result
    assert "Related content." in result
    assert "="*68 in result

def test_format_premium_markdown_missing_sources():
    item = {
        'category': 'Business',
        'title': 'Market Surge',
        'date': '1h ago',
        'url': 'https://url.com',
        'content': 'Market is up.',
        'external_sources': [],
        'related_stories': []
    }
    
    result = format_premium_markdown(item)
    
    assert "*No se extrajeron fuentes externas directamente.*" in result
    assert "### 📌 CONTEXTO RELACIONADO" not in result

def test_format_premium_markdown_defaults():
    item = {}
    result = format_premium_markdown(item)
    
    assert "# 📂 CATEGORÍA: Uncategorized" in result
    assert "## 📰 Sin Título" in result
    assert "> 🕒 **Publicado:** Desconocida" in result
    assert "> 🔗 **Perplexity URL:** #" in result
