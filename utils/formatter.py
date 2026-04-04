def generate_premium_markdown(category, title, date, url, content, external_sources, related_news):
    """
    FORCED IMPLEMENTATION: Strictly uses the user-provided 'generate_premium_markdown' structure.
    Formats external sources and related news into quoting blocks.
    """
    sources_content = ""
    
    if external_sources:
        for src in external_sources:
            sources_content += f"#### 📌 FUENTE EXTERNA: {src.get('title', 'Fuente')}\n"
            sources_content += f"> **URL:** {src.get('url', '')}\n"
            sources_content += f"> {src.get('content', 'Contenido no disponible.')}\n\n"
            
    if related_news:
        for rel in related_news:
            sources_content += f"#### 📌 NOTICIA RELACIONADA: {rel.get('title', 'Noticia')}\n"
            sources_content += f"> **URL:** {rel.get('url', '')}\n"
            sources_content += f"> {rel.get('content', 'Contenido no disponible.')}\n\n"
            
    if not sources_content:
        sources_content = "*No se extrajeron fuentes adicionales para este reporte.*"

    return f"""# 📂 CATEGORÍA: {category.upper()}
---

# 📰 {title}
> 📅 **FECHA DE PUBLICACIÓN:** {date}  
> 🔗 **ENLACE DIRECTO:** [Abrir en Perplexity]({url})

### 📋 RESUMEN DEL REPORTE
{content}

---
### 📚 FUENTES Y MATERIAL DE REFERENCIA
{sources_content}

{"="*70}
"""
