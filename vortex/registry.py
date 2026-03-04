# -*- coding: utf-8 -*-
import os

# Корневая папка пакета (vortex/)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
# Корень всего проекта (Vortex_CLI/)
PROJECT_ROOT = os.path.dirname(PACKAGE_DIR)

# --- РЕЕСТР ПУТЕЙ К ФАЙЛАМ ---

# Файл конфигурации и настроек
CONFIG_FILE = os.path.join(PACKAGE_DIR, "config", "manager.py")

# Файл управления базой данных
DB_FILE = os.path.join(PACKAGE_DIR, "database", "db.py")

# Основной файл интерфейса CLI
CLI_FILE = os.path.join(PACKAGE_DIR, "core", "cli.py")

# Логика системы обновлений
UPDATER_FILE = os.path.join(PACKAGE_DIR, "core", "updater.py")

# Описания команд и UI компоненты
COMMANDS_FILE = os.path.join(PACKAGE_DIR, "ui", "commands.py")
COMPLETER_FILE = os.path.join(PACKAGE_DIR, "ui", "completer.py")

# --- РЕЕСТР МОДУЛЕЙ ДЛЯ ИМПОРТА ---
# Эти переменные можно использовать для динамического импорта или просто как справку

MOD_CONFIG = "vortex.config.manager"
MOD_DB = "vortex.database.db"
MOD_CLI = "vortex.core.cli"
MOD_UPDATER = "vortex.core.updater"
MOD_COMMANDS = "vortex.ui.commands"
MOD_COMPLETER = "vortex.ui.completer"
