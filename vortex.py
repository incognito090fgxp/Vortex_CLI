# -*- coding: utf-8 -*-
import os
import sys
import copy
import psycopg
import re
import subprocess
from dotenv import load_dotenv, dotenv_values
from typing import Optional, Iterable, List

# SET PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_project_root():
    """Robustly find the project root by searching for pyproject.toml."""
    # 1. Try search upwards starting from current file location
    curr = os.path.abspath(BASE_DIR)
    while curr != os.path.dirname(curr):
        if os.path.exists(os.path.join(curr, "pyproject.toml")):
            return curr
        curr = os.path.dirname(curr)

    # 2. Try detection via venv path (sys.executable)
    try:
        exe_dir = os.path.dirname(sys.executable)
        if os.path.basename(exe_dir).lower() in ('bin', 'scripts'):
            venv_dir = os.path.dirname(exe_dir)
            potential_root = os.path.dirname(venv_dir)
            if os.path.exists(os.path.join(potential_root, "pyproject.toml")):
                return potential_root
    except:
        pass

    # 3. Fallback to git
    try:
        res = subprocess.run(["git", "rev-parse", "--show-toplevel"], 
                             capture_output=True, text=True, cwd=BASE_DIR)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass

    return os.path.abspath(BASE_DIR)

PROJECT_ROOT = find_project_root()

# Ensure PROJECT_ROOT and BASE_DIR are in path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
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

ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
HISTORY_PATH = os.path.join(PROJECT_ROOT, ".vortex_history")

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
        if width < 65: 
            return f"""[bold cyan]
██╗  ██╗ 
╚██╗██╔╝ 
 ╚███╔╝  
  ╚══╝   
🌀 VORTEX CLI [dim]v{VERSION}[/dim][/bold cyan]
"""
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

    def _git_run(self, args, capture=True):
        import subprocess
        try:
            res = subprocess.run(["git"] + args, capture_output=capture, text=True, cwd=PROJECT_ROOT)
            if res.returncode != 0 and capture:
                if "dubious ownership" in res.stderr:
                    console.print(f"\n[yellow]Security issue detected.[/yellow] Run this fix:")
                    console.print(f"[bold green]git config --global --add safe.directory {PROJECT_ROOT}[/bold green]")
            return res
        except Exception as e:
            console.print(f"[red]Git Error: {e}[/red]")
            return None

    def _get_installed_deps(self):
        """Get list of installed packages in the current venv."""
        import importlib.metadata
        return {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}

    def _get_required_deps(self):
        """Parse dependencies from pyproject.toml."""
        toml_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        if not os.path.exists(toml_path):
            return []
        try:
            import tomllib
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("project", {}).get("dependencies", [])
        except:
            return []

    def _sync_deps(self, force=False):
        """Sync dependencies and core logic."""
        import subprocess
        console.print("[yellow]Checking & Syncing dependencies...[/yellow]")
        
        required = self._get_required_deps()
        installed = self._get_installed_deps()
        
        missing = []
        for dep in required:
            name = re.split('[<>=!]', dep)[0].strip().lower()
            if name not in installed:
                missing.append(dep)

        # If everything is installed and no force requested, skip pip
        if not missing and not force:
            console.print("[green]✅ Dependencies already satisfied.[/green]")
            return

        try:
            # 2. Run PIP install
            if os.name == 'nt':
                # Windows: install list to avoid locking
                cmd = [sys.executable, "-m", "pip", "install"] + required + ["--quiet"]
            else:
                # Unix/Termux: Force install from absolute PROJECT_ROOT
                # Using -e (editable) to link site-packages directly to the repo
                cmd = [sys.executable, "-m", "pip", "install", "-e", PROJECT_ROOT, "--upgrade", "--quiet"]

            res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
            if res.returncode == 0:
                console.print("[green]✅ Dependencies and Core synchronized.[/green]")
            else:
                console.print(f"[red]❌ Dependency sync failed.[/red]")
                console.print(f"[dim]{res.stderr}[/dim]")
        except Exception as e:
            console.print(f"[red]Error syncing deps: {e}[/red]")

    def _checkout_and_sync(self, target: str, pull: bool = False):
        """Helper to checkout a target, pull if needed, sync deps and exit."""
        console.print(f"[yellow]Checking out {target}...[/yellow]")
        res = self._git_run(["checkout", target], capture=False)
        if res and res.returncode == 0:
            if pull:
                console.print(f"[yellow]Pulling latest changes for {target}...[/yellow]")
                self._git_run(["pull", "origin", target], capture=False)
            
            # Forced sync after checkout to update logic in venv
            self._sync_deps(force=True)
            console.print("[bold green]✅ Updated successfully![/bold green]")
            sys.exit(0)

    def cmd_update(self, args: str = "", silent=False):
        import subprocess
        parts = args.split()
        sub = parts[0].lower() if parts else "check"

        if sub == "check":
            if not silent: console.print("[yellow]Checking for updates...[/yellow]")
            
            # Fetch everything FIRST to ensure we have the latest history
            self._git_run(["fetch", "--all", "--tags", "--quiet"])

            # Get current branch
            res = self._git_run(["rev-parse", "--abbrev-ref", "HEAD"])
            if not res or res.returncode != 0: return
            branch = res.stdout.strip()

            if branch != "HEAD":
                config.set("last_branch", branch)

            # Feature only for 'main' branch
            if branch == "main":
                # Find stable tags (v0, v1, v241431...) - strictly 'v' + digits
                res_tags = self._git_run(["tag", "-l"])
                all_tags = [t.strip() for t in res_tags.stdout.split('\n') if t.strip()]
                
                # Filter tags that match ^v\d+$
                stable_tags = [t for t in all_tags if re.match(r"^v\d+$", t)]
                
                # Numeric sort: v10 > v2
                stable_tags.sort(key=lambda x: int(x[1:]), reverse=True)
                latest_stable = stable_tags[0] if stable_tags else None

                # Latest commit on origin/main
                res_latest = self._git_run(["rev-parse", "origin/main"])
                latest_commit = res_latest.stdout.strip() if res_latest and res_latest.returncode == 0 else None
                
                # Current commit
                res_current = self._git_run(["rev-parse", "HEAD"])
                current_commit = res_current.stdout.strip()

                if latest_commit and current_commit != latest_commit:
                    console.print(f"[bold cyan]🚀 Update available! You are behind origin/main.[/bold cyan]")
                    
                    if latest_stable:
                        console.print(f"Latest: [green]{latest_commit[:7]}[/green] | Stable: [green]{latest_stable}[/green]")
                        console.print("Would you like to update to the stable version? If so, select 's' (stable).")
                        choice = self.session.prompt("Update now? (y/n/s): ").lower().strip()
                    else:
                        console.print("[yellow]Note: No stable version found.[/yellow]")
                        choice = self.session.prompt("Update now? (y/n): ").lower().strip()
                    
                    if choice == 'y':
                        console.print("[yellow]Updating to latest...[/yellow]")
                        self._checkout_and_sync("main", pull=True)
                    elif choice == 's' and latest_stable:
                        console.print(f"[yellow]Updating to stable {latest_stable}...[/yellow]")
                        self._checkout_and_sync(latest_stable)
                elif not silent:
                    console.print("[green]You are on the latest version.[/green]")
                return

            # Logic for other branches or detached HEAD
            if branch == "HEAD":
                # We are in detached HEAD
                last_branch = config.get("last_branch") or "main"
                upstream = f"origin/{last_branch}"
                
                # Check if this branch actually contains current HEAD to be sure
                res_check = self._git_run(["branch", "-r", "--contains", "HEAD"])
                contained_remotes = res_check.stdout.split("\n") if res_check else []
                contained_remotes = [b.strip().replace("remotes/", "") for b in contained_remotes if "origin/" in b and "HEAD" not in b]
                
                if upstream not in contained_remotes and contained_remotes:
                    # If last_branch doesn't contain us, fallback to first remote containing us
                    upstream = contained_remotes[0]
                elif not contained_remotes:
                    upstream = f"origin/{last_branch}" # fallback
            else:
                res = self._git_run(["rev-parse", "--abbrev-ref", f"{branch}@{{u}}"])
                upstream = res.stdout.strip() if res.returncode == 0 else f"origin/{branch}"

            # Compare
            res = self._git_run(["rev-list", "--count", f"HEAD..{upstream}"])
            if not res or res.returncode != 0: return
            
            behind = int(res.stdout.strip() or 0)

            if behind > 0:
                console.print(f"[bold cyan]🚀 Update available! You are behind {upstream} by {behind} commit(s).[/bold cyan]")
                if self.session.prompt("Update now? (y/n): ").lower().strip() == 'y':
                    console.print("[yellow]Updating...[/yellow]")
                    target_branch = upstream.split("/")[-1] if branch == "HEAD" else branch
                    self._checkout_and_sync(target_branch, pull=True)
            elif not silent:
                console.print(f"[green]You are on the latest version (relative to {upstream}).[/green]")

        elif sub == "branch":
            self._git_run(["fetch", "--all"])
            res = self._git_run(["branch", "-r"])
            if not res or res.returncode != 0: return
            branches = [b.strip() for b in res.stdout.split('\n') if b.strip() and '->' not in b]
            
            t = Table(title="Remote Branches", box=box.ROUNDED)
            t.add_column("Idx", style="dim"); t.add_column("Branch Name", style="bold green")
            for i, b in enumerate(branches, 1): t.add_row(str(i), b)
            console.print(t)
            
            idx = self.session.prompt("\nSelect branch index (or 'q' to quit): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(branches):
                full_branch = branches[int(idx)-1]
                target = full_branch.replace("origin/", "", 1)
                
                check_local = self._git_run(["rev-parse", "--verify", target])
                if check_local.returncode == 0:
                    self._checkout_and_sync(target, pull=True)
                else:
                    console.print(f"[yellow]Creating tracking branch {target}...[/yellow]")
                    self._git_run(["checkout", "-b", target, full_branch], capture=False)
                    self._sync_deps(force=True)
                    sys.exit(0)

        elif sub == "tag":
            self._git_run(["fetch", "--tags"])
            res = self._git_run(["tag", "-l", "--sort=-v:refname"])
            if not res or res.returncode != 0: return
            tags = [t.strip() for t in res.stdout.split('\n') if t.strip()]
            
            if not tags:
                console.print("[yellow]No tags found.[/yellow]")
                return

            t = Table(title="Recent Tags", box=box.ROUNDED)
            t.add_column("Idx", style="dim"); t.add_column("Tag Name", style="bold green")
            for i, tag in enumerate(tags[:20], 1): t.add_row(str(i), tag)
            console.print(t)
            
            idx = self.session.prompt("\nSelect tag index (or 'q' to quit): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(tags):
                self._checkout_and_sync(tags[int(idx)-1])

        elif sub == "commit":
            self._git_run(["fetch", "--all"])
            res = self._git_run(["log", "--all", "-n", "30", "--pretty=format:%h|%ad|%an|%s|%d", "--date=short"])
            if not res or res.returncode != 0: return
            lines = res.stdout.split('\n')
            
            t = Table(title="Recent Commits (All Branches)", box=box.ROUNDED)
            t.add_column("Idx", style="dim"); t.add_column("Hash", style="cyan")
            t.add_column("Date", style="dim"); t.add_column("Subject", style="bold green")
            t.add_column("Refs", style="yellow")
            
            commits = []
            for i, line in enumerate(lines, 1):
                parts = line.split('|')
                if len(parts) >= 4:
                    h, date, author, subj = parts[:4]
                    refs = parts[4] if len(parts) > 4 else ""
                    commits.append(h)
                    t.add_row(str(i), h, date, subj, refs)
            console.print(t)
            
            idx = self.session.prompt("\nSelect commit index or enter hash (or 'q'): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(commits):
                self._checkout_and_sync(commits[int(idx)-1])
            elif len(idx) >= 7:
                self._checkout_and_sync(idx)

        else:
            self._checkout_and_sync(sub)

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
                elif cmd == 'update': self.cmd_update(arg)
                elif cmd == 'config': self.cmd_config(arg)
                elif cmd == 'check': self.cmd_check()
                elif cmd == 'tables': self.cmd_tables()
                elif cmd == 'query': self.cmd_query(arg)
                elif cmd == 'clear': 
                    os.system('cls' if os.name == 'nt' else 'clear')
                    console.print(self.get_banner())
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
