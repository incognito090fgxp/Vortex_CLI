# Vortex DB CLI - Project Context

Vortex DB CLI is a professional interactive command-line interface for managing PostgreSQL databases, built with Python. It provides a REPL-like experience with command autocompletion, execution history, and beautiful terminal formatting.

## 🚀 Project Overview

- **Purpose:** Provide a streamlined, interactive way to manage PostgreSQL databases directly from the terminal.
- **Main Technologies:** 
    - **Python 3.10+** (compatible with 3.14).
    - **Psycopg (v3):** Modern PostgreSQL adapter.
    - **Prompt Toolkit:** Powers the interactive shell with history and autocompletion.
    - **Rich:** Handles beautiful terminal output and progress indicators.
- **Architecture:** An object-oriented REPL (`VortexCLI`) managing connection state and command routing.

## 🛠 Building and Running

### Setup Instructions
1. **Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. **Install:**
   ```powershell
   pip install -e .
   ```
3. **Run:** Just type `vortex`.

## ✍️ Development Conventions

- **Security:** Sensitive data (passwords) must use `password_char=""` and avoid being saved to `.vortex_history`.
- **UI:** Follow "Gemini-style" formatting using `rich.panel.Panel` and `rich.table.Table`.
- **Configuration:** Use `is_configured()` to check if `.env` contains valid credentials.
