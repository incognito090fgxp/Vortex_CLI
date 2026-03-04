# -*- coding: utf-8 -*-
import os
import sys
import re
import subprocess
import shutil
from rich.console import Console

from ..config.manager import config, PROJECT_ROOT, SMALL_SCREEN_WIDTH
from ..ui.engine import pager

console = Console()

class UpdateManager:
    def __init__(self, session):
        self.session = session

    def _git_run(self, args, capture=True):
        try:
            res = subprocess.run(["git"] + args, capture_output=capture, text=True, cwd=PROJECT_ROOT)
            if res and res.returncode != 0 and capture:
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
        missing = [dep for dep in required if re.split('[<>=!]', dep)[0].strip().lower() not in installed]

        if not missing and not force:
            console.print("[green]✅ Dependencies already satisfied.[/green]")
            return

        try:
            for p in ["build", ".build", "vortex_cli.egg-info"]:
                shutil.rmtree(os.path.join(PROJECT_ROOT, p), ignore_errors=True)

            cmd = [sys.executable, "-m", "pip", "install"]
            if os.name == 'nt': cmd += required + ["--quiet"]
            else: cmd += ["-e", PROJECT_ROOT, "--upgrade", "--quiet"]

            res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
            if res.returncode == 0: console.print("[green]✅ Dependencies synchronized.[/green]")
            else: console.print(f"[red]❌ Sync failed: {res.stderr}[/red]")
        except Exception as e: console.print(f"[red]Error: {e}[/red]")

    def _checkout_and_sync(self, target: str, pull: bool = False):
        console.print(f"[yellow]Forcing checkout to {target}...[/yellow]")
        if pull:
            self._git_run(["fetch", "origin", target, "--tags", "--force"])
            ref = f"origin/{target}"
        else: ref = target

        if self._git_run(["reset", "--hard", ref]).returncode == 0:
            for p in ["build", ".build", "dist", "vortex_cli.egg-info"]:
                shutil.rmtree(os.path.join(PROJECT_ROOT, p), ignore_errors=True)
            self._sync_deps(force=True)
            console.print("[bold green]✅ Updated successfully![/bold green]")
            sys.exit(0)

    def cmd_update(self, args: str = "", silent=False):
        parts = args.split()
        sub = parts[0].lower() if parts else "check"
        if not silent or sub != "check": console.print("[yellow]Syncing remote...[/yellow]")
        self._git_run(["fetch", "--all", "--tags", "--force", "--quiet"])

        if sub == "check":
            res = self._git_run(["rev-parse", "--abbrev-ref", "HEAD"])
            if not res or res.returncode != 0: return
            branch = res.stdout.strip()
            if branch != "HEAD": config.set("last_branch", branch)

            if branch in ("main", "FIX"):
                res_tags = self._git_run(["tag", "-l"])
                tags = sorted([t.strip() for t in res_tags.stdout.split('\n') if re.match(r"^v\d+$", t.strip())], key=lambda x: int(x[1:]), reverse=True)
                stable = tags[0] if tags else None
                latest = self._git_run(["rev-parse", f"origin/{branch}"]).stdout.strip()
                current = self._git_run(["rev-parse", "HEAD"]).stdout.strip()

                if latest and current != latest:
                    console.print(f"[bold cyan]🚀 Update available for {branch}![/bold cyan]")
                    choice = self.session.prompt("Update now? (y/n/s): " if stable else "Update now? (y/n): ").lower().strip()
                    if choice == 'y': self._checkout_and_sync(branch, pull=True)
                    elif choice == 's' and stable: self._checkout_and_sync(stable)
                elif not silent: console.print("[green]Latest version.[/green]")
                return

            res_u = self._git_run(["rev-parse", "--abbrev-ref", f"{branch}@{{u}}"])
            upstream = res_u.stdout.strip() if res_u.returncode == 0 else f"origin/{branch}"
            behind = int(self._git_run(["rev-list", "--count", f"HEAD..{upstream}"]).stdout.strip() or 0)
            if behind > 0:
                console.print(f"[bold cyan]🚀 Update available! Behind {upstream} by {behind} commit(s).[/bold cyan]")
                if self.session.prompt("Update now? (y/n): ").lower().strip() == 'y':
                    self._checkout_and_sync(branch if branch != "HEAD" else upstream.split("/")[-1], pull=True)
            elif not silent: console.print(f"[green]Latest version (relative to {upstream}).[/green]")

        elif sub == "branch":
            res = self._git_run(["branch", "-r"])
            branches = [{"name": b.strip()} for b in res.stdout.split('\n') if b.strip() and '->' not in b]
            sel = pager(branches, "Remote Branches", [{"name": "Branch", "key": "name", "style": "bold green"}], page_size=5)
            if sel:
                target = sel['name'].replace("origin/", "", 1)
                if self._git_run(["rev-parse", "--verify", target]).returncode == 0: self._checkout_and_sync(target, pull=True)
                else:
                    self._git_run(["checkout", "-b", target, sel['name']], capture=False)
                    self._sync_deps(force=True); sys.exit(0)

        elif sub == "tag":
            res = self._git_run(["tag", "-l", "--sort=-v:refname"])
            tags = [{"name": t.strip()} for t in res.stdout.split('\n') if t.strip()]
            sel = pager(tags, "Recent Tags", [{"name": "Tag", "key": "name", "style": "bold green"}], page_size=5)
            if sel: self._checkout_and_sync(sel['name'])

        elif sub == "commit":
            res = self._git_run(["log", "--all", "-n", "100", "--pretty=format:%h|%ad|%an|%s|%d", "--date=short"])
            commits = []
            for line in res.stdout.split('\n'):
                p = line.split('|')
                if len(p) >= 4: commits.append({
                    "hash": p[0], 
                    "date": p[1], 
                    "author": p[2], 
                    "subj": p[3], 
                    "refs": p[4] if len(p) > 4 else ""
                })

            def subj_render(val, item, width):
                parts = val.split(' ', 1)
                ver = parts[0]
                rest = parts[1] if len(parts) > 1 else ""
                
                # Математика для оценки: Idx(4) + Hash(7) + Date(10) + Refs(??) + Borders(~10)
                occupied = 21 
                if width >= 100: occupied += 11 # Date
                if width >= 120: occupied += len(item.get('refs', '')) + 2
                
                est_total = occupied + len(val)
                
                # Если экран мал ИЛИ строка не влезает — краткий вариант
                if width < SMALL_SCREEN_WIDTH or est_total > width:
                    return f"[bold white]{ver}[/bold white]"
                
                # Полный вариант
                return f"[bold white]{ver}[/bold white] {rest}" if rest else f"[bold white]{ver}[/bold white]"

            sel = pager(commits, "Recent Commits", [
                {"name": "Hash", "key": "hash", "style": "cyan"},
                {"name": "Date", "key": "date", "style": "dim", "min_width": 100},
                {"name": "Subject", "key": "subj", "render": subj_render},
                {"name": "Refs", "key": "refs", "style": "yellow", "min_width": 120}
            ], page_size=5)
            if sel: self._checkout_and_sync(sel['hash'])
        else: self._checkout_and_sync(sub)
