import asyncio
from datetime import datetime
import os

async def automate_notebooklm_upload(context, file_path, logger):
    """
    FORCED IMPLEMENTATION: Strictly follows the user's 'upload_to_notebooklm' structure.
    """
    logger.info("Starting Forced NotebookLM Automation (Step 2)...")
    
    page = await context.new_page()
    try:
        await page.goto("https://notebooklm.google.com/")
        await page.wait_for_load_state("networkidle")
        
        # Comprobar si existe el botón de nuevo cuaderno
        btn_crear = page.locator('button:has-text("New notebook"), button:has-text("Nuevo cuaderno"), div[role="button"]:has(svg)').first
        
        try:
            await btn_crear.wait_for(state="visible", timeout=10000)
        except:
            print("\n" + "="*50)
            print("🔑 SESIÓN NO DETECTADA EN NOTEBOOKLM.")
            print("Abriendo ventana para inicio de sesión manual...")
            print("="*50 + "\n")
            
            # Abrir Comet con el comando mágico
            os.system(r'cmd /c start "" "C:\Users\Acarvi\Desktop\Comet.lnk" "https://notebooklm.google.com/"')
            
            # PAUSA OBLIGATORIA DEL SCRIPT HASTA QUE EL USUARIO HAYA HECHO LOGIN
            input(">>> PRESIONA ENTER AQUÍ UNA VEZ HAYAS INICIADO SESIÓN PARA CONTINUAR... <<<")
            
            await page.reload()
            await page.wait_for_load_state("networkidle")
            await btn_crear.wait_for(state="visible", timeout=15000)
            
        # Continuar con la creación del cuaderno...
        logger.info("✅ Sesión detectada. Creando cuaderno...")
        
        # [Lógica para crear cuaderno y subir el archivo .md]
        await btn_crear.click()
        await asyncio.sleep(5)
        
        # Rename
        today = datetime.now().strftime("%d/%m/%Y")
        new_name = f"Noticias del día {today}"
        logger.info(f"Renaming notebook to: {new_name}")
        try:
            title_input = page.locator("input.title-input").first
            if await title_input.is_visible():
                await title_input.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await title_input.fill(new_name)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)
        except: pass

        # Upload
        logger.info(f"Uploading file: {file_path}")
        try:
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                await file_input.set_input_files(file_path)
            else:
                add_source_btn = page.get_by_text("Add source", exact=False).or_(page.get_by_text("Añadir fuente", exact=False))
                await add_source_btn.first.click()
                await asyncio.sleep(2)
                upload_btn = page.get_by_text("Upload", exact=False).or_(page.get_by_text("Subir", exact=False))
                async with page.expect_file_chooser() as fc_info:
                    await upload_btn.first.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)
        except Exception as e:
            logger.error(f"Failed during upload: {e}")
            return False
            
        logger.success("File uploaded successfully to NotebookLM.")
        
        # Audio Overview Customization
        try:
            logger.info("Initializing Audio Overview Customization...")
            await asyncio.sleep(15) 
            
            customize_btn = page.locator("button:has(mat-icon:has-text('chevron_forward')), button:has-text('Personalizar'), button:has-text('Customize')").first
            if await customize_btn.is_visible():
                logger.info("Clicking 'Customize' for Audio Overview...")
                await customize_btn.click()
                await asyncio.sleep(3)
                
                prompt_textarea = page.locator("mat-dialog-content textarea, textarea[aria-label*='focus'], textarea[aria-label*='centrarse']").first
                if await prompt_textarea.is_visible():
                    podcast_prompt = "Generate a professional, long-form podcast in English. Focus on the connection between the main news and its sources."
                    logger.info(f"Injecting podcast prompt: {podcast_prompt}")
                    await prompt_textarea.fill(podcast_prompt)
                    await asyncio.sleep(1)
                    
                    gen_btn = page.locator("button:has-text('Generar'), button:has-text('Generate')").first
                    if await gen_btn.is_visible():
                        await gen_btn.click()
                        logger.success("Audio Overview generation started with custom prompt.")
        except Exception as e:
            logger.warning(f"Failed to customize Audio Overview: {e}")

        return True
        
    except Exception as e:
        logger.error(f"NotebookLM Automation Error: {e}")
        return False
