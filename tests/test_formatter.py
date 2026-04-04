import pytest
from utils.formatter import format_to_markdown

def test_format_to_markdown_full_data():
    category = 'Tech'
    title = 'AI Breakthrough'
    date = '2026-04-04'
    url = 'https://perplexity.ai/page/ai'
    content = 'This is the main content.'
    external_sources = [{'title': 'Reuters', 'url': 'https://reuters.com', 'content': 'Source content.'}]
    related_news = [{'title': 'Old Story', 'url': 'https://old.com', 'content': 'Related content.'}]
    
    result = format_to_markdown(category, title, date, url, content, external_sources, related_news)
    
    assert "## 📰 AI Breakthrough" in result
    assert "> 📂 **Categoría:** Tech" in result
    assert "🕒 **Publicado:** 2026-04-04" in result
    assert "### 📝 Resumen del Artículo" in result
    assert "This is the main content." in result
    assert "#### 📌 FUENTE EXTERNA: Reuters" in result
    assert "#### 📌 NOTICIA RELACIONADA: Old Story" in result
    assert "="*40 in result

def test_format_to_markdown_no_extras():
    result = format_to_markdown('Business', 'Market', 'today', 'https://url.com', 'Content.', [], [])
    
    assert "### 🔍 CONTEXTO Y FUENTES" not in result
    assert "FUENTE EXTERNA" not in result
    assert "NOTICIA RELACIONADA" not in result
