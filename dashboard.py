import flet as ft
import asyncio
import threading
import os
import scraper # Our refactored scraper

# Try to disable GPU for Flet to prevent hardware issues reported by user
os.environ["FLET_FORCE_SOFTWARE_RENDERER"] = "1"
# os.environ["WGPU_BACKEND"] = "gl" # Remove to avoid driver crashes

class Dashboard:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Perplexity Discover Scraper"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.page.window_width = 700
        self.page.window_height = 800
        self.page.bgcolor = "#111111"
        
        # Log terminal
        self.log_view = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            auto_scroll=True,
        )
        
        self.terminal_container = ft.Container(
            content=self.log_view,
            bgcolor="#1a1a1a",
            border_radius=10,
            border=ft.Border.all(1, "#333333"),
            expand=True,
            padding=5,
        )

        self.full_scrape_chk = ft.Checkbox(
            label="Full Scrape (Ignore Last Run)",
            value=False,
            label_style=ft.TextStyle(color=ft.Colors.BLUE_200)
        )
        
        self.headless_chk = ft.Checkbox(
            label="Headless Mode (Safe/No Monitor Reset)",
            value=False,
            label_style=ft.TextStyle(color=ft.Colors.GREEN_200)
        )

        # Buttons
        self.start_btn = ft.FilledButton(
            "🚀 START SCRAPER",
            on_click=self.start_scraping,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_700,
                padding=20,
                shape=ft.RoundedRectangleBorder(radius=10),
            )
        )
        
        self.copy_btn = ft.IconButton(
            icon=ft.Icons.COPY_ALL,
            tooltip="Copy Logs",
            on_click=self.copy_logs,
            icon_color=ft.Colors.BLUE_200,
        )
        
        self.open_btn = ft.IconButton(
            icon=ft.Icons.FILE_OPEN,
            tooltip="Open Results",
            on_click=self.open_results,
            icon_color=ft.Colors.GREEN_400,
        )

        # Header
        header = ft.Row(
            [
                ft.Text("PERPLEXITY DISCOVER", size=24, color=ft.Colors.BLUE_400, weight="bold"),
                ft.Row([self.copy_btn, self.open_btn], spacing=10)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.page.add(
            header,
            ft.Divider(height=20, color="#333333"),
            self.terminal_container,
            ft.Row([self.full_scrape_chk, self.headless_chk], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.start_btn], alignment=ft.MainAxisAlignment.CENTER)
        )

    async def add_log(self, text):
        self.log_view.controls.append(
            ft.Text(f"> {text}", color="#cccccc", font_family="monospace")
        )
        self.page.update()

    async def monitor_logs(self):
        while True:
            try:
                # Use a non-blocking check for the thread-safe queue
                while not scraper.log_queue.empty():
                    msg = scraper.log_queue.get_nowait()
                    await self.add_log(msg)
                    scraper.log_queue.task_done()
            except Exception:
                pass
            await asyncio.sleep(0.1)

    def start_scraping(self, e):
        self.start_btn.disabled = True
        self.start_btn.text = "RUNNING..."
        self.log_view.controls.clear() # Clear previous logs
        self.page.update()
        
        full_run = self.full_scrape_chk.value
        headless = self.headless_chk.value
        
        # Run the scraper in the background thread
        threading.Thread(target=lambda: asyncio.run(scraper.main(full_run=full_run, headless=headless)), daemon=True).start()

    def copy_logs(self, e):
        log_text = "\n".join([c.value for c in self.log_view.controls if isinstance(c, ft.Text)])
        self.page.set_clipboard(log_text)
        self.page.snack_bar = ft.SnackBar(ft.Text("Logs copied to clipboard!"))
        self.page.snack_bar.open = True
        self.page.update()

    def open_results(self, e):
        if os.path.exists(scraper.OUTPUT_FILE):
            os.startfile(scraper.OUTPUT_FILE)
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("No results file found yet."))
            self.page.snack_bar.open = True
            self.page.update()

async def main(page: ft.Page):
    dashboard = Dashboard(page)
    # Start the log monitoring task
    asyncio.create_task(dashboard.monitor_logs())

if __name__ == "__main__":
    print("--- Initializing Dashboard (Fixed) ---")
    # Setting environm🚀 Prompt Maestra para Google Antigravity: Refactorización y Testing

Rol del Agente: Eres Google Antigravity, un Agente de Desarrollo Autónomo.
Objetivo de esta sesión: Ejecutar una refactorización arquitectónica para mejorar la mantenibilidad de la aplicación, solucionar deuda técnica detectada en los logs y asegurar la estabilidad del sistema mediante TDD.

🧐 Evaluación del Estado Actual (Contexto para Antigravity)

He analizado el código fuente, los logs de ejecución y los artefactos de salida (perplexity_discover_content.txt).

Estado Operativo: El scraper es funcional (procesó 74 historias con éxito), pero el código es un bloque monolítico difícil de mantener.

Problema Principal (Arquitectura): El archivo scraper.py mezcla lógica de configuración, scraping de UI y persistencia. Esto viola el principio de responsabilidad única y hace que sea imposible de testear unitariamente, lo cual rompe el protocolo de skill_testing.md.

Deuda Técnica: Existe un DeprecationWarning: app() is deprecated since version 0.80.0. Use run() instead. en dashboard.py que debe corregirse.

📋 PLAN DE ACCIÓN EXIGIDO (Debes seguir este flujo estrictamente)

FASE 1: Aislamiento y Planificación

Branching: NO trabajes en main. Crea y muévete a una rama nueva: git checkout -b feature/refactor-and-unit-testing

Plan de Implementación: Genera un archivo implementation_plan.md que detalle:

Cómo vas a modularizar scraper.py (separando la lógica de extracción y limpieza de la lógica de navegación).

Estrategia de testing para las funciones puras.

FASE 2: Implementación del Código (Coding)

Refactorización Testeable: Divide scraper.py en módulos. El objetivo es que funciones como clean_noise y los extractores de datos sean funciones puras que puedan probarse sin levantar un navegador.

Corrección de Warnings: Actualiza dashboard.py sustituyendo ft.app(target=main) por el método ft.run() o equivalente según la documentación actual de Flet, asegurando que el dashboard inicie correctamente.

Estabilidad de GPU: Asegura que los flags de lanzamiento de Comet (--disable-gpu, --disable-software-rasterizer) estén bien implementados para evitar el estrés del hardware detectado en sesiones anteriores.

FASE 3: Validación y Testing (Protocolo de skill_testing.md)

Creación de Tests: Crea un directorio tests/ y añade test_logic.py.

Escribe tests unitarios exhaustivos para:

Limpieza de texto (Regex de ruido).

Formateo de fechas y links.

Validación de contenido extraído.

Ejecución: Ejecuta los tests. La tarea no se considera terminada hasta que todos los tests pasen (Exit Code 0).

FASE 4: Cierre y Documentación (Protocolo de skill_documentation.md)

Actualiza el README.md con la nueva estructura del proyecto.

Registra en memory_log.md la resolución del Warning de Flet y la transición a una arquitectura modular testeable.

Directiva Final: Procede de forma atómica. Empieza con la creación de la rama y el plan de implementación.ent variables for stability
    os.environ["FLET_FORCE_SOFTWARE_RENDERER"] = "1"
    
    try:
        # Fixed: DeprecationWarning: app() is deprecated since version 0.80.0. Use run() instead.
        ft.run(main)
    except Exception as e:
        print(f"Error launching Dashboard: {e}")
