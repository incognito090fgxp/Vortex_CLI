# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv, dotenv_values
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle

from .config import config, VERSION, PROJECT_ROOT
from .commands import CLI_COMMANDS
from .completer import CustomCompleter
from .db import DatabaseManager
from .updater import UpdateManager

ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
HISTORY_PATH = os.path.join(PROJECT_ROOT, ".vortex_history")

load_dotenv(ENV_PATH)
console = Console()

prompt_style = PromptStyle.from_dict({
    "prompt": "bold cyan",
    "at": "#888888",
    "host": "italic yellow",
    "bottom-toolbar": "#ffffff bg:#222222",
    "completion-menu.completion": "bg:#333333 #ffffff",
    "completion-menu.completion.current": "bg:#00aaaa #000000",
    "completion-menu.meta.completion": "bg:#444444 #aaaaaa",
})

class VortexCLI:
    def __init__(self):
        self.completer = CustomCompleter()
        self.session = PromptSession(
            history=FileHistory(HISTORY_PATH),
            completer=self.completer,
            complete_while_typing=True,
            complete_style=CompleteStyle.MULTI_COLUMN
        )
        self.db = DatabaseManager()
        self.updater = UpdateManager(self.session)
        self.ctrl_c_count = 0

    def get_banner(self):
        width = console.size.width
        if width < 65: 
            return f"""[bold cyan]
██╗  ██╗ 
╚██╗██╔╝ 
 ╚███╔╝  
  ╚══╝   
🌀 VORTEX CLI [dim]v{VERSION}[/dim][/bold cyan]
"""
        return f"""
[bold cyan]
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
[/bold cyan][dim]Vortex CLI v{VERSION}[/dim]
"""

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
        except Exception as e: console.print(f"[red]Error: {e}[/red]")

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
        except: console.print("\n[dim]Cancelled.[/dim]")

    def cmd_config(self, args: str = ""):
        parts = args.split()
        if not parts or parts[0] == "show":
            t = Table(title="Global Settings", box=box.ROUNDED)
            t.add_column("Setting", style="cyan")
            t.add_column("Value", style="green")
            for k, v in config.settings.items():
                t.add_row(k, str(v))
            console.print(t)
        elif parts[0] == "auto_update":
            if len(parts) > 1:
                val = parts[1].lower() in ("on", "true", "yes", "1")
                config.set("auto_update", val)
                console.print(f"[green]auto_update set to {val}[/green]")
            else:
                console.print(f"auto_update is {config.get('auto_update')}")
        else:
            console.print("[red]Usage: config [show | auto_update on/off][/red]")

    def run(self):
        console.print(self.get_banner())
        if config.get("auto_update"):
            self.updater.cmd_update(silent=True)
        
        if not self.is_configured(): self.cmd_auth()
        
        while True:
            try:
                db_host = os.getenv('DB_HOST', 'localhost')
                msg = [('class:prompt', 'vortex'), ('class:at', '@'), ('class:host', db_host), ('class:prompt', '> ')]
                text = self.session.prompt(msg, style=prompt_style, bottom_toolbar=lambda: HTML('<b>TAB</b>: menu')).strip()
                if not text: continue
                
                parts = text.split(maxsplit=1)
                cmd, arg = parts[0].lower(), (parts[1] if len(parts) > 1 else "")
                
                if cmd == 'exit': break
                elif cmd == 'help':
                    h = Table(show_header=False, box=None, padding=(0, 2))
                    for c, d in CLI_COMMANDS.items(): h.add_row(f"[bold cyan]{c}[/bold cyan]", d)
                    console.print(Panel(h, title="Commands", border_style="blue", expand=False))
                elif cmd == 'auth': self.cmd_auth()
                elif cmd == 'update': self.updater.cmd_update(arg)
                elif cmd == 'config': self.cmd_config(arg)
                elif cmd == 'check': self.db.cmd_check()
                elif cmd == 'tables': self.db.cmd_tables()
                elif cmd == 'query': self.db.cmd_query(arg)
                elif cmd == 'clear': 
                    os.system('cls' if os.name == 'nt' else 'clear')
                    console.print(self.get_banner())
                else:
                    if cmd in ('select', 'insert', 'update', 'delete', 'create', 'drop', 'with'): self.db.cmd_query(text)
                    else: console.print(f"[red]Unknown: {cmd}[/red]")
                self.ctrl_c_count = 0
            except KeyboardInterrupt:
                self.ctrl_c_count += 1
                if self.ctrl_c_count >= 2: break
                console.print("\n[dim]Ctrl+C again to exit[/dim]")
            except EOFError: break
            except Exception as e: console.print(f"[red]System Error: {e}[/red]")
        self.db.close()

def main():
    VortexCLI().run()

if __name__ == "__main__":
    main()
