# -*- coding: utf-8 -*-
from rich.console import Console
from prompt_toolkit import prompt as pk_prompt
from vortex.ui.engine import pager

console = Console()

class DataBrowser:
    """Handles data browsing and row-level actions."""
    def __init__(self, core):
        self.core = core

    def browse_data(self, table_name):
        while True:
            rows = self.core._execute(f'SELECT * FROM "{table_name}" LIMIT 200')
            if not rows:
                console.print(f"[yellow]Table {table_name} is empty.[/yellow]")
                return
            
            col_names = list(rows[0].keys())
            cols = [{"name": n, "key": n} for n in col_names]
            
            selected = pager(rows, title=f"Data: {table_name}", columns=cols, page_size=10,
                           description="[Enter] Row Actions | [Q] Back")
            
            if not selected: break
            self._manage_row(table_name, selected)

    def _manage_row(self, table_name, row_data):
        # В реальной БД нужен первичный ключ (ID) для действий над строкой.
        # Пока просто выведем информацию.
        console.print(f"\n[bold cyan]Selected Row:[/bold cyan]")
        for k, v in row_data.items():
            console.print(f"  {k}: [yellow]{v}[/yellow]")
        
        actions = [{"id": "info", "action": "Row Details", "desc": "Show full row data"}]
        cols = [{"name": "Action", "key": "action"}]
        pager(actions, title="Row Actions", columns=cols)
