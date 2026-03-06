# -*- coding: utf-8 -*-
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from vortex.ui.engine import pager

from .core import ConnectionManager
from .explorer import TableExplorer
from .console import SQLConsole

console = Console()

class DatabaseManager:
    """Orchestrator for Database UI and Modules."""
    def __init__(self):
        self.core = ConnectionManager()
        self.explorer = TableExplorer(self.core)
        self.sql_console = SQLConsole(self)

    def cmd_db(self):
        actions = [
            {"id": "tables", "action": "Explorer", "desc": "Navigate tables, structure and data"},
            {"id": "stats", "action": "Stats", "desc": "Database size and object counts"},
            {"id": "check", "action": "Check", "desc": "Verify connection and health"},
            {"id": "query", "action": "Console", "desc": "Dedicated SQL REPL"}
        ]
        cols = [{"name": "Module", "key": "action", "style": "bold green"},
                {"name": "Description", "key": "desc", "style": "dim"}]

        while True:
            res = pager(actions, title=f"Database: {self.core._db_name}", columns=cols)
            if res is None: break
            
            # Handling both selection and direct text input
            target = res['id'] if isinstance(res, dict) else res.lower().strip()
            
            if target == "tables": self.explorer.show_tables()
            elif target == "stats": self.cmd_stats()
            elif target == "check": self.cmd_check()
            elif target in ("query", "console"): self.sql_console.run()
            elif target in ("exit", "q", "back"): break
            elif not isinstance(res, dict): self.cmd_query(res)

    def cmd_check(self):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
            p.add_task("Health Check...", total=None)
            conn = self.core.get_connection()
        if conn:
            console.print(Panel(f"[bold green]ONLINE[/bold green]\nDB: [cyan]{self.core._db_name}[/cyan]", border_style="green", expand=False))
            input("\nPress Enter...")

    def cmd_stats(self):
        data = self.core.get_stats()
        if not data: return
        s = data[0]
        stats_text = (f"DB: [bold cyan]{self.core._db_name}[/bold cyan]\nSize: [bold green]{s['size']}[/bold green]\n"
                      f"Tables: [bold yellow]{s['tables']}[/bold yellow]\nIndexes: [bold blue]{s['indexes']}[/bold blue]")
        console.print(Panel(stats_text, title="DB Stats", expand=False))
        input("\nPress Enter...")

    def cmd_query(self, sql: str):
        rows = self.core._execute(sql)
        if rows:
            cols = [{"name": n, "key": n} for n in rows[0].keys()]
            pager(rows, title="Query Results", columns=cols)
        elif rows is not None:
            console.print("[bold green]✔ Done.[/bold green]")
            input("\nPress Enter...")

    # Proxy for legacy calls
    def get_connection(self): return self.core.get_connection()
    def close(self): self.core.close()
