# SCRAPER-002: Remove Destructive Cleanup

**Estado:** BACKLOG
**Descripción:** Eliminar el uso de `taskkill` en `core/browser.py` y asegurar un cierre elegante de tabs y sesiones.
**Criterios de Aceptación (DoD):**
- [ ] Referencias a `taskkill` eliminadas.
- [ ] Bloques `finally` en `scraper.py` y `core/notebooklm.py` cierran las pestañas individualmente.
- [ ] El proceso del navegador finaliza limpiamente sin matar procesos del sistema.
**Archivos Implicados:**
- `core/browser.py`
- `scraper.py`
- `core/notebooklm.py`
