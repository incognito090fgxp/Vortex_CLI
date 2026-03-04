# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv, dotenv_values
from prompt_toolkit import prompt
from rich.console import Console
from rich.panel import Panel
from ..config.manager import ENV_PATH

console = Console()

class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def is_configured(self):
        if not os.path.exists(ENV_PATH): return False
        env_data = dotenv_values(ENV_PATH)
        password = env_data.get("DB_PASSWORD", "")
        return password not in ["your_password_here", "", None]

    def save_env(self, data: dict):
        try:
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                for key, val in data.items(): f.write(f"{key}={val}\n")
            load_dotenv(ENV_PATH, override=True)
            console.print(Panel("[green]✅ Settings Applied![/green]", expand=False))
        except Exception as e: 
            console.print(f"[red]Error saving .env: {e}[/red]")

    def cmd_auth(self):
        console.print(Panel.fit("[yellow]🛠 Connection Setup[/yellow]"))
        try:
            new = {}
            new["DB_HOST"] = prompt("Host [localhost]: ") or "localhost"
            new["DB_PORT"] = prompt("Port [5432]: ") or "5432"
            new["DB_NAME"] = prompt("DB Name [postgres]: ") or "postgres"
            new["DB_USER"] = prompt("User [postgres]: ") or "postgres"
            new["DB_PASSWORD"] = prompt("Password: ", is_password=True)
            self.save_env(new)
            self.db.close() # Reset connection cache
        except: 
            console.print("\n[dim]Cancelled.[/dim]")
