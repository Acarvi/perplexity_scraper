# Current Sprint: Technical Rescue

## Priorities

1. **Eliminar "Limpieza" Destructiva**
   - [ ] Remove `taskkill` from `core/browser.py`
   - [ ] Ensure `finally` blocks in `scraper.py` and `core/notebooklm.py` handle tab closure.

2. **Parseo Universal de Fechas**
   - [ ] Update `utils/text_processor.py` Regex for Absolute and Relative dates.
   - [ ] Add "Very Old" (year 2000) fallback.

3. **Diseño de Markdown Editorial**
   - [ ] Improve H1/H2 aesthetics in `utils/formatter.py`.
   - [ ] Add mandatory "AVISO DE CONTEXTO" disclaimer.

4. **Fix de NotebookLM (File Chooser)**
   - [ ] Implement `expect_file_chooser()` in `core/notebooklm.py`.
   - [ ] Automate "Customize" and prompt injection.

## Rules of Engagement
- Never touch `main`.
- No `taskkill`.
- Mandatory E2E verification.
