# Vortex DB CLI - Project Context

Vortex DB CLI is a professional interactive command-line interface for managing PostgreSQL databases, built with Python. It provides a REPL-like experience with command autocompletion, execution history, and beautiful terminal formatting.

## 🚀 Project Overview

- **Purpose:** Provide a streamlined, interactive way to manage PostgreSQL databases directly from the terminal.
- **Main Technologies:** 
    - **Python 3.10+** (designed to be compatible with latest versions like 3.14).
    - **Psycopg (v3):** Modern PostgreSQL adapter for Python.
    - **Prompt Toolkit:** Powers the interactive shell with autocompletion and history.
    - **Rich:** Handles beautiful terminal output, tables, and progress indicators.
    - **Dotenv:** Manages database credentials securely via `.env` files.
- **Architecture:** A single-class interactive application (`VortexCLI`) that manages the database connection lifecycle and command routing.

## 🛠 Building and Running

### Prerequisites
- Python installed on the system.
- Access to a PostgreSQL instance.

### Setup Instructions
1. **Create Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # Linux/macOS
   ```
2. **Install Dependencies (Development Mode):**
   ```powershell
   pip install -e .
   ```
   *This makes the `vortex` command available globally within the virtual environment.*
3. **Configure Environment:**
   - Copy `.env.example` to `.env`.
   - Update `.env` with your database credentials.

### Key Commands
- **Start CLI:** `vortex`
- **Help:** Type `help` inside the CLI.
- **Check Connection:** `check`
- **List Tables:** `tables`
- **SQL Query:** `query <SQL>` or simply start typing a SQL keyword (e.g., `SELECT ...`).
- **Exit:** `exit` or double `Ctrl+C`.

## 📂 Project Structure

- `vortex_db.py`: Main entry point and logic for the interactive CLI.
- `pyproject.toml`: Modern Python packaging configuration, defines the `vortex` script entry point.
- `requirements.txt`: List of dependencies (redundant but kept for traditional pip usage).
- `.env.example`: Template for required database environment variables.
- `.gitignore`: Configured to protect `.env` secrets and exclude `venv/` and `__pycache__`.

## ✍️ Development Conventions

- **Interactive Logic:** All core commands are methods within the `VortexCLI` class in `vortex_db.py`.
- **Formatting:** Use `rich.table.Table` for displaying database results and `rich.panel.Panel` for informational messages.
- **Connection Management:** The CLI uses a persistent connection established via `get_connection()` which handles reconnection if the session is lost.
- **SQL Execution:** The `cmd_query` method handles both result-returning queries (SELECT) and transactional commands (INSERT/UPDATE/DELETE) with automatic commits.
- **Safety:** Credentials must never be hardcoded; always use `os.getenv` with `load_dotenv()`.
