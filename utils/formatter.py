def format_to_markdown(category, title, date, url, content, external_sources, related_news):
    """
    PREMIUM NEWSLETTER FORMATTER (Phase 3)
    Hierarchy: # CATEGORY -> ## TITLE -> ### RESUMEN -> ### CONTEXTO (FUENTES)
    Includes mandatory context disclaimers for all secondary sources.
    """
    sources_content = ""
    
    # Disclaimer Template - Updated to exact USER request
    disclaimer = f"> ⚠️ **AVISO DE CONTEXTO:** Esta es una noticia relacionada a la noticia principal **\"{title}\"** (del {date}). Es material de apoyo y puede contener datos desactualizados.\n"

    if external_sources:
        for src in external_sources:
            sources_content += f"#### 📌 FUENTE EXTERNA: {src.get('title', 'Fuente')}\n"
            sources_content += disclaimer
            sources_content += f"**URL:** {src.get('url', '')}\n"
            sources_content += f"> {src.get('content', 'Contenido no disponible.')}\n\n"
            sources_content += "---\n"
            
    if related_news:
        for rel in related_news:
            sources_content += f"#### 📌 NOTICIA RELACIONADA: {rel.get('title', 'Noticia')}\n"
            sources_content += disclaimer
            sources_content += f"**URL:** {rel.get('url', '')}\n"
            sources_content += f"> {rel.get('content', 'Contenido no disponible.')}\n\n"
            sources_content += "---\n"
            
    if not sources_content:
        sources_content = "*No se extrajeron fuentes adicionales para este reporte.*"

    return f"""# 📂 CATEGORÍA: {category.upper()}
{"="*40}

## 📰 {title}
> 📅 **FECHA DE PUBLICACIÓN:** {date}  
> 🔗 **ENLACE DIRECTO:** [Abrir en Perplexity]({url})

### 📝 RESUMEN DEL REPORTE
{content.strip()}

---

### 🔍 CONTEXTO Y FUENTES DE INFORMACIÓN
{sources_content.strip()}

{"="*70}
\n"""
