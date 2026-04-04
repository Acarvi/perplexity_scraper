import asyncio
from datetime import datetime
import os

async def upload_to_notebooklm(context, file_path, logger):
    """
    FORCED IMPLEMENTATION: Strictly follows the user's 'upload_to_notebooklm' redesign.
    """
    logger.info("Starting Flexible NotebookLM Automation (Redesign)...")
    
    page = await context.new_page()
    try:
        await page.goto("https://notebooklm.google.com/")
        await page.wait_for_load_state("networkidle")
        
        print("Buscando botón de Nuevo Cuaderno en NotebookLM...")
        # 1. Intentar encontrar el botón con múltiples estrategias (Inglés, Español, o Iconos SVG)
        btn_crear = page.locator('button:has-text("New"), button:has-text("Nuevo"), [aria-label*="New notebook" i], [aria-label*="Nuevo cuaderno" i]').first
        
        try:
            await btn_crear.wait_for(state="visible", timeout=8000)
            await btn_crear.click()
            print("✅ Cuaderno creado. Procediendo a subir archivo...")
        except:
            print("❌ No se pudo localizar el botón mediante texto/aria-label.")
            # Fallback: Click en coordenadas o intentar forzar un click en el primer div clickeable en la parte superior izquierda
            try:
                print("Intentando selector alternativo (clase genérica)...")
                await page.locator('div[role="button"]').nth(1).click() 
            except Exception as e:
                print(f"⚠️ Fallo total en la UI de NotebookLM: {e}")
                
                # Check for session issue before giving up
                print("\n" + "="*50)
                print("🔑 SESIÓN NO DETECTADA O UI DESCONOCIDA.")
                print("Abriendo ventana para inicio de sesión manual...")
                print("="*50 + "\n")
                
                os.system(r'cmd /c start "" "C:\Users\Acarvi\Desktop\Comet.lnk" "https://notebooklm.google.com/"')
                input(">>> PRESIONA ENTER AQUÍ UNA VEZ HAYAS INICIADO SESIÓN PARA CONTINUAR... <<<")
                
                await page.reload()
                await page.wait_for_load_state("networkidle")
                btn_crear = page.locator('button:has-text("New"), button:has-text("Nuevo"), [aria-label*="New notebook" i], [aria-label*="Nuevo cuaderno" i]').first
                await btn_crear.wait_for(state="visible", timeout=15000)
                await btn_crear.click()

        # 2. Automation Flow: Handle 'Add Source' Modal and Upload First
        logger.info("Detectando modal de 'Añadir fuente' en NotebookLM...")
        try:
            # Esperar a que el modal de añadir fuente aparezca o que el input de archivo esté disponible
            # Google suelo abrirlo automáticamente al crear un cuaderno vacío
            modal_locator = page.locator("mat-dialog-container, div[role='dialog']").first
            await modal_locator.wait_for(state="visible", timeout=15000)
            logger.info("Modal detectado. Procediendo a la carga de archivo.")
        except:
            logger.warning("No se detectó modal automático. Continuando con búsqueda manual de input.")

        # Subida Inmediata mediante el input oculto
        logger.info(f"Subiendo archivo: {file_path}")
        try:
            # Encontrar el input de tipo archivo que está dentro del modal o de la página
            file_input = page.locator("input[type='file']").first
            await file_input.set_input_files(file_path)
            
            # Esperar a que el procesamiento termine (el texto 'Cargando' o similar desaparezca)
            logger.info("Esperando a que finalice la carga y el procesamiento del archivo...")
            await asyncio.sleep(10) # Pausa de seguridad para el OCR/Procesamiento inicial
            
            # Si hay un botón de cerrar modal o similar, intentar pulsarlo o esperar a que se cierre solo al terminar la carga
            # Generalmente, al subir el primer archivo, el modal puede ofrecer 'Add more' o simplemente quedarse ahí.
            # Intentamos pulsar fuera o en el botón de cerrar si existe.
            try:
                close_btn = page.locator("button[aria-label*='close' i], button[aria-label*='cerrar' i]").first
                if await close_btn.is_visible():
                    await close_btn.click()
            except: pass
            
        except Exception as e:
            logger.error(f"Error durante la subida al modal: {e}")
            return False
            
        logger.success("Archivo subido y modal gestionado.")

        # 3. Rename Notebook (Solo DESPUÉS de cerrar el modal de carga)
        today = datetime.now().strftime("%d/%m/%Y")
        new_name = f"Noticias del día {today}"
        logger.info(f"Cambiando nombre del cuaderno a: {new_name}")
        try:
            # El título suele estar arriba a la izquierda
            title_input = page.locator("input.title-input, [aria-label*='title' i], [aria-label*='título' i], button:has-text('Untitled'), button:has-text('Cuaderno sin título')").first
            await title_input.wait_for(state="visible", timeout=10000)
            await title_input.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await title_input.fill(new_name)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"No se pudo renombrar el cuaderno (UI bloqueada?): {e}")
        
        # 4. Prompt Injection (Audio Overview)
        try:
            logger.info("Initializing Audio Overview Customization...")
            await asyncio.sleep(20) 
            
            customize_btn = page.locator("button:has-text('Personalizar'), button:has-text('Customize'), button:has(mat-icon:has-text('chevron_forward'))").first
            if await customize_btn.is_visible():
                await customize_btn.click()
                await asyncio.sleep(3)
                
                prompt_textarea = page.locator("textarea[aria-label*='focus' i], textarea[aria-label*='centrarse' i], mat-dialog-content textarea").first
                if await prompt_textarea.is_visible():
                    podcast_prompt = "Generate a professional, long-form podcast in English. Focus on the connection between the main news and its sources."
                    await prompt_textarea.fill(podcast_prompt)
                    await asyncio.sleep(1)
                    
                    gen_btn = page.locator("button:has-text('Generar'), button:has-text('Generate')").first
                    if await gen_btn.is_visible():
                        await gen_btn.click()
                        logger.success("Audio Overview generation started with custom prompt.")
        except: pass

        return True
        
    except Exception as e:
        logger.error(f"NotebookLM Automation Error: {e}")
        return False
    finally:
        # Keep tab open briefly for confirm
        await asyncio.sleep(5)
