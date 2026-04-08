import pytest
from utils.formatter import format_to_markdown

def test_format_to_markdown_full_data():
    category = 'Tech'
    title = 'AI Breakthrough'
    date = '2026-04-04'
    url = 'https://perplexity.ai/page/ai'
    content = 'This is the main content.'
    external_sources = [{'title': 'Reuters', 'url': 'https://reuters.com'}]
    related_news = [{'title': 'Old Story', 'url': 'https://old.com', 'content': 'Related content.', 'date': '2026-04-03'}]
    
    result = format_to_markdown(category, title, date, url, content, external_sources, related_news)
    
    assert "# 📂 CATEGORÍA: TECH" in result
    assert "## 📰 AI Breakthrough" in result
    assert "> 📅 **Fecha de publicación:** 2026-04-04" in result
    assert "### 📝 RESUMEN DEL REPORTE" in result
    assert "This is the main content." in result
    
    # Check related news block and mandatory disclaimer
    assert "### 🔍 NOTICIAS RELACIONADAS (CONTEXTO PROFUNDO)" in result
    assert "#### 📌 Old Story" in result
    assert "> *\"Esta noticia [Old Story] es noticia auxiliar para la noticia principal [AI Breakthrough], esta noticia es del día [2026-04-03] y por tanto puede tener información desactualizada.\"*" in result
    assert "**URL:** https://old.com" in result
    
    # Check external links
    assert "### 🌐 LINKS EXTERNOS Y FUENTES DE CONTEXTO" in result
    assert "- **Reuters**: https://reuters.com" in result
    
    assert "="*70 in result

def test_format_to_markdown_no_extras():
    result = format_to_markdown('Business', 'Market', 'today', 'https://url.com', 'Content.', [], [])
    
    # No extras should mean these sections are missing
    assert "### 🔍 NOTICIAS RELACIONADAS" not in result
    assert "### 🌐 LINKS EXTERNOS" not in result
