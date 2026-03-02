# -*- coding: utf-8 -*-

# CLI System Commands Descriptions
CLI_COMMANDS = {
    "check": "Проверить соединение с базой данных",
    "tables": "Вывести список всех таблиц в схеме public",
    "query": "Выполнить произвольный SQL запрос",
    "auth": "Перенастроить параметры подключения (.env)",
    "update": "Обновить CLI через Git pull",
    "config": "Настройки CLI (автообновление и др.)",
    "clear": "Очистить экран терминала",
    "help": "Показать справку по командам",
    "exit": "Выйти из Vortex CLI",
}

ALL_DESCRIPTIONS = {k.upper(): v for k, v in CLI_COMMANDS.items()}

def get_completer_map():
    """Returns the command map for autocomplete"""
    return {
        "check": None,
        "tables": None,
        "auth": None,
        "update": None,
        "config": {
            "auto_update": {"on": None, "off": None},
            "show": None,
        },
        "clear": None,
        "help": None,
        "exit": None,
        "query": None,
    }
