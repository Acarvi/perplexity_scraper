def format_to_markdown(category, title, date, url, content, external_sources, related_news):
    """
    FORCED IMPLEMENTATION: Strictly uses the user-provided 'format_to_markdown' structure.
    """
    md = f"## 📰 {title}\n"
    md += f"> 📂 **Categoría:** {category} | 🕒 **Publicado:** {date}\n"
    md += f"> 🔗 **Fuente Original:** {url}\n\n"
    md += f"### 📝 Resumen del Artículo\n{content}\n\n"
    
    if external_sources or related_news:
        md += "---\n### 🔍 CONTEXTO Y FUENTES (Deep Scraping)\n\n"
    
    if external_sources:
        for src in external_sources:
            md += f"#### 📌 FUENTE EXTERNA: {src.get('title', 'Link')}\n"
            md += f"**URL:** {src.get('url', '')}\n"
            md += f"> {src.get('content', 'Contenido no disponible.')}\n\n"
            
    if related_news:
        for rel in related_news:
            md += f"#### 📌 NOTICIA RELACIONADA: {rel.get('title', 'Link')}\n"
            md += f"**URL:** {rel.get('url', '')}\n"
            md += f"> {rel.get('content', 'Contenido no disponible.')}\n\n"
        
    md += "====================================================================\n\n"
    return md
