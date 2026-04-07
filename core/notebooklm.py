import asyncio
import os
from datetime import datetime

async def upload_to_notebooklm(context, file_path, logger):
    """
    NotebookLM Automation (Phase 4)
    Handles: Notebook creation, robust file upload via expect_file_chooser, and custom podcast generation.
    """
    page = await context.new_page()
    try:
        logger.info("Accediendo a NotebookLM...")
        await page.goto("https://notebooklm.google.com/", wait_until="networkidle", timeout=60000)
        
        # 1. Crear Nuevo Cuaderno
        # Buscamos el botón de 'Nuevo cuaderno' o el '+' grande
        try:
            new_btn = page.locator('button:has-text("Nuevo cuaderno"), button:has-text("New notebook"), .v-btn--icon').first
            await new_btn.wait_for(state="visible", timeout=30000)
            await new_btn.click()
            logger.info("Creando nuevo cuaderno...")
        except Exception as e:
            logger.warning(f"No se detectó el botón de 'Nuevo cuaderno': {e}")
            # Si ya estamos en un cuaderno o no carga, procedemos
        
        await asyncio.sleep(5)
        
        # 2. Subir Archivo (Rigor Extra - Interceptor de Playwright)
        logger.info("Detectando modal de 'Añadir fuente' en NotebookLM...")
        try:
            # Primero click en el botón general de 'Añadir fuente' si el modal no está abierto
            add_source_btn = page.locator('button:has-text("Añadir fuente"), button:has-text("Add source"), .v-btn--icon').first
            if await add_source_btn.is_visible():
                await add_source_btn.click()
                await asyncio.sleep(2)

            async with page.expect_file_chooser() as fc_info:
                # Interceptamos el diálogo al hacer clic en la opción 'Archivo' o 'File'
                file_option = page.locator('*:has-text("Archivo"), *:has-text("File"), [aria-label*="File" i]').first
                await file_option.wait_for(state="visible", timeout=15000)
                await file_option.click()
            
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_path)
            logger.success(f"Archivo {os.path.basename(file_path)} subido exitosamente.")
        except Exception as e:
            logger.error(f"Error interceptando selector de archivos: {e}")
            # Fallback directo al input oculto si es posible
            try:
                await page.set_input_files('input[type="file"]', file_path)
                logger.success("Subida completada via fallback (input).")
            except:
                logger.error("Fallo total en la subida de archivo.")
                return False

        await asyncio.sleep(10) # Esperar al procesamiento inicial

        # 3. Cambiar nombre del cuaderno (Opcional pero ordenado)
        try:
            name_label = page.locator('input[aria-label="Notebook name"], input[aria-label="Nombre del cuaderno"]').first
            if await name_label.is_visible():
                timestamp = datetime.now().strftime("%d/%m/%Y")
                await name_label.click()
                await name_label.fill(f"Perplexity Discover {timestamp}")
                await page.keyboard.press("Enter")
                logger.info(f"Nombre del cuaderno actualizado.")
        except: pass

        # 4. Prompt Injection & Podcast Generation (Rigor Extra)
        try:
            logger.info("Iniciando personalización de Audio Overview...")
            # NotebookLM llama a esto 'Guía del cuaderno' o 'Resumen de audio'
            audio_panel_btn = page.locator("button:has-text('Audio Overview'), button:has-text('Resumen de audio'), button:has-text('Guía del cuaderno')").first
            await audio_panel_btn.wait_for(state="visible", timeout=30000)
            await audio_panel_btn.click()
            await asyncio.sleep(5)
            
            # Buscar botón de Personalizar/Customize
            customize_btn = page.locator("button:has-text('Personalizar'), button:has-text('Customize'), [aria-label*='Customize' i]").first
            await customize_btn.wait_for(state="visible", timeout=10000)
            await customize_btn.click()
            await asyncio.sleep(3)
                
            prompt_textarea = page.locator("textarea[aria-label*='focus' i], textarea[aria-label*='centrarse' i], mat-dialog-content textarea").first
            if await prompt_textarea.is_visible():
                podcast_prompt = "Generate a professional, long-form podcast in English summarizing these news. Focus on the analysis of the main stories."
                await prompt_textarea.fill(podcast_prompt)
                await asyncio.sleep(1)
                
                gen_btn = page.locator("button:has-text('Generar'), button:has-text('Generate')").first
                if await gen_btn.is_visible():
                    await gen_btn.click()
                    logger.success("Generación de Podcast iniciada con prompt personalizado.")
                    return True
            
            # Fallback: Generar sin prompt si el textarea no apareció
            direct_gen = page.locator("button:has-text('Generar'), button:has-text('Generate')").first
            if await direct_gen.is_visible():
                await direct_gen.click()
                logger.success("Generación de Podcast iniciada (Sin personalización).")
                return True
                
        except Exception as e:
            logger.warning(f"No se pudo completar la automatización del Podcast: {e}")
            return True # Retornamos True porque la subida fue exitosa

    except Exception as e:
        logger.error(f"Error en la automatización de NotebookLM: {e}")
        return False
    finally:
        # No cerramos la página para que el usuario pueda ver el progreso si lo desea
        # Pero en producción real preferiríamos page.close() tras confirmar la barra de progreso
        pass
