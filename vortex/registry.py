# -*- coding: utf-8 -*-
import os

# Корневая папка пакета (vortex/)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
# Корень всего проекта (Vortex_CLI/)
PROJECT_ROOT = os.path.dirname(PACKAGE_DIR)

# --- ПУТИ К ФАЙЛАМ ДАННЫХ ---
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
HISTORY_PATH = os.path.join(PROJECT_ROOT, ".vortex_history")
SETTINGS_PATH = os.path.join(PROJECT_ROOT, ".vortex_settings.json")

# --- РЕЕСТР ПУТЕЙ К ФАЙЛАМ ИСХОДНОГО КОДА ---
CONFIG_FILE = os.path.join(PACKAGE_DIR, "config", "manager.py")
DB_FILE = os.path.join(PACKAGE_DIR, "database", "db.py")
CLI_FILE = os.path.join(PACKAGE_DIR, "core", "cli.py")
UPDATER_FILE = os.path.join(PACKAGE_DIR, "core", "updater.py")
AUTH_FILE = os.path.join(PACKAGE_DIR, "core", "auth.py")
COMMANDS_FILE = os.path.join(PACKAGE_DIR, "ui", "commands.py")
COMPLETER_FILE = os.path.join(PACKAGE_DIR, "ui", "completer.py")
BANNER_FILE = os.path.join(PACKAGE_DIR, "ui", "banner.py")
STYLE_FILE = os.path.join(PACKAGE_DIR, "ui", "style.py")

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
