# -*- coding: utf-8 -*-
import os
import psycopg
from psycopg.rows import dict_row
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from prompt_toolkit import prompt as pk_prompt
from vortex.ui.engine import pager

console = Console()

class DatabaseManager:
    def __init__(self):
        self.conn = None

    def get_connection(self):
        """Returns current connection or creates a new one."""
        if self.conn and not self.conn.closed:
            if self.conn.info.transaction_status == psycopg.pq.TransactionStatus.INERROR:
                self.conn.rollback()
            return self.conn
        try:
            self.conn = psycopg.connect(
                host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"), autocommit=False, connect_timeout=5
            )
            return self.conn
        except Exception as e:
            console.print(f"\n[bold red]OFFLINE[/bold red] {e}")
            return None

    def close(self):
        """Closes the connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def cmd_check(self):
        """Standard check command logic."""
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
            p.add_task("Checking...", total=None)
            conn = self.get_connection()
        if conn:
            console.print(Panel(f"[bold green]ONLINE[/bold green] [dim]({os.getenv('DB_NAME')})[/dim]", border_style="green", expand=False))

    def cmd_stats(self):
        """Display database statistics."""
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # DB Size
                cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cur.fetchone()[0]
                
                # Table/Index counts
                cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cur.fetchone()[0]
                
                cur.execute("SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'")
                index_count = cur.fetchone()[0]

                stats_text = (
                    f"Database: [bold cyan]{os.getenv('DB_NAME')}[/bold cyan]\n"
                    f"Size: [bold green]{db_size}[/bold green]\n"
                    f"Tables: [bold yellow]{table_count}[/bold yellow]\n"
                    f"Indexes: [bold blue]{index_count}[/bold blue]"
                )
                console.print(Panel(stats_text, title="DB Statistics", expand=False))
        except Exception as e:
            console.print(f"[red]Stats error: {e}[/red]")

    def cmd_tables(self):
        """Main entry point for Table Management Explorer."""
        conn = self.get_connection()
        if not conn: return
        try:
            while True:
                with conn.cursor() as cur:
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
                    rows = cur.fetchall()
                    if not rows:
                        console.print("\n[yellow]No tables found.[/yellow]")
                        return
                    
                    items = [{"name": r[0]} for r in rows]
                    cols = [{"name": "Table Name", "key": "name", "style": "bold green"}]
                    
                    selected = pager(items, title="Database Explorer", columns=cols, page_size=10, description="[Enter] Manage Table | [Q] Back")
                    
                    if not selected: break
                    
                    self._manage_table(selected['name'])
        except Exception as e: 
            if conn: conn.rollback()
            console.print(f"[red]Explorer Error: {e}[/red]")

    def _manage_table(self, table_name):
        """Action menu for a specific table."""
        actions = [
            {"id": "columns", "action": "View Columns (Structure)"},
            {"id": "browse", "action": "Browse Data (Rows)"},
            {"id": "truncate", "action": "Truncate Table (Clear)"},
            {"id": "drop", "action": "Drop Table (Delete)"}
        ]
        cols = [{"name": "Available Actions", "key": "action", "style": "cyan"}]
        
        while True:
            choice = pager(actions, title=f"Table: {table_name}", columns=cols, description="Select an action to perform")
            if not choice: break
            
            if choice['id'] == "columns":
                self._show_columns(table_name)
            elif choice['id'] == "browse":
                self._browse_data(table_name)
            elif choice['id'] == "truncate":
                if self._confirm_danger(f"Truncate table {table_name}?"):
                    self._execute_simple(f"TRUNCATE TABLE {table_name} CASCADE")
            elif choice['id'] == "drop":
                if self._confirm_danger(f"DROP table {table_name}?"):
                    self._execute_simple(f"DROP TABLE {table_name} CASCADE")
                    return # Table is gone, go back to list

    def _show_columns(self, table_name):
        """Display table structure."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public' 
                ORDER BY ordinal_position
            """, (table_name,))
            rows = cur.fetchall()
            items = [{"name": r[0], "type": r[1], "null": r[2], "def": str(r[3]) if r[3] else ""} for r in rows]
            cols = [
                {"name": "Column", "key": "name", "style": "bold cyan"},
                {"name": "Type", "key": "type", "style": "green"},
                {"name": "Null", "key": "null", "min_width": 60},
                {"name": "Default", "key": "def", "min_width": 80}
            ]
            pager(items, title=f"Structure: {table_name}", columns=cols, description="Press Q to go back")

    def _browse_data(self, table_name):
        """Interactive data browser for a table."""
        conn = self.get_connection()
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(f"SELECT * FROM {table_name} LIMIT 200")
                rows = cur.fetchall()
                if not rows:
                    console.print(f"[yellow]Table {table_name} is empty.[/yellow]")
                    return
                
                # Dynamic columns from keys of the first row
                col_names = list(rows[0].keys())
                cols = [{"name": n, "key": n} for n in col_names]
                
                pager(rows, title=f"Data: {table_name} (Top 200)", columns=cols, page_size=10)
        except Exception as e:
            console.print(f"[red]Browse error: {e}[/red]")

    def _confirm_danger(self, message):
        """Safety confirmation prompt."""
        try:
            ans = pk_prompt(f"[DANGER] {message} (type 'yes' to confirm): ")
            return ans.lower().strip() == 'yes'
        except (KeyboardInterrupt, EOFError):
            return False

    def _execute_simple(self, sql):
        """Execute and commit a simple command."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()
                console.print("[bold green]✔ Action successful.[/bold green]")
        except Exception as e:
            if conn: conn.rollback()
            console.print(f"[bold red]Execution error: {e}[/bold red]")

    def cmd_query(self, sql: str):
        """Interactive SQL query runner."""
        if not sql: return
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql)
                if cur.description:
                    rows = cur.fetchall()
                    if not rows:
                        console.print("\n[yellow]Query returned no rows.[/yellow]")
                        return
                    col_names = list(rows[0].keys())
                    cols = [{"name": n, "key": n} for n in col_names]
                    pager(rows, title="Query Results", columns=cols, page_size=10)
                else:
                    conn.commit()
                    console.print("[bold green]✔ Committed.[/bold green]")
        except Exception as e:
            if conn: conn.rollback()
            console.print(Panel(f"[bold red]{e}[/bold red]", title="SQL Error", expand=False))
