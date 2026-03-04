# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle

from ..config.manager import config, ENV_PATH, HISTORY_PATH
from ..ui.commands import CLI_COMMANDS
from ..ui.completer import CustomCompleter
from ..ui.banner import get_banner
from ..ui.style import prompt_style
from ..database.db import DatabaseManager
from .updater import UpdateManager
from .auth import AuthManager

# Load environment variables early
load_dotenv(ENV_PATH)
console = Console()

class VortexCLI:
    def __init__(self):
        self.db = DatabaseManager()
        self.auth = AuthManager(self.db)
        self.completer = CustomCompleter()
        self.session = PromptSession(
            history=FileHistory(HISTORY_PATH),
            completer=self.completer,
            complete_while_typing=True,
            complete_style=CompleteStyle.MULTI_COLUMN
        )
        self.updater = UpdateManager(self.session)
        self.ctrl_c_count = 0

    def cmd_config(self, args: str = ""):
        parts = args.split()
        if not parts or parts[0] == "show":
            from rich.table import Table
            from rich import box
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
        console.print(get_banner())
        
        if config.get("auto_update"):
            self.updater.cmd_update(silent=True)
        
        if not self.auth.is_configured(): 
            self.auth.cmd_auth()
        
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
                elif cmd == 'auth': self.auth.cmd_auth()
                elif cmd == 'update': self.updater.cmd_update(arg)
                elif cmd == 'config': self.cmd_config(arg)
                elif cmd == 'check': self.db.cmd_check()
                elif cmd == 'tables': self.db.cmd_tables()
                elif cmd == 'query': self.db.cmd_query(arg)
                elif cmd == 'clear': 
                    os.system('cls' if os.name == 'nt' else 'clear')
                    console.print(get_banner())
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
