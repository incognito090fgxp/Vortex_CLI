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

## 🔄 Git-based Update Protocol (ls-remote)
- **Remote Ground Truth**: The system MUST query GitHub directly via `git ls-remote` for the most accurate branch and tag hashes, bypassing local cache inconsistencies.
- **Direct Hash Verification**: Update checks are performed by comparing the local `HEAD` hash against the remote branch hash. 
- **Branch Mismatch Detection**: If the local code hash matches a specific remote branch (e.g., `FIX`) while the local branch is named differently (e.g., `DEV`), the system MUST offer to switch the branch name to match the code.
- **Pinned State Handling**: When updating to a tag or a specific commit, the system MUST create a local "pinned" branch (e.g., `v0.1.2` or `vtx/a1b2c3d`) to avoid detached HEAD states and ensure clear version reporting.
- **Ahead/Behind Logic**: If hashes differ, `git rev-list --count` is used to determine if the remote is ahead (update available) or the local is ahead (no update offered).
