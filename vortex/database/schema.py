# -*- coding: utf-8 -*-
from rich.console import Console
from prompt_toolkit import prompt as pk_prompt
from vortex.ui.engine import pager

console = Console()

class SchemaManager:
    """Handles table structure and column management."""
    def __init__(self, core):
        self.core = core

    def show_columns(self, table_name):
        while True:
            rows = self.core._execute("""
                SELECT column_name as name, data_type as type, is_nullable as null, column_default as def
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public' 
                ORDER BY ordinal_position
            """, (table_name,))
            if not rows: return
            
            for r in rows:
                if r['def'] is None: r['def'] = ""
            
            cols = [
                {"name": "Column", "key": "name", "style": "bold cyan"},
                {"name": "Type", "key": "type", "style": "green"},
                {"name": "Null", "key": "null", "min_width": 60},
                {"name": "Default", "key": "def", "min_width": 100}
            ]
            
            selected = pager(rows, title=f"Structure: {table_name}", columns=cols, 
                           description="[Enter] Column Actions | [Q] Back")
            
            if not selected: break
            self._manage_column(table_name, selected['name'])

    def _manage_column(self, table_name, column_name):
        actions = [
            {"id": "drop", "action": "Drop Column", "desc": f"Delete '{column_name}' from table"},
            {"id": "rename", "action": "Rename Column", "desc": "Change column name"}
        ]
        cols = [{"name": "Action", "key": "action", "style": "red"}]
        choice = pager(actions, title=f"Column: {column_name}", columns=cols)
        
        if not choice: return
        
        if choice['id'] == "drop":
            if self._confirm_danger(f"DROP column {column_name}?"):
                self.core._execute(f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"', fetch=False, commit=True)
        elif choice['id'] == "rename":
            new_name = pk_prompt(f"New name for {column_name}: ").strip()
            if new_name:
                self.core._execute(f'ALTER TABLE "{table_name}" RENAME COLUMN "{column_name}" TO "{new_name}"', fetch=False, commit=True)

    def _confirm_danger(self, message):
        try:
            console.print(f"\n[bold red]⚠ WARNING:[/bold red] {message}")
            ans = pk_prompt("Type 'yes' to confirm: ")
            return ans.lower().strip() == 'yes'
        except: return False
