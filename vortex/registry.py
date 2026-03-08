# -*- coding: utf-8 -*-
import os

# Корневая папка пакета (vortex/)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
# Корень всего проекта (Vortex_CLI/)
PROJECT_ROOT = os.path.dirname(PACKAGE_DIR)

# --- ПУТИ К ФАЙЛАМ ДАННЫХ ---
DATA_DIR = os.path.join(PROJECT_ROOT, ".vortex_data")
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
HISTORY_PATH = os.path.join(DATA_DIR, "history")
SQL_HISTORY_PATH = os.path.join(DATA_DIR, "sql_history")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
EGG_INFO_DIR = os.path.join(DATA_DIR, "vortex_cli.egg-info")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    try: os.makedirs(DATA_DIR)
    except: pass

# --- РЕЕСТР ПУТЕЙ К ФАЙЛАМ ИСХОДНОГО КОДА ---
CONFIG_FILE = os.path.join(PACKAGE_DIR, "config", "manager.py")
DB_FILE = os.path.join(PACKAGE_DIR, "database", "db.py")
DB_CORE = os.path.join(PACKAGE_DIR, "database", "core.py")
DB_EXPLORER = os.path.join(PACKAGE_DIR, "database", "explorer.py")
DB_SCHEMA = os.path.join(PACKAGE_DIR, "database", "schema.py")
DB_BROWSER = os.path.join(PACKAGE_DIR, "database", "browser.py")
DB_CONSOLE = os.path.join(PACKAGE_DIR, "database", "console.py")
DB_README = os.path.join(PACKAGE_DIR, "database", "README.md")

CLI_FILE = os.path.join(PACKAGE_DIR, "core", "cli.py")
UPDATER_FILE = os.path.join(PACKAGE_DIR, "core", "updater.py")
AUTH_FILE = os.path.join(PACKAGE_DIR, "core", "auth.py")
COMMANDS_FILE = os.path.join(PACKAGE_DIR, "ui", "commands.py")
COMPLETER_FILE = os.path.join(PACKAGE_DIR, "ui", "completer.py")
BANNER_FILE = os.path.join(PACKAGE_DIR, "ui", "banner.py")
STYLE_FILE = os.path.join(PACKAGE_DIR, "ui", "style.py")
ENGINE_DIR = os.path.join(PACKAGE_DIR, "ui", "engine")
ENGINE_README = os.path.join(ENGINE_DIR, "README.md")
GEMINI_FILE = os.path.join(PROJECT_ROOT, "GEMINI.md")

# --- РЕЕСТР МОДУЛЕЙ ДЛЯ ИМПОРТА ---
MOD_CONFIG = "vortex.config.manager"
MOD_DB = "vortex.database.db"
MOD_CLI = "vortex.core.cli"
MOD_UPDATER = "vortex.core.updater"
MOD_AUTH = "vortex.core.auth"
MOD_COMMANDS = "vortex.ui.commands"
MOD_COMPLETER = "vortex.ui.completer"
MOD_BANNER = "vortex.ui.banner"
MOD_STYLE = "vortex.ui.style"
MOD_ENGINE = "vortex.ui.engine"
