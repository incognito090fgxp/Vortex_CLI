# -*- coding: utf-8 -*-
import os
import sys
import copy
import psycopg
import re
from dotenv import load_dotenv, dotenv_values
from typing import Optional, Iterable, List

# SET PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle

from vortex_commands import CLI_COMMANDS
from vortex_config import config, VERSION
from vortex_completer import CustomCompleter

ENV_PATH = os.path.join(BASE_DIR, ".env")
HISTORY_PATH = os.path.join(BASE_DIR, ".vortex_history")
BUILD_DIR = os.path.join(BASE_DIR, ".build")

load_dotenv(ENV_PATH)
console = Console()

prompt_style = PromptStyle.from_dict({
    "prompt": "bold cyan",
    "at": "#888888",
    "host": "italic yellow",
    "bottom-toolbar": "#ffffff bg:#222222",
    "completion-menu.completion": "bg:#333333 #ffffff",
    "completion-menu.completion.current": "bg:#00aaaa #000000",
    "completion-menu.meta.completion": "bg:#444444 #aaaaaa",
})

class VortexCLI:
    def __init__(self):
        if not os.path.exists(BUILD_DIR):
            try: os.makedirs(BUILD_DIR)
            except: pass
        
        self.completer = CustomCompleter()
        self.session = PromptSession(
            history=FileHistory(HISTORY_PATH),
            completer=self.completer,
            complete_while_typing=True,
            complete_style=CompleteStyle.MULTI_COLUMN
        )
        self.db_conn = None
        self.ctrl_c_count = 0

    def get_banner(self):
        width = console.size.width
        if width < 65: return f"[bold cyan]🌀 VORTEX CLI[/bold cyan] [dim]v{VERSION}[/dim]\n"
        return f"""
[bold cyan]
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
[/bold cyan][dim]Vortex CLI v{VERSION}[/dim]
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
        except: console.print("\n[dim]Cancelled.[/dim]")

    def get_connection(self):
        if self.db_conn and not self.db_conn.closed:
            if self.db_conn.info.transaction_status == psycopg.pq.TransactionStatus.INERROR:
                self.db_conn.rollback()
            return self.db_conn
        try:
            self.db_conn = psycopg.connect(
                host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"), autocommit=False, connect_timeout=5
            )
            return self.db_conn
        except Exception as e:
            console.print(f"\n[bold red]OFFLINE[/bold red] {e}")
            return None

    def cmd_check(self):
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
            p.add_task("Checking...", total=None); conn = self.get_connection()
        if conn:
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
        except Exception as e: 
            if conn: conn.rollback()
            console.print(f"[red]Error: {e}[/red]")

    def cmd_config(self, args: str = ""):
        parts = args.split()
        if not parts or parts[0] == "show":
            t = Table(title="Global Settings", box=box.ROUNDED)
            t.add_column("Setting", style="cyan")
            t.add_column("Value", style="green")
            for k, v in config.settings.items():
                t.add_row(k, str(v))
            console.print(t)
        elif parts[0] == "auto_update":
            if len(parts) > 1:
                val = parts[1].lower() in ("on", "true", "yes", "1")
                config.set("auto_update", val)
                console.print(f"[green]auto_update set to {val}[/green]")
            else:
                console.print(f"auto_update is {config.get('auto_update')}")
        else:
            console.print("[red]Usage: config [show | auto_update on/off][/red]")

    def cmd_update(self, silent=False):
        import subprocess
        if not silent: console.print("[yellow]Checking for updates...[/yellow]")
        try:
            # Check git version first
            git_ver = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if git_ver.returncode != 0:
                if not silent: console.print("[red]Error: git is not installed or not in PATH.[/red]")
                return

            # Get current branch
            branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=BASE_DIR)
            if branch_res.returncode != 0:
                if not silent: 
                    console.print(f"[red]Error getting current branch: {branch_res.stderr.strip()}[/red]")
                    console.print(f"[dim]Working directory: {BASE_DIR}[/dim]")
                    if "dubious ownership" in branch_res.stderr:
                        console.print(f"\n[yellow]Try running:[/yellow]\n[bold green]git config --global --add safe.directory {BASE_DIR}[/bold green]")
                return
            branch = branch_res.stdout.strip()

            # Fetch updates
            fetch_res = subprocess.run(["git", "fetch"], capture_output=True, text=True, cwd=BASE_DIR)
            if fetch_res.returncode != 0:
                if not silent:
                    console.print(f"[red]Error during git fetch: {fetch_res.stderr.strip()}[/red]")
                    if "dubious ownership" in fetch_res.stderr:
                        console.print(f"\n[yellow]Try running:[/yellow]\n[bold green]git config --global --add safe.directory {BASE_DIR}[/bold green]")
                return

            # Determine upstream
            upstream_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", f"{branch}@{{u}}"], capture_output=True, text=True, cwd=BASE_DIR)
            if upstream_res.returncode == 0:
                upstream = upstream_res.stdout.strip()
            else:
                upstream = None
                for candidate in [f"origin/{branch}", "origin/main", "origin/master"]:
                    check = subprocess.run(["git", "rev-parse", "--verify", candidate], capture_output=True, cwd=BASE_DIR)
                    if check.returncode == 0:
                        upstream = candidate
                        break
            
            if not upstream:
                if not silent: console.print("[red]Error: Upstream branch not found.[/red]")
                return

            # Compare commits
            behind_res = subprocess.run(["git", "rev-list", "--count", f"HEAD..{upstream}"], capture_output=True, text=True, cwd=BASE_DIR)
            if behind_res.returncode != 0:
                if not silent: console.print(f"[red]Error checking update status: {behind_res.stderr.strip()}[/red]")
                return
            
            behind_count = int(behind_res.stdout.strip() or 0)
            if behind_count > 0:
                console.print(f"[bold cyan]🚀 Update available! You are behind by {behind_count} commit(s).[/bold cyan]")
                confirm = self.session.prompt("Update now? (y/n): ").lower().strip()
                if confirm == 'y':
                    console.print("[yellow]Updating...[/yellow]")
                    result = subprocess.run(["git", "pull"], capture_output=True, text=True, cwd=BASE_DIR)
                    if result.returncode == 0:
                        console.print("[bold green]✅ Updated successfully![/bold green]")
                        console.print("[yellow]Please restart Vortex CLI to apply changes.[/yellow]")
                        sys.exit(0)
                    else:
                        console.print(f"[bold red]Update failed:[/bold red]\n{result.stderr.strip()}")
                else:
                    console.print("[dim]Update deferred.[/dim]")
            else:
                if not silent: console.print("[green]You are already on the latest version.[/green]")
        except Exception as e:
            if not silent: console.print(f"[red]Unexpected error during update: {e}[/red]")

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
        if config.get("auto_update"):
            self.cmd_update(silent=True)
        if not self.is_configured(): self.cmd_auth()
        while True:
            try:
                db_host = os.getenv('DB_HOST', 'localhost')
                msg = [('class:prompt', 'vortex'), ('class:at', '@'), ('class:host', db_host), ('class:prompt', '> ')]
                text = self.session.prompt(msg, style=prompt_style, bottom_toolbar=lambda: HTML('<b>TAB</b>: menu')).strip()
                if not text: continue
                parts = text.split(maxsplit=1)
                cmd, arg = parts[0].lower(), (parts[1] if len(parts) > 1 else "")
                if cmd == 'exit': break
                elif cmd == 'help': self.show_help()
                elif cmd == 'auth': self.cmd_auth()
                elif cmd == 'update': self.cmd_update()
                elif cmd == 'config': self.cmd_config(arg)
                elif cmd == 'check': self.cmd_check()
                elif cmd == 'tables': self.cmd_tables()
                elif cmd == 'query': self.cmd_query(arg)
                elif cmd == 'clear': console.clear(); console.print(self.get_banner())
                else:
                    if cmd in ('select', 'insert', 'update', 'delete', 'create', 'drop', 'with'): self.cmd_query(text)
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
