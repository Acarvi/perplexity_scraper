# Workflow Skill: Gold Rules

## REGLAS DE ORO

1. **PROHIBIDO TOCAR main**: Nunca realices cambios directamente en la rama `main`. Crea siempre una rama de característica (ej. `feature-fix-all`). Antes de terminar, verifica que has borrado las ramas antiguas (`git branch -D`).
2. **PROHIBIDO EL COMPORTAMIENTO DESTRUCTIVO**: No utilices `taskkill`, `os.system("taskkill")` ni comandos similares. El usuario usa Comet para sus asuntos personales. Solo puedes cerrar las ventanas de Playwright mediante `await browser.close()`.
3. **TESTEO E2E OBLIGATORIO**: No basta con pasar pytest. Debes ejecutar `python scraper.py` y verificar manualmente el archivo `.md` de salida y el flujo visual en NotebookLM.
