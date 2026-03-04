# Vortex CLI Development Guide (Updated)

## 🏗 Modular Architecture
The project has been refactored into a structured package under the `vortex/` directory:
- `vortex/core/`: Primary application logic (`cli.py`) and the update system (`updater.py`).
- `vortex/config/`: Configuration management (`manager.py`), versioning, and path resolution.
- `vortex/ui/`: Interactive components like command definitions (`commands.py`) and tab-completion (`completer.py`).
- `vortex/database/`: Database connectivity and query execution (`db.py`).
- `vortex/registry.py`: Central registry of file paths and module names for dynamic lookups.

## 📌 Versioning System (PEP 440)
We use a 4-digit versioning scheme: **Release.Beta.DEV.FIX** (e.g., `0.3.1.5`)
- **Release**: Major version / infrastructure change.
- **Beta**: Stable feature sets.
- **DEV**: Development iterations.
- **FIX**: Hotfixes and minor patches.

## 🔄 Update & Sync Mechanism (Termux Optimized)
The update system in `vortex/core/updater.py` is designed for high reliability:
- **Git Strategy**: Uses `git reset --hard` to synchronize with remote branches/tags. This bypasses common "divergent branches" errors in Termux and Git environments where history might have been rewritten.
- **Cleanup**: Automatically removes `build/`, `.build/`, `dist/`, and `*.egg-info` directories before and after updates to prevent installation errors (like the `egg_base` error).
- **Dependency Sync**: 
  - **Windows**: Installs dependencies directly to avoid locking the `.exe`.
  - **Unix/Termux**: Performs `pip install -e .` (editable mode) to link the repository to the environment.
  - **Fallback**: If editable installation fails, it attempts a simple dependency-only installation.
- **Shadowing Check**: Automatically detects if a `vortex.py` file exists in the project root, which would shadow the actual package and cause `ImportError`.

## 📂 Key Pathing (`PROJECT_ROOT`)
- `PROJECT_ROOT` is dynamically determined in `vortex/config/manager.py`.
- It must point to the directory containing `.env`, `.vortex_settings.json`, and `pyproject.toml`.
- **Warning**: Do NOT place a `vortex.py` file in the project root; it will break the package imports.

## 🏷 Tagging Strategy
- **Stable Tags**: Strictly `v` followed by digits (e.g., `v1`, `v10`). 
- CLI uses numeric sorting to identify the "Latest Stable" version.
- Move tags manually: `git tag -f v1 <hash> && git push origin v1 --force`.
