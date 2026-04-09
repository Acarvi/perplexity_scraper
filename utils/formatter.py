def format_to_markdown(category, title, date, url, content, external_sources, related_news):
    """
    PREMIUM NEWSLETTER FORMATTER (Phase 3 Refactor)
    Structure:
    1. Primary News Block (Title, Link, Content, Date)
    2. Related News Block (Mandatory Disclaimer, Content)
    3. External Links Block (URLs only)
    """
    
    # 1. PRIMARY NEWS BLOCK
    markdown = f"""# 📂 CATEGORÍA: {category.upper()}
{"="*40}

## 📰 {title}
> 📅 **Fecha de publicación:** {date}  
> 🔗 **Enlace directo:** [Abrir en Perplexity]({url})

### 📝 RESUMEN DEL REPORTE
{content.strip()}

---

"""

    # 2. RELATED NEWS BLOCK (Deep Scraping)
    if related_news:
        markdown += "### 🔍 NOTICIAS RELACIONADAS (CONTEXTO PROFUNDO)\n\n"
        for rel in related_news:
            rel_title = rel.get('title', 'Noticia Sin Título')
            rel_date = rel.get('date', 'Fecha no disponible')
            rel_url = rel.get('url', '')
            rel_content = rel.get('content', 'Contenido no disponible.').strip()
            
            # MANDATORY USER DISCLAIMER
            disclaimer = f"> *\"Esta noticia [{rel_title}] es noticia auxiliar para la noticia principal [{title}], esta noticia es del día [{rel_date}] y por tanto puede tener información desactualizada.\"*"
            
            markdown += f"#### 📌 {rel_title}\n"
            markdown += f"{disclaimer}\n\n"
            markdown += f"**URL:** {rel_url}\n\n"
            markdown += f"{rel_content}\n\n"
            markdown += "---\n\n"
    
    # 3. EXTERNAL LINKS BLOCK
    if external_sources:
        markdown += "### 🌐 LINKS EXTERNOS Y FUENTES DE CONTEXTO\n\n"
        for src in external_sources:
            src_title = src.get('title', 'Fuente Externa')
            src_url = src.get('url', '')
            markdown += f"- **{src_title}**: {src_url}\n"
        markdown += "\n"

    markdown += f"\n{'='*70}\n\n"
    return markdown
