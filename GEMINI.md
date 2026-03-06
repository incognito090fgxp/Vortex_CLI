# Vortex CLI Development Guide (Updated)

## 🏗 Modular Architecture & Development Mandates
**CRITICAL**: Follow `MODULES_GUIDE.md` (root directory) strictly for any component creation or movement.

- **Registry First**: Every new file or module MUST be registered in `vortex/registry.py`.
- **Documentation**: Update `vortex/info.txt` after any architectural changes. This file is the primary guide for system module responsibilities.
- **UI Engine**: Always use `vortex.ui.engine` for interactive tables or lists. Do not write UI logic in core modules.
- **Environment**: Protect `.env` and never commit database credentials.

## 📂 System File Map (Internal Reference)
- `vortex/registry.py`: Central source of truth for all project paths and module names.
- `vortex/info.txt`: High-level architectural overview and module responsibilities.
- `vortex/config/manager.py`: Global configuration, VERSION constant, and settings persistence.
- `.vortex_data/`: **[NEW]** Centralized storage for history and local settings.
- `vortex/core/cli.py`: Main REPL loop and command orchestration.
- `vortex/database/`: **[MODULAR]**
    - `db.py`: Unified entry point (Orchestrator).
    - `core.py`: Database engine and connection manager.
    - `explorer.py`: Table navigation hub.
    - `schema.py`: Table structure and column management.
    - `browser.py`: Row-level data browser.
    - `console.py`: Isolated SQL REPL with private history.
    - `README.md`: Detailed manual for the Database module.
- `vortex/ui/engine/core.py`: Universal Interactive Pager (VUE) implementation.

## 📌 Versioning System (PEP 440)
We use a 4-digit versioning scheme: **Release.Beta.DEV.FIX** (e.g., `0.3.1.8`)

## 🌍 Cross-Platform Compatibility (MANDATORY)
**CRITICAL**: When modifying the codebase, you MUST ensure compatibility across Windows, Linux, macOS, and Termux (Android).

1.  **Lazy Loading**: Never import heavy dependencies at the top level of `vortex/__init__.py`.
2.  **Binary Dependencies**: Avoid `[binary]` suffixes for libraries in `pyproject.toml`.
3.  **Path Handling**: Always use `os.path.join` and reference paths via `vortex.registry`.
4.  **Database Efficiency**: Always use `psycopg.rows.dict_row`.
5.  **Destructive Safety**: All destructive operations (DROP, TRUNCATE) MUST implement a mandatory `yes` confirmation prompt.

## 📟 Interactive Pager System (`_pager`)
- **Alternate Screen Buffer**: Uses `console.screen()` to provide a "clean window" experience.
- **Keyboard Navigation**: Supports Arrow keys and fast numeric input.
- **Adaptive Rendering**: Supports dynamic content truncation based on terminal width.

## 🔄 Git-based Update Protocol
- **Ahead/Behind Validation**: Before suggesting an update, the system MUST verify that the remote ref contains new commits not present in the local HEAD using `git rev-list --count HEAD..upstream`.
- **Downgrade Protection**: If the local branch is ahead of the remote, or if they have diverged but the remote has no unique commits, no update should be offered.
- **Tag Policy**: Stable version updates (tags) are only offered to users on the `main` branch and only if the tag points to a commit ahead of the current HEAD.
