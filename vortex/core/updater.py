# -*- coding: utf-8 -*-
import os
import sys
import re
import subprocess
import shutil
import glob
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ..config.manager import config, PROJECT_ROOT

console = Console()

class UpdateManager:
    def __init__(self, session):
        self.session = session

    def _git_run(self, args, capture=True):
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
        import importlib.metadata
        return {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}

    def _get_required_deps(self):
        toml_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        if not os.path.exists(toml_path): return []
        try:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("project", {}).get("dependencies", [])
        except:
            return []

    def _sync_deps(self, force=False):
        console.print("[yellow]Checking & Syncing dependencies...[/yellow]")
        required = self._get_required_deps()
        installed = self._get_installed_deps()

        missing = []
        for dep in required:
            name = re.split('[<>=!]', dep)[0].strip().lower()
            if name not in installed:
                missing.append(dep)

        if not missing and not force:
            console.print("[green]✅ Dependencies already satisfied.[/green]")
            return

        try:
            # CLEANUP BEFORE INSTALL TO AVOID EGG_INFO ERRORS
            for p in ["build", ".build", "vortex_cli.egg-info"]:
                path = os.path.join(PROJECT_ROOT, p)
                if os.path.exists(path): shutil.rmtree(path, ignore_errors=True)

            if os.name == 'nt':
                cmd = [sys.executable, "-m", "pip", "install"] + required + ["--quiet"]
            else:
                cmd = [sys.executable, "-m", "pip", "install", "-e", PROJECT_ROOT, "--upgrade", "--quiet"]

            res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
            if res.returncode == 0:
                console.print("[green]✅ Dependencies and Core synchronized.[/green]")
            else:
                console.print(f"[red]❌ Dependency sync failed.[/red]")
                console.print(f"[dim]{res.stderr}[/dim]")
                if not os.name == 'nt':
                    console.print("[yellow]Retrying with simple dependency install...[/yellow]")
                    subprocess.run([sys.executable, "-m", "pip", "install"] + required + ["--quiet"], cwd=PROJECT_ROOT)
        except Exception as e:
            console.print(f"[red]Error syncing deps: {e}[/red]")

    def _checkout_and_sync(self, target: str, pull: bool = False):
        console.print(f"[yellow]Forcing checkout to {target}...[/yellow]")
        if pull:
            self._git_run(["fetch", "origin", target, "--tags", "--force"])
            target_ref = f"origin/{target}"
        else:
            target_ref = target

        res = self._git_run(["reset", "--hard", target_ref], capture=True)
        if res and res.returncode == 0:
            console.print("[yellow]Cleaning build artifacts...[/yellow]")
            for p in ["build", ".build", "dist", "vortex_cli.egg-info"]:
                path = os.path.join(PROJECT_ROOT, p)
                if os.path.exists(path): shutil.rmtree(path, ignore_errors=True)
            self._sync_deps(force=True)
            console.print("[bold green]✅ Updated successfully![/bold green]")
            sys.exit(0)
        else:
            res = self._git_run(["checkout", "-f", target], capture=True)
            if res and res.returncode == 0:
                self._sync_deps(force=True)
                console.print("[bold green]✅ Updated successfully (via checkout)![/bold green]")
                sys.exit(0)
            else:
                console.print(f"[red]❌ Update failed for {target}[/red]")
                if res: console.print(f"[dim]{res.stderr}[/dim]")

    def _pager(self, items, title, columns, page_size=5):
        """Interactive paginated selector."""
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit import prompt as pk_prompt
        from prompt_toolkit.styles import Style as PStyle

        current_page = 0
        cursor_pos = 0
        total_items = len(items)
        if total_items == 0:
            console.print("[yellow]No items found.[/yellow]")
            return None

        st = PStyle.from_dict({"prompt": "bold cyan"})

        with console.screen():
            while True:
                total_pages = (total_items + page_size - 1) // page_size
                start = current_page * page_size
                end = min(start + page_size, total_items)
                page_items = items[start:end]
                page_count = len(page_items)
                
                if cursor_pos >= page_count: cursor_pos = max(0, page_count - 1)

                console.clear()
                t = Table(title=f"{title} (Page {current_page + 1}/{total_pages})", box=box.ROUNDED)
                t.add_column("Idx", style="dim", width=4)
                for col in columns:
                    t.add_column(col['name'], style=col.get('style', ''))

                for i, item in enumerate(page_items):
                    abs_idx = start + i + 1
                    row_style = "reverse" if i == cursor_pos else ""
                    t.add_row(str(abs_idx), *[str(item.get(c['key'], '')) for c in columns], style=row_style)

                console.print(t)
                nav = [
                    "[bold cyan]↑/↓[/bold cyan]: move", 
                    "[bold cyan]←/→[/bold cyan]: page", 
                    "[bold cyan]Enter[/bold cyan]: select", 
                    "[bold cyan]Esc/q[/bold cyan]: quit"
                ]
                console.print(f"Navigation: {' | '.join(nav)}")

                kb = KeyBindings()
                @kb.add('up')
                def _(event):
                    nonlocal cursor_pos
                    if cursor_pos > 0: cursor_pos -= 1
                    event.app.exit(result=("up", None))
                
                @kb.add('down')
                def _(event):
                    nonlocal cursor_pos
                    if cursor_pos < page_count - 1: cursor_pos += 1
                    event.app.exit(result=("down", None))
                
                @kb.add('left')
                def _(event): event.app.exit(result=("prev", None))
                
                @kb.add('right')
                def _(event): event.app.exit(result=("next", None))
                
                @kb.add('escape')
                @kb.add('q')
                def _(event): event.app.exit(result=("quit", None))

                @kb.add('p')
                def _(event): event.app.exit(result=("prev", None))

                @kb.add('n')
                def _(event): event.app.exit(result=("next", None))
                
                @kb.add('enter')
                def _(event):
                    text = event.app.current_buffer.text.strip()
                    event.app.exit(result=("input", text) if text else ("select", cursor_pos))

                try:
                    res = pk_prompt("Enter index or command: ", key_bindings=kb, style=st)
                    if not res: continue
                    action, value = res
                except (KeyboardInterrupt, EOFError): return None

                if action == "quit": return None
                elif action == "prev":
                    if current_page > 0: current_page -= 1; cursor_pos = 0
                elif action == "next":
                    if current_page < total_pages - 1: current_page += 1; cursor_pos = 0
                elif action == "select":
                    return page_items[value]
                elif action == "input":
                    if value == 'q': return None
                    elif value == 'p' and current_page > 0: current_page -= 1; cursor_pos = 0
                    elif value == 'n' and current_page < total_pages - 1: current_page += 1; cursor_pos = 0
                    elif value.isdigit():
                        idx = int(value)
                        if 1 <= idx <= total_items: return items[idx-1]
                        else: console.print(f"[red]Invalid index: {idx}[/red]")

    def cmd_update(self, args: str = "", silent=False):
        parts = args.split()
        sub = parts[0].lower() if parts else "check"

        if not silent or sub != "check":
            console.print("[yellow]Syncing with remote...[/yellow]")
        self._git_run(["fetch", "--all", "--tags", "--force", "--quiet"])

        if sub == "check":
            res = self._git_run(["rev-parse", "--abbrev-ref", "HEAD"])
            if not res or res.returncode != 0: return
            branch = res.stdout.strip()
            if branch != "HEAD": config.set("last_branch", branch)

            if branch == "main" or branch == "FIX":
                res_tags = self._git_run(["tag", "-l"])
                stable_tags = [t.strip() for t in res_tags.stdout.split('\n') if re.match(r"^v\d+$", t.strip())]
                stable_tags.sort(key=lambda x: int(x[1:]), reverse=True)
                latest_stable = stable_tags[0] if stable_tags else None

                upstream = f"origin/{branch}"
                res_latest = self._git_run(["rev-parse", upstream])
                latest_commit = res_latest.stdout.strip() if res_latest and res_latest.returncode == 0 else None
                current_commit = self._git_run(["rev-parse", "HEAD"]).stdout.strip()

                if latest_commit and current_commit != latest_commit:
                    console.print(f"[bold cyan]🚀 Update available! You are behind {upstream}.[/bold cyan]")
                    if latest_stable:
                        console.print(f"Latest: [green]{latest_commit[:7]}[/green] | Stable: [green]{latest_stable}[/green]")
                        choice = self.session.prompt("Update now? (y/n/s): ").lower().strip()
                    else:
                        choice = self.session.prompt("Update now? (y/n): ").lower().strip()

                    if choice == 'y': self._checkout_and_sync(branch, pull=True)
                    elif choice == 's' and latest_stable: self._checkout_and_sync(latest_stable)
                elif not silent: console.print("[green]You are on the latest version.[/green]")
                return

            if branch == "HEAD":
                last_branch = config.get("last_branch") or "main"
                upstream = f"origin/{last_branch}"
                res_check = self._git_run(["branch", "-r", "--contains", "HEAD"])
                contained = [b.strip().replace("remotes/", "") for b in res_check.stdout.split("\n") if "origin/" in b and "HEAD" not in b]
                if upstream not in contained and contained: upstream = contained[0]
            else:
                res = self._git_run(["rev-parse", "--abbrev-ref", f"{branch}@{{u}}"])
                upstream = res.stdout.strip() if res.returncode == 0 else f"origin/{branch}"

            res_list = self._git_run(["rev-list", "--count", f"HEAD..{upstream}"])
            if not res_list or res_list.returncode != 0: return
            behind = int(res_list.stdout.strip() or 0)

            if behind > 0:
                console.print(f"[bold cyan]🚀 Update available! You are behind {upstream} by {behind} commit(s).[/bold cyan]")
                if self.session.prompt("Update now? (y/n): ").lower().strip() == 'y':
                    target = upstream.split("/")[-1] if branch == "HEAD" else branch
                    self._checkout_and_sync(target, pull=True)
            elif not silent: console.print(f"[green]You are on the latest version (relative to {upstream}).[/green]")

        elif sub == "branch":
            res_b = self._git_run(["branch", "-r"])
            if not res_b or res_b.returncode != 0: return
            branches = [{"name": b.strip()} for b in res_b.stdout.split('\n') if b.strip() and '->' not in b]
            
            selected = self._pager(branches, "Remote Branches", [{"name": "Branch Name", "key": "name", "style": "bold green"}])
            if selected:
                target = selected['name'].replace("origin/", "", 1)
                if self._git_run(["rev-parse", "--verify", target]).returncode == 0:
                    self._checkout_and_sync(target, pull=True)
                else:
                    console.print(f"[yellow]Creating tracking branch {target}...[/yellow]")
                    self._git_run(["checkout", "-b", target, selected['name']], capture=False)
                    self._sync_deps(force=True)
                    sys.exit(0)

        elif sub == "tag":
            res_t = self._git_run(["tag", "-l", "--sort=-v:refname"])
            if not res_t or res_t.returncode != 0: return
            tags = [{"name": t.strip()} for t in res_t.stdout.split('\n') if t.strip()]
            
            selected = self._pager(tags, "Recent Tags", [{"name": "Tag Name", "key": "name", "style": "bold green"}])
            if selected:
                self._checkout_and_sync(selected['name'])

        elif sub == "commit":
            res = self._git_run(["log", "--all", "-n", "100", "--pretty=format:%h|%ad|%an|%s|%d", "--date=short"])
            if not res or res.returncode != 0: return
            commits = []
            for line in res.stdout.split('\n'):
                parts = line.split('|')
                if len(parts) >= 4:
                    commits.append({
                        "hash": parts[0],
                        "date": parts[1],
                        "subj": parts[3],
                        "refs": parts[4] if len(parts) > 4 else ""
                    })

            selected = self._pager(commits, "Recent Commits", [
                {"name": "Hash", "key": "hash", "style": "cyan"},
                {"name": "Date", "key": "date", "style": "dim"},
                {"name": "Subject", "key": "subj", "style": "bold green"},
                {"name": "Refs", "key": "refs", "style": "yellow"}
            ])
            if selected:
                self._checkout_and_sync(selected['hash'])
        else:
            self._checkout_and_sync(sub)
