# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
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
        return f"[bold cyan]🌀 VORTEX CLI [dim]v{VERSION}[/dim][/bold cyan]"

    def cmd_config(self, args: str = ""):
        from rich.console import Console
        from rich.table import Table
        console = Console()
        parts = args.split()
        if not parts or parts[0] == "show":
            t = Table(title="Global Settings")
            t.add_column("Setting", style="cyan")
            t.add_column("Value", style="green")
            for k, v in config.settings.items(): t.add_row(k, str(v))
            console.print(t)
        elif parts[0] == "auto_update" and len(parts) > 1:
            val = parts[1].lower() in ("on", "true", "yes", "1")
            config.set("auto_update", val)
            console.print(f"[green]auto_update set to {val}[/green]")

    def run(self):
        from rich.console import Console
        console = Console()
        console.print(self.get_banner())
        
        if config.get("auto_update"):
            self.updater.check_for_updates(silent=True)

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
                    from rich.table import Table
                    from rich.panel import Panel
                    h = Table(show_header=False, box=None)
                    for c, d in CLI_COMMANDS.items(): h.add_row(f"[bold cyan]{c}[/bold cyan]", d)
                    console.print(Panel(h, title="Commands", border_style="blue"))
                elif cmd == 'update': self.updater.check_for_updates(arg)
                elif cmd == 'config': self.cmd_config(arg)
                elif cmd == 'check': self.db.get_connection() and console.print("[green]ONLINE[/green]")
                elif cmd == 'tables': self.db.list_tables()
                elif cmd == 'query': self.db.run_query(arg)
                elif cmd == 'clear': os.system('cls' if os.name == 'nt' else 'clear'); console.print(self.get_banner())
                else:
                    if cmd in ('select', 'insert', 'update', 'delete', 'create', 'drop', 'with'): self.db.run_query(text)
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
