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

        # 2. Automation Flow: Upload File
        await asyncio.sleep(8)
        
        # Rename Notebook
        today = datetime.now().strftime("%d/%m/%Y")
        new_name = f"Noticias del día {today}"
        logger.info(f"Renaming notebook to: {new_name}")
        try:
            title_input = page.locator("input.title-input, [aria-label*='title' i], [aria-label*='título' i]").first
            if await title_input.is_visible():
                await title_input.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await title_input.fill(new_name)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)
        except: pass

        # 3. Uploading
        logger.info(f"Uploading file: {file_path}")
        try:
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                await file_input.set_input_files(file_path)
            else:
                add_source_btn = page.get_by_text("Add source", exact=False).or_(page.get_by_text("Añadir fuente", exact=False))
                await add_source_btn.first.click()
                await asyncio.sleep(3)
                upload_btn = page.get_by_text("Upload", exact=False).or_(page.get_by_text("Subir", exact=False))
                async with page.expect_file_chooser() as fc_info:
                    await upload_btn.first.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)
        except Exception as e:
            logger.error(f"Failed during upload: {e}")
            return False
            
        logger.success("File uploaded successfully to NotebookLM.")
        
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
