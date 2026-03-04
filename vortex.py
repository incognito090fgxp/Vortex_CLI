# -*- coding: utf-8 -*-
"""
Vortex CLI Launcher
Allows running the application via 'python vortex.py' from the root directory.
"""
import sys
import os

# Get absolute path of this file's directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ensure the project root is in sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# If we are running this file directly, and there's a 'vortex' directory,
# Python might get confused. We force the import from the package.
try:
    from vortex.core.cli import main
except ImportError:
    # Fallback for some environments
    from vortex import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[dim]Interrupted by user.[/dim]")
        sys.exit(0)
