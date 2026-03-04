# -*- coding: utf-8 -*-
import os
import psycopg
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

class DatabaseManager:
    def __init__(self):
        self.conn = None

    def get_connection(self):
        """Returns or creates a database connection."""
        if self.conn and not self.conn.closed:
            if self.conn.info.transaction_status == psycopg.pq.TransactionStatus.INERROR:
                self.conn.rollback()
            return self.conn
        
        try:
            self.conn = psycopg.connect(
                host=os.getenv("DB_HOST"), 
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"), 
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"), 
                autocommit=False, 
                connect_timeout=5
            )
            return self.conn
        except Exception as e:
            console.print(f"\n[bold red]OFFLINE[/bold red] {e}")
            return None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def run_query(self, sql: str):
        """Executes a SQL query and displays results."""
        if not sql: return
        conn = self.get_connection()
        if not conn: return
        
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                console.print()
                if cur.description:
                    t = Table(box=box.MINIMAL_DOUBLE_HEAD, header_style="bold yellow")
                    for d in cur.description: 
                        t.add_column(d[0])
                    for r in cur.fetchmany(50): 
                        t.add_row(*[str(i) for i in r])
                    console.print(t)
                else:
                    conn.commit()
                    console.print("[bold green]✔ Committed.[/bold green]")
        except Exception as e:
            if conn: conn.rollback()
            console.print(Panel(f"[bold red]{e}[/bold red]", title="SQL Error", expand=False))

    def list_tables(self):
        """Lists all public tables in the database."""
        conn = self.get_connection()
        if not conn: return
        
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
                rows = cur.fetchall()
                console.print()
                if not rows: 
                    console.print("[yellow]No tables.[/yellow]")
                else:
                    t = Table(box=box.ROUNDED, header_style="bold cyan")
                    t.add_column("Idx", style="dim")
                    t.add_column("Table Name", style="bold green")
                    for i, (n,) in enumerate(rows, 1): 
                        t.add_row(str(i), n)
                    console.print(t)
        except Exception as e: 
            if conn: conn.rollback()
            console.print(f"[red]Error: {e}[/red]")
