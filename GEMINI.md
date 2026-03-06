# Vortex CLI Development Guide (Updated)

## 🏗 Modular Architecture & Development Mandates
**CRITICAL**: Follow `MODULES_GUIDE.md` (root directory) strictly for any component creation or movement.

- **Registry First**: Every new file or module MUST be registered in `vortex/registry.py`.
- **Documentation**: Update `vortex/info.txt` after any architectural changes.
- **UI Engine**: Always use `vortex.ui.engine` for interactive tables or lists. Do not write UI logic in core modules.
- **Environment**: Protect `.env` and never commit database credentials.

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
- **Dynamic Detection**: Automatically identifies the current branch and its upstream; no hardcoded branch names.
- **Stable Tags**: On the `main` branch, the system tracks the latest `v*` tags. Users on `main` are offered a "Stable" update option (`s`) if a newer tag is available.
- **Cleanup**: Proactively removes `build/`, `.build/`, and `*.egg-info` to fix `egg_base` errors.
- **Shadowing Check**: Be aware that a `vortex.py` launcher exists in the root; it is designed not to shadow the package via absolute imports.

## 📟 Interactive Pager System (`_pager`)
- **Alternate Screen Buffer**: Uses `console.screen()` to provide a "clean window" experience (like `vim`/`less`), restoring the previous terminal content upon exit.
- **Keyboard Navigation**: Supports Arrow keys (↑/↓ for selection, ←/→ for paging), `Enter` for confirmation, and `Esc`/`q` for cancellation.
- **Hybrid Input**: Supports both direct digit input (typing index + Enter) and visual cursor-based selection.

## 📂 Key Pathing (`PROJECT_ROOT`)
- Always use `vortex.registry` as the single source of truth for all file paths.

## 🎨 UI Standards & Adaptive Display
- **Small Screens**: Use `SMALL_SCREEN_WIDTH` from `vortex.config.manager` (default: 65) to toggle between full and compact UI (e.g., in banners and tables).
- **Commit Formatting**: In commit lists, the version (the first word of the subject) must be highlighted using `[bold white]`. 
- **Dynamic Truncation**: If a table row's estimated width exceeds the current terminal width, automatically truncate the commit subject to the version only to maintain table integrity.
