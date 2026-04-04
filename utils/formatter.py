def format_premium_markdown(item):
    """
    Formatea una noticia into the Premium Editorial structure requested.
    item: dict with keys (category, title, date, url, content, external_sources, related_stories)
    """
    category = item.get('category', 'Uncategorized')
    real_title = item.get('title', 'Sin Título')
    parsed_date = item.get('date', 'Desconocida')
    url = item.get('url', '#')
    main_content = item.get('content', '')
    external_sources = item.get('external_sources', [])
    related_stories = item.get('related_stories', [])

    markdown_output = f"""# 📂 CATEGORÍA: {category}
---

## 📰 {real_title}
> 🕒 **Publicado:** {parsed_date}
> 🔗 **Perplexity URL:** {url}

### 📝 Resumen Ejecutivo (Perplexity)
{main_content}

---
### 🔍 PROFUNDIZACIÓN Y FUENTES ORIGINALES
*Esta sección contiene el contexto completo de las fuentes citadas:*
"""

    # Add external sources
    if external_sources:
        for source in external_sources:
            markdown_output += f"""
#### 📌 FUENTE: {source.get('title', 'Fuente Externa')}
**Link:** {source.get('url', '#')}
> {source.get('content', 'Sin contenido extraído.')}
"""
    else:
        markdown_output += "\n*No se extrajeron fuentes externas directamente.*\n"

    # Add Perplexity related stories (optional but good for context)
    if related_stories:
        markdown_output += "\n---\n### 📌 CONTEXTO RELACIONADO (Perplexity)\n"
        for rel in related_stories:
            markdown_output += f"""
#### 🔗 {rel.get('title', 'Noticia Relacionada')}
**URL:** {rel.get('url', '#')}
{rel.get('content', 'Contenido resumido por el sistema.')}
"""

    markdown_output += f"\n{'='*68}\n\n"
    return markdown_output
