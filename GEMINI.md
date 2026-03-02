# 🤖 Gemini CLI Mandates for Vortex Project

Foundational rules for maintaining the Vortex ecosystem.

## 🛠 Project Architecture
- **Language**: Python 3.9+
- **Entry Point**: `vortex.py` (exposed as `vortex` via `pyproject.toml`)
- **Modules**:
  - `vortex_config.py`: Single source of truth for VERSION and local settings.
  - `vortex_commands.py`: Definitions and descriptions of all CLI commands.
  - `vortex_completer.py`: Encapsulated logic for `prompt_toolkit` autocomplete.
  - `.build/`: Hidden directory for setuptools metadata (configured in `setup.cfg`).

## 📜 Coding Standards
- **Encoding**: ALL files must be saved in **UTF-8**. Include `# -*- coding: utf-8 -*-` at the top if adding new files.
- **Independence**: Never use relative imports. Use `sys.path.insert(0, BASE_DIR)` in the main script to ensure modules are found globally.
- **Commands**: New system commands MUST be added to `vortex_commands.py` first.
- **UI**: Use `rich` for all terminal output (Panels, Tables, Progress).

## 🔄 Update & Settings Mechanism
- **Git Updates**: Use `subprocess` with `cwd=BASE_DIR` to execute Git commands regardless of the user's current directory.
- **Config**: User settings are stored in `.vortex_settings.json` (ignored by Git). Default settings are hardcoded in `vortex_config.py`.
- **Auto-Update**: Always check `config.get("auto_update")` before running the silent update check on startup.

## 🔐 Security
- **Sensitive Data**: NEVER save passwords or connection strings to history.
- **Local Files**: `.env`, `.vortex_history`, and `.vortex_settings.json` are strictly local and MUST be kept in `.gitignore`.
