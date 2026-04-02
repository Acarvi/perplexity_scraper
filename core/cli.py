import os
import json
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, MofNCompleteColumn
from rich import print as rprint

console = Console()

DATA_DIR = os.path.join(os.getcwd(), "data")
LAST_RUN_FILE = os.path.join(DATA_DIR, "last_run.json")

def get_last_run_time():
    if os.path.exists(LAST_RUN_FILE):
        try:
            with open(LAST_RUN_FILE, "r") as f:
                data = json.load(f)
                return datetime.fromisoformat(data["last_run"]).replace(tzinfo=timezone.utc)
        except Exception: pass
    # Default to 24h ago if no file exists
    return datetime.now(timezone.utc) - timedelta(hours=24)

def save_last_run_time(timestamp):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(LAST_RUN_FILE, "w") as f:
        json.dump({"last_run": timestamp.isoformat()}, f)

def show_banner():
    banner = Panel.fit(
        "[bold cyan]PERPLEXITY DISCOVER[/bold cyan]\n[dim]High-Performance CLI Scraper[/dim]",
        border_style="bright_blue",
        padding=(1, 4)
    )
    console.print(banner)

def get_user_config():
    # Handle CLI flags first
    for arg in sys.argv:
        if arg.startswith("--since="):
            try:
                hours = int(arg.split("=")[1].replace("h", ""))
                last_run = datetime.now(timezone.utc) - timedelta(hours=hours)
                return "custom", last_run, hours
            except: pass

    last_run = get_last_run_time()
    last_run_str = last_run.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    table = Table(title="Select Scrape Range", box=None, show_header=False)
    table.add_row("[1]", "Last 24 hours (Recommend for Newsletter)")
    table.add_row("[2]", f"Since last run ([yellow]{last_run_str}[/yellow])")
    table.add_row("[3]", "Custom hours")
    
    console.print(table)
    
    choice = Prompt.ask("Choose mode", choices=["1", "2", "3"], default="1")
    
    mode_map = {"1": "last_24h", "2": "since_last", "3": "custom"}
    mode = mode_map[choice]
    
    custom_hours = 24
    if mode == "since_last":
        # Calculate hours since last run
        delta = datetime.now(timezone.utc) - last_run
        custom_hours = int(delta.total_seconds() / 3600)
    elif mode == "custom":
        custom_hours = int(Prompt.ask("Enter hours back", default="48"))
    elif mode == "last_24h":
        custom_hours = 24
        
    # Return calculated time
    return mode, datetime.now(timezone.utc) - timedelta(hours=custom_hours), custom_hours

class CLILogger:
    @staticmethod
    def info(msg):
        console.print(f"[bold blue]INFO[/bold blue] {msg}")

    @staticmethod
    def success(msg):
        console.print(f"[bold green]SUCCESS[/bold green] {msg}")

    @staticmethod
    def error(msg):
        console.print(f"[bold red]ERROR[/bold red] {msg}")

    @staticmethod
    def warning(msg):
        console.print(f"[bold yellow]WARNING[/bold yellow] {msg}")

def create_progress():
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True
    )
