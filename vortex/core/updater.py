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

    def _check_shadowing(self):
        """Check for vortex.py in the root which might shadow the package."""
        shadow = os.path.join(PROJECT_ROOT, "vortex.py")
        if os.path.exists(shadow):
            console.print(f"\n[bold red]CRITICAL:[/bold red] Found [cyan]vortex.py[/cyan] in project root.")
            console.print("[yellow]This file prevents the CLI from running correctly. Please rename or delete it.[/yellow]")
            return True
        return False

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
                # Use --no-deps if needed, but normally we want dependencies
                cmd = [sys.executable, "-m", "pip", "install", "-e", PROJECT_ROOT, "--upgrade", "--quiet"]

            res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
            if res.returncode == 0:
                console.print("[green]✅ Dependencies and Core synchronized.[/green]")
            else:
                console.print(f"[red]❌ Dependency sync failed.[/red]")
                console.print(f"[dim]{res.stderr}[/dim]")
                # If editable install fails, fallback to normal install of dependencies
                if not os.name == 'nt':
                    console.print("[yellow]Retrying with simple dependency install...[/yellow]")
                    subprocess.run([sys.executable, "-m", "pip", "install"] + required + ["--quiet"], cwd=PROJECT_ROOT)
        except Exception as e:
            console.print(f"[red]Error syncing deps: {e}[/red]")

    def _checkout_and_sync(self, target: str, pull: bool = False):
        console.print(f"[yellow]Forcing checkout to {target}...[/yellow]")
        
        # Ensure we are not tracking a local branch that diverged
        if pull:
            self._git_run(["fetch", "origin", target])
            target_ref = f"origin/{target}"
        else:
            target_ref = target

        # FORCE RESET TO REMOTE state instead of pull to avoid reconciliation issues
        res = self._git_run(["reset", "--hard", target_ref], capture=True)
        
        if res and res.returncode == 0:
            # CLEANUP BUILD CACHE
            console.print("[yellow]Cleaning build artifacts...[/yellow]")
            for p in ["build", ".build", "dist", "vortex_cli.egg-info"]:
                path = os.path.join(PROJECT_ROOT, p)
                if os.path.exists(path): shutil.rmtree(path, ignore_errors=True)
            
            self._sync_deps(force=True)
            self._check_shadowing()
            console.print("[bold green]✅ Updated successfully![/bold green]")
            sys.exit(0)
        else:
            # Fallback to checkout if reset failed (might be a tag)
            res = self._git_run(["checkout", "-f", target], capture=True)
            if res and res.returncode == 0:
                self._sync_deps(force=True)
                self._check_shadowing()
                console.print("[bold green]✅ Updated successfully (via checkout)![/bold green]")
                sys.exit(0)
            else:
                console.print(f"[red]❌ Update failed for {target}[/red]")
                if res: console.print(f"[dim]{res.stderr}[/dim]")

    def cmd_update(self, args: str = "", silent=False):
        parts = args.split()
        sub = parts[0].lower() if parts else "check"
        
        if self._check_shadowing() and not silent:
            console.print("[yellow]Please fix the shadowing issue before updating.[/yellow]")

        if sub == "check":
            if not silent: console.print("[yellow]Checking for updates...[/yellow]")
            self._git_run(["fetch", "--all", "--tags", "--quiet"])
            
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
            self._git_run(["fetch", "--all"])
            res_b = self._git_run(["branch", "-r"])
            if not res_b or res_b.returncode != 0: return
            branches = [b.strip() for b in res_b.stdout.split('\n') if b.strip() and '->' not in b]
            
            t = Table(title="Remote Branches", box=box.ROUNDED)
            t.add_column("Idx", style="dim"); t.add_column("Branch Name", style="bold green")
            for i, b in enumerate(branches, 1): t.add_row(str(i), b)
            console.print(t)
            
            idx = self.session.prompt("\nSelect branch index (or 'q' to quit): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(branches):
                full = branches[int(idx)-1]
                target = full.replace("origin/", "", 1)
                if self._git_run(["rev-parse", "--verify", target]).returncode == 0:
                    self._checkout_and_sync(target, pull=True)
                else:
                    console.print(f"[yellow]Creating tracking branch {target}...[/yellow]")
                    self._git_run(["checkout", "-b", target, full], capture=False)
                    self._sync_deps(force=True)
                    sys.exit(0)

        elif sub == "tag":
            self._git_run(["fetch", "--tags"])
            res_t = self._git_run(["tag", "-l", "--sort=-v:refname"])
            if not res_t or res_t.returncode != 0: return
            tags = [t.strip() for t in res_t.stdout.split('\n') if t.strip()]
            
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
