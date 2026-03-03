# Vortex CLI Development Guide

## 📌 Versioning System (PEP 440)
We use a 4-digit versioning scheme: **Release.Beta.DEV.FIX** (e.g., `0.2.0.5`)
- **Release**: Major versions (infrastructure change).
- **Beta**: Stable feature sets within a release.
- **DEV**: Development iterations / experimental features.
- **FIX**: Hotfixes and minor patches.

### 🏷 Tagging Strategy
- **Floating Stable Tags**: Use tags like `v0`, `v1`, `v10` to point to the latest **proven stable** commit.
- **Format**: Strictly `v` followed by digits (`^v\d+$`). No dots, letters, or other symbols allowed for stable aliases.
- **Sorting**: CLI uses numeric sorting for these tags (e.g., `v10` is recognized as newer than `v2`).
- Users are encouraged to stay on these tags for production use.
- Developer moves these tags manually: `git tag -f v0 <hash> && git push origin v0 --force`.

## 🔄 Update & Settings Mechanism
- **Logic**: 
  - **Main Branch**: Performs a dual check for the latest commit (`origin/main`) and the latest stable numeric tag. 
    - If an update is available, it prompts: *"Would you like to update to the stable version? If so, select 's' (stable)."*
    - User choices: `y` (update to latest commit), `s` (update to latest stable tag), `n` (skip).
    - If no stable tag exists, it notifies: *"Note: No stable version found."* and only offers `y/n`.
  - **Other Branches/Detached HEAD**: Calculates the "commit distance" between the local HEAD and the upstream branch. This feature is disabled outside of `main` to prevent accidental stable-tracking on development branches.
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
