# -*- coding: utf-8 -*-

# CLI System Commands Descriptions
CLI_COMMANDS = {
    "db": "Управление базой данных (проводник, статистика, консоль)",
    "auth": "Перенастроить параметры подключения (.env)",
    "update": "Управление обновлениями (ветки, теги, коммиты)",
    "config": "Настройки CLI (автообновление и др.)",
    "clear": "Очистить экран терминала",
    "help": "Показать справку по командам",
    "exit": "Выйти из Vortex CLI",
}

# Дополнительные описания для подкоманд
SUB_COMMANDS = {
    "UPDATE CHECK": "Проверить наличие обновлений на текущей ветке",
    "UPDATE BRANCH": "Выбрать и переключиться на другую ветку",
    "UPDATE TAG": "Выбрать и переключиться на тег (версию)",
    "UPDATE COMMIT": "Выбрать конкретный коммит из истории",
}

ALL_DESCRIPTIONS = {k.upper(): v for k, v in CLI_COMMANDS.items()}
ALL_DESCRIPTIONS.update(SUB_COMMANDS)

def get_completer_map():
    """Returns the command map for autocomplete"""
    return {
        "db": None,
        "auth": None,
        "update": {
            "check": None,
            "branch": None,
            "tag": None,
            "commit": None,
        },
        "config": {
            "auto_update": {"on": None, "off": None},
            "show": None,
        },
        "clear": None,
        "help": None,
        "exit": None,
    }
