import asyncio
from datetime import datetime
import os

async def automate_notebooklm_upload(context, file_path, logger):
    """
    Automates the process of creating a new notebook and uploading a source to NotebookLM.
    Robust version with Login Retry.
    """
    logger.info("Starting Robust NotebookLM Automation (Step 2)...")
    
    attempts = 0
    while attempts < 2:
        # Check if context is valid
        if not context:
            logger.error("No valid browser context found.")
            return False
            
        page = await context.new_page()
        try:
            await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=60000)
            
            # Robust Multi-language and Role-based Selectors
            new_nb_selectors = [
                "button:has-text('Nuevo')",
                "button:has-text('New')",
                "div[role='button']:has-text('Nuevo')",
                "div[role='button']:has-text('New')",
                "button:has(mat-icon:has-text('add'))",
                "[aria-label*='notebook']",
                "[aria-label*='cuaderno']"
            ]
            
            # 1. Detection Loop (10 seconds)
            new_nb_btn = None
            for _ in range(10):
                for selector in new_nb_selectors:
                    try:
                        btn = page.locator(selector).first
                        if await btn.is_visible():
                            new_nb_btn = btn
                            break
                    except: continue
                if new_nb_btn: break
                await asyncio.sleep(1)
            
            if not new_nb_btn:
                if attempts == 0:
                    logger.warning("🔑 SESIÓN NO DETECTADA. Por favor, inicia sesión en la ventana de Comet que se acaba de abrir.")
                    # Launch Comet using the MAGIC COMMAND from Skill
                    login_url = "https://notebooklm.google.com/"
                    os.system(f'cmd /c start "" "C:\\Users\\Acarvi\\Desktop\\Comet.lnk" "{login_url}"')
                    
                    print("\n" + "!"*60)
                    print("ATENCIÓN: Se requiere inicio de sesión en NotebookLM.")
                    print("!"*60)
                    input("Presiona ENTER en esta consola UNA VEZ HAYAS INICIADO SESIÓN en la ventana de Comet...")
                    
                    attempts += 1
                    await page.close()
                    continue
                else:
                    logger.error("Could not find 'New Notebook' button after retry. Are you signed in?")
                    return False
            
            # 2. Automation Flow
            logger.info("Clicking 'New Notebook'...")
            await new_nb_btn.click()
            await asyncio.sleep(10) # Longer wait for notebook creation
            
            # Rename Notebook
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

            # 3. Upload File
            logger.info(f"Uploading file: {file_path}")
            try:
                # File input is sometimes hidden but available
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
            
            # 4. Audio Overview Customization
            try:
                logger.info("Initializing Audio Overview Customization...")
                await asyncio.sleep(20) # Wait for initial processing
                
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
                else:
                    logger.warning("Could not find 'Customize' button. Audio Overview might still be processing or disabled.")
            except Exception as e:
                logger.warning(f"Failed to customize Audio Overview: {e}")

            return True
            
        except Exception as e:
            logger.error(f"NotebookLM Automation Error: {e}")
            attempts += 1
        finally:
            if attempts >= 2 or new_nb_btn: 
                pass
            else:
                try: await page.close()
                except: pass
    return False
