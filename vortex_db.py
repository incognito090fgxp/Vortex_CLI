import os
import sys
import copy
import psycopg
from dotenv import load_dotenv, dotenv_values
from typing import Optional, Iterable, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import NestedCompleter, Completion, Completer, CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion, AutoSuggestFromHistory
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle

from vortex_commands import ALL_DESCRIPTIONS, PLACEHOLDERS, get_completer_map, SQL_HIERARCHY

# ОПРЕДЕЛЯЕМ ПУТИ ОТНОСИТЕЛЬНО СКРИПТА
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
HISTORY_PATH = os.path.join(BASE_DIR, ".vortex_history")

# Загружаем конкретный .env файл
load_dotenv(ENV_PATH)

console = Console()

prompt_style = PromptStyle.from_dict({
    'prompt': 'bold cyan',
    'at': '#888888',
    'host': 'italic yellow',
    'bottom-toolbar': '#ffffff bg:#222222',
    'completion-menu.completion': 'bg:#333333 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'completion-menu.meta.completion': 'bg:#444444 #aaaaaa',
    'auto-suggestion': '#00eeee italic', 
})

class VortexAutoSuggest(AutoSuggest):
    def __init__(self):
        self.history_suggest = AutoSuggestFromHistory()

    def get_suggestion(self, buffer, document: Document) -> Optional[Suggestion]:
        text = document.text.strip().upper()
        for key, value in PLACEHOLDERS.items():
            if text.endswith(key):
                return Suggestion(value)
        return self.history_suggest.get_suggestion(buffer, document)

class CustomCompleter(Completer):
    def __init__(self):
        self.table_names: List[str] = []
        self.refresh_nested()

    def refresh_nested(self, tables: List[str] = None):
        self.table_names = tables or []
        table_map = {f'"{t}"' if (t[0].isdigit() or ' ' in t) else t: None for t in self.table_names}
        dynamic_sql = copy.deepcopy(SQL_HIERARCHY)
        dynamic_sql['SELECT']['*']['FROM'] = table_map
        dynamic_sql['SELECT']['COUNT(*)']['FROM'] = table_map
        dynamic_sql['INSERT']['INTO'] = table_map
        dynamic_sql['UPDATE'] = table_map
        dynamic_sql['DELETE']['FROM'] = table_map
        dynamic_sql['DROP']['TABLE'] = table_map
        completer_dict = get_completer_map()
        completer_dict['query'] = dynamic_sql
        self.nested = NestedCompleter.from_nested_dict(completer_dict)

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        for completion in self.nested.get_completions(document, complete_event):
            meta = ALL_DESCRIPTIONS.get(completion.text.upper(), "")
            if completion.text.strip('"') in self.table_names: meta = "Table"
            yield Completion(completion.text, start_position=completion.start_position, display_meta=meta)

class VortexCLI:
    def __init__(self):
        self.completer = CustomCompleter()
        self.session = PromptSession(
            history=FileHistory(HISTORY_PATH),
            auto_suggest=VortexAutoSuggest(),
            completer=self.completer,
            complete_while_typing=True,
            complete_style=CompleteStyle.MULTI_COLUMN
        )
        self.db_conn = None
        self.ctrl_c_count = 0

    def get_banner(self):
        width = console.size.width
        if width < 65: return "[bold cyan]🌀 VORTEX CLI[/bold cyan] [dim]v0.1[/dim]\n"
        return """
[bold cyan]
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
[/bold cyan][dim]Vortex CLI v0.1[/dim]
"""

    def is_configured(self):
        if not os.path.exists(ENV_PATH): return False
        env_data = dotenv_values(ENV_PATH)
        password = env_data.get("DB_PASSWORD", "")
        return password not in ["your_password_here", "", None]

    def save_env(self, data: dict):
        try:
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                for key, val in data.items(): f.write(f"{key}={val}\n")
            load_dotenv(ENV_PATH, override=True)
            console.print(Panel("[green]✅ Settings Applied![/green]", expand=False))
        except Exception as e: console.print(f"[red]Error: {e}[/red]")

    def cmd_auth(self):
        console.print(Panel.fit("[yellow]🛠 Connection Setup[/yellow]"))
        try:
            new = {}
            new["DB_HOST"] = prompt("Host [localhost]: ") or "localhost"
            new["DB_PORT"] = prompt("Port [5432]: ") or "5432"
            new["DB_NAME"] = prompt("DB Name [postgres]: ") or "postgres"
            new["DB_USER"] = prompt("User [postgres]: ") or "postgres"
            new["DB_PASSWORD"] = prompt("Password: ", is_password=True)
            self.save_env(new)
            if self.db_conn: self.db_conn.close(); self.db_conn = None
            self.refresh_tables_cache()
        except: console.print("\n[dim]Cancelled.[/dim]")

    def get_connection(self):
        if self.db_conn and not self.db_conn.closed:
            if self.db_conn.info.transaction_status == psycopg.pq.TransactionStatus.INERROR:
                self.db_conn.rollback()
            return self.db_conn
        try:
            # Принудительно берем из переменных окружения (они обновлены через load_dotenv)
            self.db_conn = psycopg.connect(
                host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"), autocommit=False, connect_timeout=5
            )
            return self.db_conn
        except Exception as e:
            console.print(f"\n[bold red]OFFLINE[/bold red] {e}")
            return None

    def refresh_tables_cache(self):
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                self.completer.refresh_nested([r[0] for r in cur.fetchall()])
        except: pass

    def cmd_check(self):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
            p.add_task("Checking...", total=None); conn = self.get_connection()
        if conn:
            self.refresh_tables_cache()
            console.print(Panel(f"[bold green]ONLINE[/bold green] [dim]({os.getenv('DB_NAME')})[/dim]", border_style="green", expand=False))

    def cmd_tables(self):
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
                    self.completer.refresh_nested([r[0] for r in rows])
        except Exception as e: 
            if conn: conn.rollback()
            console.print(f"[red]Error: {e}[/red]")

    def cmd_query(self, sql: str):
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
                    if any(x in sql.upper() for x in ('CREATE', 'DROP', 'ALTER')): self.refresh_tables_cache()
        except Exception as e:
            if conn: conn.rollback()
            console.print(Panel(f"[bold red]{e}[/bold red]", title="SQL Error", expand=False))

    def show_help(self):
        from vortex_commands import CLI_COMMANDS
        h = Table(show_header=False, box=None, padding=(0, 2))
        for cmd, desc in CLI_COMMANDS.items(): h.add_row(f"[bold cyan]{cmd}[/bold cyan]", desc)
        console.print(Panel(h, title="Commands", border_style="blue", expand=False))

    def run(self):
        console.print(self.get_banner())
        if not self.is_configured(): self.cmd_auth()
        self.refresh_tables_cache()

        while True:
            try:
                db_host = os.getenv('DB_HOST', 'localhost')
                msg = [('class:prompt', 'vortex'), ('class:at', '@'), ('class:host', db_host), ('class:prompt', '> ')]
                text = self.session.prompt(msg, style=prompt_style, bottom_toolbar=lambda: HTML('<b>TAB</b>: menu | <b>RIGHT</b>: hint')).strip()
                if not text: continue
                parts = text.split(maxsplit=1)
                cmd, arg = parts[0].lower(), (parts[1] if len(parts) > 1 else "")
                if cmd == 'exit': break
                elif cmd == 'help': self.show_help()
                elif cmd == 'auth': self.cmd_auth()
                elif cmd == 'check': self.cmd_check()
                elif cmd == 'tables': self.cmd_tables()
                elif cmd == 'query': self.cmd_query(arg)
                elif cmd == 'clear': console.clear(); console.print(self.get_banner())
                else:
                    if cmd.upper() in ALL_DESCRIPTIONS or cmd in ('select', 'insert', 'update', 'delete', 'create', 'drop', 'with'): self.cmd_query(text)
                    else: console.print(f"[red]Unknown: {cmd}[/red]")
                self.ctrl_c_count = 0
            except KeyboardInterrupt:
                self.ctrl_c_count += 1
                if self.ctrl_c_count >= 2: break
                console.print("\n[dim]Ctrl+C again to exit[/dim]")
            except EOFError: break
            except Exception as e: console.print(f"[red]System Error: {e}[/red]")
        if self.db_conn: self.db_conn.close()

def main():
    VortexCLI().run()

if __name__ == "__main__":
    main()
