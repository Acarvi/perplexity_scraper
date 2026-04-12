def format_to_markdown(category, title, date, url, content, external_sources, related_news):
    """
    PREMIUM NEWSLETTER FORMATTER (Phase 3 Refactor)
    Optimized for NotebookLM Ingestion.
    """
    
    # Helper to escape brackets in markdown titles
    def esc(text):
        if not text: return ""
        # Remove any non-ascii characters that might break NotebookLM ingestion if necessary
        # but keep it rich.
        return text.replace("[", "(").replace("]", ")").replace("\n", " ").strip()

    # 1. PRIMARY NEWS BLOCK
    markdown = f"""# [CATEGORY] {esc(category).upper()}
{"="*40}

## [NEWS] {esc(title)}
> [DATE] **FECHA DE PUBLICACIÓN:** {date}  
> [LINK] **ENLACE DIRECTO:** [Abrir en Perplexity]({url})

### [SUMMARY] RESUMEN DEL REPORTE
{content.strip()}

---

"""

    # 2. RELATED NEWS BLOCK (Deep Scraping)
    if related_news:
        markdown += "### [CONTEXT] CONTEXTO Y NOTICIAS RELACIONADAS\n\n"
        for rel in related_news:
            rel_title = esc(rel.get('title', 'Noticia Sin Título'))
            rel_date = rel.get('date', 'Fecha no disponible')
            rel_url = rel.get('url', '')
            rel_content = rel.get('content', 'Contenido no disponible.').strip()
            
            # MANDATORY USER DISCLAIMER
            disclaimer = f"> [!] **AVISO DE CONTEXTO:** Esta es una noticia relacionada a la noticia principal **\"{esc(title)}\"** (del {date}). Es material de apoyo y puede contener datos desactualizados."
            
            markdown += f"#### [RELATED] {rel_title}\n"
            markdown += f"{rel_content}\n"
            markdown += f"{disclaimer}\n"
            markdown += f"**URL:** {rel_url}\n\n"
            markdown += "---\n\n"
    
    # 3. EXTERNAL LINKS BLOCK
    if external_sources:
        markdown += "### [SOURCES] FUENTES EXTERNAS Y LINKS DE REFERENCIA\n\n"
        for src in external_sources:
            src_title = esc(src.get('title', 'Fuente Externa'))
            src_url = src.get('url', '')
            markdown += f"- **{src_title}**: {src_url}\n"
        markdown += "\n"

    markdown += f"\n{'='*70}\n\n"
    return markdown
