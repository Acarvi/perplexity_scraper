def generate_premium_markdown(category, real_title, parsed_date, url, main_content, external_sources):
    """
    FORCED IMPLEMENTATION: Strictly uses the user-provided f-string template.
    """
    md = f"""# 📂 CATEGORÍA: {category}
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
    for src in external_sources:
        md += f"""
#### 📌 FUENTE: {src.get('title', 'Fuente Externa')}
**Link:** {src.get('url', '')}
> {src.get('content', '')}
"""
    return md
