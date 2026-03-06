# Vortex CLI Development Guide (Updated)

## 🏗 Modular Architecture & Development Mandates
**CRITICAL**: Follow `MODULES_GUIDE.md` (root directory) strictly for any component creation or movement.

- **Registry First**: Every new file or module MUST be registered in `vortex/registry.py`.
- **Documentation**: Update `vortex/info.txt` after any architectural changes.
- **UI Engine**: Always use `vortex.ui.engine` for interactive tables or lists. Do not write UI logic in core modules.
- **Environment**: Protect `.env` and never commit database credentials.

## 📂 System File Map (Internal Reference)
- `vortex/registry.py`: Central source of truth for all project paths and module names.
- `vortex/config/manager.py`: Global configuration, VERSION constant, and settings persistence.
- `vortex/core/updater.py`: Git-based update logic with dynamic branch/tag detection.
- `vortex/core/cli.py`: Main REPL loop and command orchestration.
- `vortex/ui/engine/core.py`: Universal Interactive Pager (VUE) implementation.
- `vortex/ui/engine/README.md`: API documentation for the UI Engine (`pager` function).
- `vortex/info.txt`: High-level architectural overview and module responsibilities.

## 📌 Versioning System (PEP 440)
We use a 4-digit versioning scheme: **Release.Beta.DEV.FIX** (e.g., `0.3.1.8`)

## 🌍 Cross-Platform Compatibility (MANDATORY)
**CRITICAL**: When modifying the codebase, you MUST ensure compatibility across Windows, Linux, macOS, and Termux (Android).

1.  **Lazy Loading**: Never import heavy dependencies (like `dotenv`, `rich`, `psycopg`) at the top level of `vortex/__init__.py` or `vortex/config/__init__.py`. This breaks the `pip` installation process because dependencies aren't installed yet when `setuptools` tries to read the version.
2.  **Binary Dependencies**: Avoid `[binary]` suffixes for libraries in `pyproject.toml` (e.g., use `psycopg` instead of `psycopg[binary]`) to ensure compatibility with Termux/ARM environments where wheels might not be available.
3.  **Path Handling**: Always use `os.path.join` and reference paths via `vortex.registry` to avoid issues with different slash directions or relative path resolution.
4.  **Entry Points**: Keep `vortex/__init__.py` as a "Lazy Wrapper" to support both legacy installations and clean new builds.

## 🔄 Update & Sync Mechanism (Termux Optimized)
- **Git Strategy**: Uses `git reset --hard` to bypass "divergent branches" errors.
- **Dynamic Detection**: Automatically identifies the current branch and its upstream (e.g., `origin/FIX`). No hardcoded branch names allowed.
- **Stable Tags**: On the `main` branch, users are offered a "Stable" update option (`s`) if a newer `v*` tag commit is detected.
- **Dependency Sync**: Automatically runs `pip install -e .` (Linux/Termux) or standard install (Windows) after updates to sync `pyproject.toml`.
- **Cleanup**: Proactively removes `build/`, `.build/`, and `*.egg-info` to fix `egg_base` errors.

## 📟 Interactive Pager System (`_pager`)
- **Alternate Screen Buffer**: Uses `console.screen()` to provide a "clean window" experience.
- **Keyboard Navigation**: Supports Arrow keys (↑/↓ selection, ←/→ paging) and fast numeric input.
- **Adaptive Rendering**: The `render` callback in `columns` receives `(value, item, current_terminal_width)` for dynamic content truncation.

## 📂 Key Pathing (`PROJECT_ROOT`)
- Always use `vortex.registry` as the single source of truth for all file paths.
