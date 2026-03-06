# -*- coding: utf-8 -*-
import os
import sys
import re
import subprocess
import shutil
from rich.console import Console

from ..config.manager import config, PROJECT_ROOT, SMALL_SCREEN_WIDTH, VERSION
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
            else: 
                # Для Termux/Linux используем -e для корректной работы путей
                cmd += ["-e", PROJECT_ROOT, "--upgrade", "--quiet"]

            res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
            if res.returncode == 0: 
                console.print("[green]✅ Dependencies synchronized.[/green]")
            else: 
                console.print(f"[red]❌ Sync failed. Try running manually:[/red]")
                console.print(f"[bold white]{' '.join(cmd).replace('--quiet', '')}[/bold white]")
        except Exception as e: console.print(f"[red]Error syncing deps: {e}[/red]")

    def _checkout_and_sync(self, target: str, pull: bool = False):
        console.print(f"[yellow]Forcing checkout to {target}...[/yellow]")

        # Если pull=True, значит target — это имя ветки (напр. "main" или "FIX")
        if pull:
            self._git_run(["fetch", "origin", target, "--tags", "--force"])
            ref = f"origin/{target}"
        else:
            # Если pull=False, target — это либо тег, либо хеш, либо уже полный ref
            ref = target

        res = self._git_run(["reset", "--hard", ref])
        if res and res.returncode == 0:
            # Очистка перед синхронизацией
            for p in ["build", ".build", "dist", "vortex_cli.egg-info"]:
                shutil.rmtree(os.path.join(PROJECT_ROOT, p), ignore_errors=True)

            self._sync_deps(force=True)
            console.print("[bold green]✅ Updated successfully![/bold green]")
            # Вместо жесткого exit, даем системе завершить цикл если нужно, 
            # но в данном контексте перезапуск обычно необходим.
            sys.exit(0)
        else:
            console.print(f"[red]❌ Failed to reset to {ref}[/red]")

    def cmd_update(self, args: str = "", silent=False):
        parts = args.split()
        sub = parts[0].lower() if parts else "check"
        if not silent or sub != "check": console.print("[yellow]Syncing remote...[/yellow]")
        self._git_run(["fetch", "--all", "--tags", "--force", "--quiet"])

        if sub == "check":
            # 1. Определяем текущую ветки
            res_branch = self._git_run(["rev-parse", "--abbrev-ref", "HEAD"])
            if not res_branch or res_branch.returncode != 0: return
            branch = res_branch.stdout.strip()

            # Если мы в detached HEAD, не предлагаем обновление ветки, только теги
            is_detached = (branch == "HEAD")

            # 2. Ищем апстрим только если мы на ветке
            branch_update = False
            upstream = None
            if not is_detached:
                res_u = self._git_run(["rev-parse", "--abbrev-ref", f"{branch}@{{u}}"])
                upstream = res_u.stdout.strip() if res_u.returncode == 0 else f"origin/{branch}"

                # Проверяем наличие НОВЫХ коммитов в апстриме
                res_up_count = self._git_run(["rev-list", "--count", f"HEAD..{upstream}"])
                branch_update = (res_up_count and res_up_count.returncode == 0 and int(res_up_count.stdout.strip()) > 0)

            # 3. Работа с тегами (только для main)
            latest_tag = None
            tag_update = False
            if branch == "main":
                res_tags = self._git_run(["tag", "-l", "--sort=-v:refname", "v*"])
                tags = [t.strip() for t in res_tags.stdout.split('\n') if t.strip()]
                if tags:
                    latest_tag = tags[0]
                    # Проверяем, есть ли в теге коммиты, которых нет в HEAD
                    res_tag_count = self._git_run(["rev-list", "--count", f"HEAD..{latest_tag}"])
                    tag_update = (res_tag_count and res_tag_count.returncode == 0 and int(res_tag_count.stdout.strip()) > 0)

            # 4. Логика вывода
            if branch_update or tag_update:
                if not is_detached:
                    status_branch = "[green]Latest[/green]" if not branch_update else f"[bold cyan]Update available ({upstream})[/bold cyan]"
                    console.print(f"Branch [bold cyan]{branch}[/bold cyan]: {status_branch}")

                if branch == "main" and latest_tag:
                    status_tag = "[green]Current[/green]" if not tag_update else f"[bold magenta]New stable available ({latest_tag})[/bold magenta]"
                    console.print(f"Stable [bold magenta]{latest_tag}[/bold magenta]: {status_tag}")

                opts = []
                if branch_update: opts.append("y (branch)")
                if branch == "main" and tag_update: opts.append("s (stable)")
                opts.append("n (skip)")

                choice = self.session.prompt(f"Update now? ({'/'.join(o[0] for o in opts)}): ").lower().strip()

                if choice == 'y' and branch_update:
                    self._checkout_and_sync(branch, pull=True)
                elif choice == 's' and tag_update:
                    self._checkout_and_sync(latest_tag)
            elif not silent:
                console.print(f"[green]✅ You are on the latest version of {branch}.[/green]")
            return

        elif sub == "branch":
            res = self._git_run(["branch", "-r"])
            branches = [{"name": b.strip()} for b in res.stdout.split('\n') if b.strip() and '->' not in b]
            sel = pager(branches, "Remote Branches", [{"name": "Branch", "key": "name", "style": "bold green"}], page_size=5)
            if sel:
                target = sel['name'].replace("origin/", "", 1)
                self._checkout_and_sync(target, pull=True)

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
                if len(p) >= 4:
                    commits.append({
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
                
                # Занятое место: Idx(4) + Hash(7) + Date(10) + Refs(??) + Borders(~10)
                occupied = 21 
                if width >= 100: occupied += 11 # Дата
                if width >= 120: occupied += len(item.get('refs', '')) + 2
                
                # Если экран мал ИЛИ строка целиком не влезает
                if width < SMALL_SCREEN_WIDTH or (occupied + len(val)) > width:
                    return f"[bold white]{ver}[/bold white]"
                
                return f"[bold white]{ver}[/bold white] {rest}" if rest else f"[bold white]{ver}[/bold white]"

            sel = pager(commits, "Recent Commits", [
                {"name": "Hash", "key": "hash", "style": "cyan"},
                {"name": "Date", "key": "date", "style": "dim", "min_width": 100},
                {"name": "Subject", "key": "subj", "render": subj_render},
                {"name": "Refs", "key": "refs", "style": "yellow", "min_width": 120}
            ], page_size=5)
            if sel: self._checkout_and_sync(sel['hash'])
        else: self._checkout_and_sync(sub)

