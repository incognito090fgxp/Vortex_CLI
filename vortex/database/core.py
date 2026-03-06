# -*- coding: utf-8 -*-
import os
import psycopg
from psycopg.rows import dict_row
from rich.console import Console

console = Console()

class ConnectionManager:
    """Core Database Engine & Inspector."""
    def __init__(self):
        self.conn = None
        self._db_name = os.getenv("DB_NAME", "unknown")

    def get_connection(self):
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
            self._db_name = os.getenv("DB_NAME")
            return self.conn
        except Exception as e:
            console.print(f"\n[bold red]CONNECTION ERROR:[/bold red] {e}")
            return None

    def _execute(self, query, params=None, fetch=True, commit=False):
        conn = self.get_connection()
        if not conn: return None
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, params)
                if commit: conn.commit()
                return cur.fetchall() if fetch else True
        except Exception as e:
            if conn: conn.rollback()
            console.print(f"[bold red]SQL Error:[/bold red] {e}")
            return None

    def get_stats(self):
        """Fetches DB-wide statistics."""
        return self._execute("""
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as size,
                (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as tables,
                (SELECT count(*) FROM pg_indexes WHERE schemaname = 'public') as indexes
        """)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
