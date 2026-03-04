# -*- coding: utf-8 -*-
import os
import psycopg
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

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

    def cmd_tables(self):
        """Standard tables command logic."""
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
                rows = cur.fetchall()
                console.print()
                if not rows: console.print("[yellow]No tables.[/yellow]")
                else:
                    t = Table(box=box.ROUNDED, header_style="bold cyan")
                    t.add_column("Idx", style="dim"); t.add_column("Table Name", style="bold green")
                    for i, (n,) in enumerate(rows, 1): t.add_row(str(i), n)
                    console.print(t)
        except Exception as e: 
            if conn: conn.rollback()
            console.print(f"[red]Error: {e}[/red]")

    def cmd_query(self, sql: str):
        """Standard query command logic."""
        if not sql: return
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                console.print()
                if cur.description:
                    t = Table(box=box.MINIMAL_DOUBLE_HEAD, header_style="bold yellow")
                    for d in cur.description: t.add_column(d[0])
                    for r in cur.fetchmany(50): t.add_row(*[str(i) for i in r])
                    console.print(t)
                else:
                    conn.commit(); console.print("[bold green]✔ Committed.[/bold green]")
        except Exception as e:
            if conn: conn.rollback()
            console.print(Panel(f"[bold red]{e}[/bold red]", title="SQL Error", expand=False))
