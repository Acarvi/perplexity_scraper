# SCRAPER-001: Fix Markdown Formatting

**Estado:** IN_PROGRESS
**Solución Técnica Propuesta:**
1. **Extracción de Contenido:** Reemplazar `.inner_text()` por un script `page.evaluate` personalizado que:
   - Capture el `textContent` pero filtre elementos ocultos.
   - Detecte elementos de imagen/logo y extraiga su atributo `alt` o `aria-label` para evitar palabras faltantes (p. ej. nombres de fuentes como 'Reuters').
2. **Parser de Fechas:** 
   - Limitar el rango de búsqueda inicial a los primeros 2000 caracteres del `body` o buscar específicamente elementos `<time>` y `span` con patrones de fecha.
   - Implementar un sistema de pesos: si se encuentra una fecha cerca de un elemento "Published", tiene prioridad sobre la de un widget de bolsa.
3. **Limpieza de Ruido:** 
   - Modificar las regex de `clean_noise` para que sean "Markdown-aware".
   - Evitar `re.MULTILINE` en patrones que no lo necesiten para no romper la estructura de las líneas.
   - Normalizar los saltos de línea al final del proceso de limpieza, no entre patrones.
4. **Links Externos:** Escapar caracteres especiales en los títulos de los links para evitar que rompan la sintaxis Markdown `[título](url)`.

**Criterios de Aceptación (DoD):**
- [ ] No existen saltos de línea (`\n`) inyectados en medio de negritas o elementos de lista.
- [ ] El formato de links externos es válido y funcional.
- [ ] El parser de fechas no se bloquea con widgets de bolsa (evitar "Strict Cutoff").
- [ ] El archivo se importa correctamente en NotebookLM.

**Archivos Implicados:**
- `utils/text_processor.py`
- `core/parser.py`
- `utils/formatter.py`
