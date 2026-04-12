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
    
    assert "# [CATEGORY] TECH" in result
    assert "## [NEWS] AI Breakthrough" in result
    assert "> [DATE] **FECHA DE PUBLICACIÓN:** 2026-04-04" in result
    assert "### [SUMMARY] RESUMEN DEL REPORTE" in result
    assert "This is the main content." in result
    
    # Check related news block and mandatory disclaimer
    assert "### [CONTEXT] CONTEXTO Y NOTICIAS RELACIONADAS" in result
    assert "#### [RELATED] Old Story" in result
    assert "> [!] **AVISO DE CONTEXTO:** Esta es una noticia relacionada a la noticia principal **\"AI Breakthrough\"** (del 2026-04-04). Es material de apoyo y puede contener datos desactualizados." in result
    assert "**URL:** https://old.com" in result
    
    # Check external links
    assert "### [SOURCES] FUENTES EXTERNAS Y LINKS DE REFERENCIA" in result
    assert "- **Reuters**: https://reuters.com" in result
    
    assert "="*70 in result

def test_format_to_markdown_no_extras():
    result = format_to_markdown('Business', 'Market', 'today', 'https://url.com', 'Content.', [], [])
    
    # No extras should mean these sections are missing
    assert "### [CONTEXT] CONTEXTO Y NOTICIAS RELACIONADAS" not in result
    assert "### [SOURCES] FUENTES EXTERNAS" not in result
