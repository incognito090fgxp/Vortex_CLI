# -*- coding: utf-8 -*-
def main():
    """Lazy loader for the main entry point to avoid circular imports during installation."""
    from .core.cli import main as real_main
    real_main()

__all__ = ["main"]
