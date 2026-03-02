# Vortex CLI Development Guide

## 📌 Versioning System (PEP 440)
We use a 4-digit versioning scheme: **Release.Beta.DEV.FIX** (e.g., `0.2.0.5`)
- **Release**: Major versions (infrastructure change).
- **Beta**: Stable feature sets within a release.
- **DEV**: Development iterations / experimental features.
- **FIX**: Hotfixes and minor patches.

### 🏷 Tagging Strategy
- **Floating Stable Tags**: Use tags like `v0`, `v1` to point to the latest **proven stable** commit of that release. 
- Users are encouraged to stay on these tags for production use.
- Developer moves these tags manually: `git tag -f v0 <hash> && git push origin v0 --force`.

## 🔄 Update & Settings Mechanism
- **Logic**: `update check` calculates the "commit distance" between the local HEAD and the upstream branch. 
- **Distance-based**: String version comparison is secondary; if the remote branch has more commits, an update is available. This ensures correct "left-to-right" progression regardless of file content.
- **Dependency Sync**: 
  - **Windows**: Installs dependencies by list from `pyproject.toml` to avoid locking `vortex.exe`.
  - **Unix**: Performs `pip install .`.
  - **Repair**: If the environment is broken (ModuleNotFoundError), use `pip install -e .`.

## 📂 Project Structure
- `vortex.py`: Core CLI logic and command handlers.
- `vortex_config.py`: Single source of truth for VERSION and local settings.
- `vortex_commands.py`: Command definitions and help text.
- `vortex_completer.py`: Tab-completion logic.
- `pyproject.toml`: Package metadata and dependencies.
