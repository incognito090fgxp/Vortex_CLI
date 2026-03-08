# -*- coding: utf-8 -*-
import os
import sys
import re
import subprocess
import shutil
from rich.console import Console

from ..config.manager import config, PROJECT_ROOT, EGG_INFO_DIR, SMALL_SCREEN_WIDTH, VERSION
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

    def _should_check_dep(self, dep_str: str):
        """Basic check if dependency applies to current platform based on markers."""
        if ";" not in dep_str: return True
        try:
            name, marker = dep_str.split(";", 1)
            marker = marker.lower().strip()
            is_win = sys.platform == 'win32'
            
            # Simple marker evaluation for known markers used in the project
            if "sys_platform" in marker:
                if "=='win32'" in marker.replace(" ", ""): return is_win
                if "!='win32'" in marker.replace(" ", ""): return not is_win
            
            if "python_version" in marker:
                match = re.search(r"python_version\s*<\s*['\"]([\d\.]+)['\"]", marker)
                if match:
                    req_ver = tuple(map(int, match.group(1).split('.')))
                    return sys.version_info[:len(req_ver)] < req_ver
        except:
            pass
        return True # Default to True to be safe

    def _sync_deps(self, force=False):
        console.print("[yellow]Checking & Syncing dependencies...[/yellow]")
        required = self._get_required_deps()
        installed = self._get_installed_deps()
        
        # Filter dependencies that actually apply to this platform
        active_required = [d for d in required if self._should_check_dep(d)]
        
        # Check if anything is missing from the active set
        missing = []
        for dep in active_required:
            name = re.split('[;<>!=]', dep)[0].strip().lower()
            if name not in installed:
                missing.append(dep)

        if not missing and not force:
            console.print("[green]✅ Dependencies already satisfied.[/green]")
            return

        try:
            # Clean both root and .vortex_data egg-info
            shutil.rmtree(EGG_INFO_DIR, ignore_errors=True)
            for p in ["build", ".build", "vortex_cli.egg-info"]:
                shutil.rmtree(os.path.join(PROJECT_ROOT, p), ignore_errors=True)

            cmd = [sys.executable, "-m", "pip", "install"]
            if os.name == 'nt': 
                # On Windows, we can pass active required deps directly
                cmd += active_required + ["--quiet"]
            else: 
                # Для Termux/Linux используем -e для корректной работы путей
                # Pip сам поймет маркеры из pyproject.toml
                cmd += ["-e", PROJECT_ROOT, "--upgrade", "--quiet"]

            res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
            if res.returncode == 0: 
                # If egg-info appeared in root, try to move it to .vortex_data
                root_egg = os.path.join(PROJECT_ROOT, "vortex_cli.egg-info")
                if os.path.exists(root_egg) and not os.path.exists(EGG_INFO_DIR):
                    try: shutil.move(root_egg, EGG_INFO_DIR)
                    except: pass
                console.print("[green]✅ Dependencies synchronized.[/green]")
            else: 
                console.print(f"[red]❌ Sync failed. Try running manually:[/red]")
                console.print(f"[bold white]{' '.join(cmd).replace('--quiet', '')}[/bold white]")
        except Exception as e: console.print(f"[red]Error syncing deps: {e}[/red]")

    def _checkout_and_sync(self, target: str, pull: bool = False):
        console.print(f"[yellow]Forcing checkout to {target}...[/yellow]")

        if pull:
            # Обновление ветки: остаемся на ветке
            self._git_run(["fetch", "origin", target, "--tags", "--force"])
            self._git_run(["checkout", "-B", target, f"origin/{target}"])
            ref = f"origin/{target}"
        else:
            # Прыжок на коммит или тег: уходим в Detached HEAD (без лишних веток)
            if target.startswith('v'):
                self._git_run(["fetch", "origin", f"refs/tags/{target}:refs/tags/{target}", "--force"])
            self._git_run(["checkout", "--detach", target])
            ref = target

        res = self._git_run(["reset", "--hard", ref])
        if res and res.returncode == 0:
            shutil.rmtree(EGG_INFO_DIR, ignore_errors=True)
            for p in ["build", ".build", "dist", "vortex_cli.egg-info"]:
                shutil.rmtree(os.path.join(PROJECT_ROOT, p), ignore_errors=True)
            self._sync_deps(force=True)
            console.print("[bold green]✅ Updated successfully![/bold green]")
            sys.exit(0)
        else:
            console.print(f"[red]❌ Failed to reset to {ref}[/red]")

    def cmd_update(self, args: str = "", silent=False):
        parts = args.split()
        sub = parts[0].lower() if parts else "check"
        
        # 0. Синхронизируем метаданные
        if not silent: console.print("[yellow]Syncing with GitHub...[/yellow]")
        self._git_run(["fetch", "--prune", "origin", "--quiet"])

        # 1. Получаем ПРЯМУЮ информацию от GitHub (хэши голов)
        if not silent or sub != "check": console.print("[yellow]Querying GitHub for latest refs...[/yellow]")
        res_remote = self._git_run(["ls-remote", "--heads", "--tags", "origin"])
        if not res_remote or res_remote.returncode != 0:
            if not silent: console.print("[red]❌ Failed to query remote. Check connection.[/red]")
            return

        remote_refs = {} # {ref_name: hash}
        for line in res_remote.stdout.split('\n'):
            if not line.strip(): continue
            h, ref = line.split('\t')
            name = ref.replace("refs/heads/", "").replace("refs/tags/", "")
            if name.endswith("^{}"): remote_refs[name[:-3]] = h
            elif name not in remote_refs: remote_refs[name] = h

        # 2. Локальное состояние
        res_head = self._git_run(["rev-parse", "HEAD"])
        local_hash = res_head.stdout.strip() if res_head else ""
        res_branch = self._git_run(["rev-parse", "--abbrev-ref", "HEAD"])
        local_branch = res_branch.stdout.strip() if res_branch else "HEAD"
        is_detached = (local_branch == "HEAD")

        if sub == "check":
            # 3. Детекция текущего положения (в какой ветке наш коммит?)
            tracking_branch = None
            if not is_detached and local_branch in remote_refs:
                tracking_branch = local_branch
            else:
                # Если мы отсоединены, ищем ветку-кандидата (FIX или main)
                res_cont = self._git_run(["branch", "-r", "--contains", local_hash])
                if res_cont and res_cont.returncode == 0:
                    contained_in = [b.strip().replace("origin/", "") for b in res_cont.stdout.split('\n') if b.strip()]
                    for b in ["FIX", "main"]:
                        if b in contained_in:
                            tracking_branch = b
                            break

            # 4. Логика уведомлений
            branch_update = False
            tag_update = False
            target_branch = tracking_branch or "main"

            # Branch mismatch: если мы на ветке, но её код совпадает с другой "головой"
            if not is_detached:
                for name, h in remote_refs.items():
                    if h == local_hash and name != local_branch and not name.startswith('v'):
                        console.print(f"[yellow]⚠ Branch mismatch![/yellow] Your code matches [bold cyan]{name}[/bold cyan], but you are on [red]{local_branch}[/red].")
                        if self.session.prompt(f"Switch to [bold cyan]{name}[/bold cyan]? (y/n): ").lower() == 'y':
                            self._checkout_and_sync(name, pull=True)
                            return
                        break

            # Проверка обновлений для ветки
            if target_branch in remote_refs:
                remote_hash = remote_refs[target_branch]
                if local_hash != remote_hash:
                    # Считаем разницу через локальные метаданные
                    res_behind = self._git_run(["rev-list", "--count", f"HEAD..origin/{target_branch}"])
                    behind = int(res_behind.stdout.strip()) if res_behind and res_behind.returncode == 0 else 0
                    branch_update = (behind > 0)

                    if branch_update:
                        console.print(f"Branch [bold cyan]{target_branch}[/bold cyan] ({local_hash[:7]}): [bold cyan]Update available[/bold cyan] ([red]-{behind}[/red] commits)")

            # Проверка тегов
            tags = sorted([t for t in remote_refs.keys() if t.startswith('v')], reverse=True)
            latest_tag = tags[0] if tags else None
            if latest_tag:
                tag_hash = remote_refs[latest_tag]
                if local_hash != tag_hash:
                    res_tag_behind = self._git_run(["rev-list", "--count", f"HEAD..{latest_tag}"])
                    tag_behind = int(res_tag_behind.stdout.strip()) if res_tag_behind and res_tag_behind.returncode == 0 else 0
                    tag_update = (tag_behind > 0)

                    if tag_update:
                        console.print(f"Stable [bold magenta]{latest_tag}[/bold magenta]: [bold magenta]New stable available[/bold magenta]")

            # 5. Меню обновления
            if branch_update or tag_update:
                opts = []
                if branch_update: opts.append(f"y (update {target_branch})")
                if tag_update: opts.append(f"s (switch to {latest_tag})")
                opts.append("n (skip)")
                choice = self.session.prompt(f"Update now? ({'/'.join(o[0] for o in opts)}): ").lower().strip()
                if choice == 'y' and branch_update: self._checkout_and_sync(target_branch, pull=True)
                elif choice == 's' and tag_update: self._checkout_and_sync(latest_tag)
            elif not silent:
                info = f"of {local_branch}" if not is_detached else f"at {local_hash[:7]}"
                if tracking_branch and is_detached: info += f" (on {tracking_branch} track)"
                console.print(f"[green]✅ You are on the latest version {info}.[/green]")
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
            # Берем логи ТОЛЬКО из origin, чтобы не видеть локальный мусор
            res = self._git_run(["log", "origin/main", "origin/FIX", "-n", "100", "--pretty=format:%h|%ad|%an|%s|%d", "--date=short"])
            if not res or not res.stdout.strip():
                res = self._git_run(["log", "--all", "-n", "100", "--pretty=format:%h|%ad|%an|%s|%d", "--date=short"])
            
            commits = []
            for line in res.stdout.split('\n'):
                p = line.split('|')
                if len(p) >= 4:
                    commits.append({"hash": p[0], "date": p[1], "author": p[2], "subj": p[3], "refs": p[4] if len(p) > 4 else ""})

            def subj_render(val, item, width):
                parts = val.split(' ', 1)
                ver = parts[0]
                rest = parts[1] if len(parts) > 1 else ""
                occupied = 21 
                if width >= 100: occupied += 11 
                if width >= 120: occupied += len(item.get('refs', '')) + 2
                if width < SMALL_SCREEN_WIDTH or (occupied + len(val)) > width: return f"[bold white]{ver}[/bold white]"
                return f"[bold white]{ver}[/bold white] {rest}" if rest else f"[bold white]{ver}[/bold white]"

            sel = pager(commits, "Recent Commits", [
                {"name": "Hash", "key": "hash", "style": "cyan"},
                {"name": "Date", "key": "date", "style": "dim", "min_width": 100},
                {"name": "Subject", "key": "subj", "render": subj_render},
                {"name": "Refs", "key": "refs", "style": "yellow", "min_width": 120}
            ], page_size=5)
            if sel: self._checkout_and_sync(sel['hash'])
        else: self._checkout_and_sync(sub)
