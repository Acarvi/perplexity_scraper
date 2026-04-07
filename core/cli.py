import os
import json
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

class CLILogger:
    @staticmethod
    def info(msg):
        console.print("[bold blue]INFO[/bold blue]", msg)

    @staticmethod
    def success(msg):
        console.print("[bold green]SUCCESS[/bold green]", msg)

    @staticmethod
    def error(msg):
        console.print("[bold red]ERROR[/bold red]", msg)

    @staticmethod
    def warning(msg):
        console.print("[bold yellow]WARNING[/bold yellow]", msg)

def show_banner():
    console.print("\n[bold cyan]==========================================[/bold cyan]")
    console.print("[bold cyan]   Perplexity Discover Scraper (HighPerf)[/bold cyan]")
    console.print("[bold cyan]==========================================[/bold cyan]\n")

def get_user_config():
    # TEST MODE: Default to last 24h to ensure results for verification
    mode = "last_24h"
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(hours=24)
    custom_hours = 24
    
    return mode, start_date, custom_hours

def create_progress():
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    )

def save_last_run_time():
    last_run = {"last_run": datetime.now(timezone.utc).isoformat()}
    with open("last_run.json", "w") as f:
        json.dump(last_run, f)

def log_debug(msg):
    with open("debug_scraper.log", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {msg}\n")
