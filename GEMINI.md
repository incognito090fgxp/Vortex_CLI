# Vortex CLI Development Guide (Updated)

## 🏗 Modular Architecture
The project has been refactored into a structured package under the `vortex/` directory:
- `vortex/core/`: Primary application logic (`cli.py`), the update system (`updater.py`), and authentication (`auth.py`).
- `vortex/config/`: Configuration management (`manager.py`), versioning, and path resolution.
- `vortex/ui/`: Interactive components like banners (`banner.py`), styles (`style.py`), and command definitions.
- `vortex/database/`: Database connectivity and query execution (`db.py`).
- `vortex/registry.py`: Central registry of file paths and module names for dynamic lookups.

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
- **Cleanup**: Proactively removes `build/`, `.build/`, and `*.egg-info` to fix `egg_base` errors.
- **Shadowing Check**: Be aware that a `vortex.py` launcher exists in the root; it is designed not to shadow the package via absolute imports.

## 📂 Key Pathing (`PROJECT_ROOT`)
- Always use `vortex.registry` as the single source of truth for all file paths.
