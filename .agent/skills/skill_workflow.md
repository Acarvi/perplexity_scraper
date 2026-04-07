# Workflow Skill: Gold Rules

## REGLAS DE ORO

1. **PROHIBIDO TOCAR main**: Nunca realices cambios directamente en la rama `main`. Crea siempre una rama de característica (ej. `feature-fix-all`). Antes de terminar, verifica que has borrado las ramas antiguas (`git branch -D`).
2. **PROHIBIDO EL COMPORTAMIENTO DESTRUCTIVO**: No utilices `taskkill`, `os.system("taskkill")` ni comandos similares. El usuario usa Comet para sus asuntos personales. Solo puedes cerrar las ventanas de Playwright mediante `await browser.close()`.
3. **TESTEO E2E OBLIGATORIO**: No basta con pasar pytest. Debes ejecutar `python scraper.py` y verificar manualmente el archivo `.md` de salida y el flujo visual en NotebookLM.
4. **PUSH OBLIGATORIO EN RAMA AL FINALIZAR**: Siempre, al terminar la implementación y validar que los tests (incluido el E2E) pasan, el agente DEBE hacer commit y un `git push origin HEAD` (o el nombre de la rama actual). Está terminantemente prohibido hacer push o merge a `main` directamente, siempre se hará push a la rama de la feature en la que se está trabajando.
