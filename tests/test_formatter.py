import pytest
from utils.formatter import generate_premium_markdown

def test_generate_premium_markdown_full_data():
    category = 'Tech'
    title = 'AI Breakthrough'
    date = '2026-04-04'
    url = 'https://perplexity.ai/page/ai'
    content = 'This is the main content.'
    external_sources = [{'title': 'Reuters', 'url': 'https://reuters.com', 'content': 'Source content.'}]
    related_news = [{'title': 'Old Story', 'url': 'https://old.com', 'content': 'Related content.'}]
    
    result = generate_premium_markdown(category, title, date, url, content, external_sources, related_news)
    
    assert "# 📂 CATEGORÍA: TECH" in result
    assert "# 📰 AI Breakthrough" in result
    assert "> 📅 **FECHA DE PUBLICACIÓN:** 2026-04-04" in result
    assert "### 📋 RESUMEN DEL REPORTE" in result
    assert "This is the main content." in result
    assert "#### 📌 FUENTE EXTERNA: Reuters" in result
    assert "#### 📌 NOTICIA RELACIONADA: Old Story" in result
    assert "> **URL:** https://reuters.com" in result
    assert "="*70 in result

def test_generate_premium_markdown_no_extras():
    result = generate_premium_markdown('Business', 'Market', 'today', 'https://url.com', 'Content.', [], [])
    
    assert "### 📚 FUENTES Y MATERIAL DE REFERENCIA" in result
    assert "*No se extrajeron fuentes adicionales para este reporte.*" in result
