# -*- coding: utf-8 -*-
import os
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML

from ..registry import SQL_HISTORY_PATH
from ..ui.style import prompt_style

console = Console()

class SQLConsole:
    """Dedicated SQL REPL with its own history and isolated window."""
    def __init__(self, manager):
        self.manager = manager
        self.session = PromptSession(history=FileHistory(SQL_HISTORY_PATH))

    def run(self):
        """Starts the interactive SQL console in an alternate screen buffer."""
        with console.screen():
            console.clear()
            console.print(Panel(
                "[bold cyan]SQL INTERACTIVE CONSOLE[/bold cyan]\n"
                "Type your SQL queries here. Results will be shown in the pager.\n"
                "History is saved in [bold white].vortex_data/sql_history[/bold white].",
                title="Isolated Mode",
                border_style="cyan"
            ))

            while True:
                try:
                    prompt_msg = [
                        ('class:prompt', 'sql'),
                        ('class:at', '> ')
                    ]
                    
                    query = self.session.prompt(
                        prompt_msg, 
                        style=prompt_style,
                        bottom_toolbar=lambda: HTML('Type <b>exit</b> or <b>q</b> to return | <b>History</b>: ↑/↓')
                    ).strip()
                    
                    if not query:
                        continue
                    if query.lower() in ('exit', 'q', 'back'):
                        break
                    if query.lower() == 'clear':
                        console.clear()
                        continue
                    
                    self.manager.cmd_query(query)
                    
                except (KeyboardInterrupt, EOFError):
                    break
                except Exception as e:
                    console.print(f"[bold red]Console Error:[/bold red] {e}")
        
        console.print("[dim]Exited SQL Console. Returning to main CLI...[/dim]")
