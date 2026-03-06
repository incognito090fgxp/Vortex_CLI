# -*- coding: utf-8 -*-
from rich.console import Console
from prompt_toolkit import prompt as pk_prompt
from vortex.ui.engine import pager

from .schema import SchemaManager
from .browser import DataBrowser

console = Console()

class TableExplorer:
    """Navigation hub for database tables."""
    def __init__(self, core):
        self.core = core
        self.schema = SchemaManager(core)
        self.browser = DataBrowser(core)

    def show_tables(self):
        while True:
            rows = self.core._execute("""
                SELECT relname as name, n_live_tup as rows 
                FROM pg_stat_user_tables ORDER BY relname
            """)
            if rows is None: break
            if not rows:
                console.print("\n[yellow]No tables found in 'public' schema.[/yellow]")
                break
            
            cols = [
                {"name": "Table Name", "key": "name", "style": "bold green"},
                {"name": "Rows (approx)", "key": "rows", "style": "dim yellow"}
            ]
            
            selected = pager(rows, title="Database Explorer", columns=cols, page_size=10, 
                           description="[Enter] Manage Table | [Q] Back")
            
            if not selected: break
            self._manage_table(selected['name'])

    def _manage_table(self, table_name):
        actions = [
            {"id": "columns", "action": "View Columns (Structure)", "desc": "Structure and column management"},
            {"id": "browse", "action": "Browse Data (Rows)", "desc": "Interactive data browser"},
            {"id": "truncate", "action": "Truncate Table (Clear)", "desc": "Delete ALL data (CASCADE)"},
            {"id": "drop", "action": "Drop Table (Delete)", "desc": "Delete table entirely"}
        ]
        cols = [{"name": "Action", "key": "action", "style": "bold cyan"},
                {"name": "Description", "key": "desc", "style": "dim"}]
        
        while True:
            choice = pager(actions, title=f"Table: {table_name}", columns=cols)
            if not choice: break
            
            cid = choice['id']
            if cid == "columns": self.schema.show_columns(table_name)
            elif cid == "browse": self.browser.browse_data(table_name)
            elif cid == "truncate":
                if self._confirm_danger(f"Truncate table {table_name}?"):
                    self.core._execute(f"TRUNCATE TABLE {table_name} CASCADE", fetch=False, commit=True)
            elif cid == "drop":
                if self._confirm_danger(f"DROP table {table_name}?"):
                    self.core._execute(f"DROP TABLE {table_name} CASCADE", fetch=False, commit=True)
                    return

    def _confirm_danger(self, message):
        try:
            console.print(f"\n[bold red]⚠ WARNING:[/bold red] {message}")
            ans = pk_prompt("Type 'yes' to confirm: ")
            return ans.lower().strip() == 'yes'
        except: return False
