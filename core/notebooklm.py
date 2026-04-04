import asyncio
from datetime import datetime
import os

async def automate_notebooklm_upload(context, file_path, logger):
    """
    Automates the process of creating a new notebook and uploading a source to NotebookLM.
    Expects an authenticated context.
    """
    logger.info("Starting NotebookLM Automation (Step 2)...")
    
    # 1. Navigate to NotebookLM
    page = await context.new_page()
    try:
        await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5) # Wait for UI to settle
        
        # Check if we are logged in (look for 'New Notebook' or equivalent)
        # Trying multiple languages/roles for robustness
        new_nb_selectors = [
            "text='New notebook'", 
            "text='Nuevo cuaderno'", 
            "button:has-text('New notebook')", 
            "button:has-text('Nuevo cuaderno')",
            "div[aria-label*='Create']",
            "div[aria-label*='Crear']"
        ]
        
        new_nb_btn = None
        for selector in new_nb_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible():
                    new_nb_btn = btn
                    break
            except: continue
        
        if not new_nb_btn:
            logger.error("Could not find 'New Notebook' button. Are you signed in?")
            # Screenshot for debug if we had a way to save it easily
            return False
            
        logger.info("Clicking 'New Notebook'...")
        await new_nb_btn.click()
        await asyncio.sleep(5) # Wait for notebook creation
        
        # 2. Rename Notebook
        today = datetime.now().strftime("%d/%m/%Y")
        new_name = f"Noticias del día {today}"
        
        logger.info(f"Renaming notebook to: {new_name}")
        try:
            # Stable selector for the title input
            title_input = page.locator("input.title-input").first
            if await title_input.is_visible():
                await title_input.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await title_input.fill(new_name)
                await page.keyboard.press("Enter")
                await asyncio.sleep(2)
            else:
                # Fallback to general title locators
                title_loc = page.locator("h1, [role='textbox'][aria-label*='title'], [contenteditable='true']").first
                if await title_loc.is_visible():
                    await title_loc.click()
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")
                    await page.keyboard.type(new_name)
                    await page.keyboard.press("Enter")
        except Exception as e:
            logger.warning(f"Could not rename notebook: {e}")

        # 3. Upload File
        logger.info(f"Uploading file: {file_path}")
        # Look for the file input or the 'Upload' button
        # Playwright's set_input_files works on <input type='file'>
        try:
            # Often the input is hidden, so we look for the generic one
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                await file_input.set_input_files(file_path)
            else:
                # If no direct input, try to click 'Add source' -> 'Upload'
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
        
        # 4. Audio Overview Customization (Podcast Prompt)
        try:
            logger.info("Initializing Audio Overview Customization...")
            # Wait for processing to settle
            await asyncio.sleep(15) 
            
            # Find the 'Customize' chevron button
            customize_btn = page.locator("button:has(mat-icon:has-text('chevron_forward'))").first
            if not await customize_btn.is_visible():
                customize_btn = page.locator("button:has-text('Personalizar'), button:has-text('Customize')").first
                
            if await customize_btn.is_visible():
                logger.info("Clicking 'Customize' for Audio Overview...")
                await customize_btn.click()
                await asyncio.sleep(3)
                
                # In the dialog, find the textarea
                prompt_textarea = page.locator("mat-dialog-content textarea, textarea[aria-label*='focus'], textarea[aria-label*='centrarse']").first
                if await prompt_textarea.is_visible():
                    podcast_prompt = "Generate a professional, long-form podcast in English. Use a deep analytical tone and focus on the connection between the main news and its sources."
                    logger.info(f"Injecting podcast prompt: {podcast_prompt}")
                    await prompt_textarea.fill(podcast_prompt)
                    await asyncio.sleep(1)
                    
                    # Click Generate (Generar)
                    gen_btn = page.locator("button:has-text('Generar'), button:has-text('Generate')").first
                    if await gen_btn.is_visible():
                        await gen_btn.click()
                        logger.success("Audio Overview generation started with custom prompt.")
            else:
                logger.warning("Could not find 'Customize' button. Audio Overview might still be processing or disabled.")
        except Exception as e:
            logger.error(f"Failed to customize Audio Overview: {e}")

        # 5. Final Wait
        await asyncio.sleep(10) # Let it process
        return True
        
    except Exception as e:
        logger.error(f"NotebookLM Automation Error: {e}")
        return False
    finally:
        # We don't close the page here if the user wants to see it, 
        # but the request says 'automated', so maybe we should leave it open for them?
        # User said "cierre total de ventanas" in the PREVIOUS phase, but for this one
        # they said "navegando a notebooklm... espera a que se procese".
        # I'll keep the page open so they can see the result.
        pass
