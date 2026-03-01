# Описания системных команд CLI
CLI_COMMANDS = {
    'check': 'Проверить соединение с базой данных',
    'tables': 'Вывести список всех таблиц в схеме public',
    'query': 'Выполнить произвольный SQL запрос',
    'auth': 'Перенастроить параметры подключения (.env)',
    'clear': 'Очистить экран терминала',
    'help': 'Показать справку по командам',
    'exit': 'Выйти из Vortex CLI',
}

# Базовая иерархия SQL для NestedCompleter (будет дополнена динамически таблицами)
SQL_HIERARCHY = {
    'SELECT': {
        '*': {'FROM': {}},
        'COUNT(*)': {'FROM': {}},
        'DISTINCT': {},
    },
    'INSERT': {'INTO': {}},
    'UPDATE': {},
    'DELETE': {'FROM': {}},
    'CREATE': {'TABLE': {}, 'DATABASE': {}, 'INDEX': {}},
    'DROP': {'TABLE': {}, 'DATABASE': {}},
    'ALTER': {'TABLE': {'ADD': {'COLUMN': {}}, 'DROP': {'COLUMN': {}}, 'RENAME': {'TO': {}}}},
    'JOIN': {'INNER': {'JOIN': {}}, 'LEFT': {'JOIN': {}}, 'RIGHT': {'JOIN': {}}},
    'WHERE': {},
    'GROUP': {'BY': {}},
    'ORDER': {'BY': {}},
    'LIMIT': {},
}

# Мета-описания
ALL_DESCRIPTIONS = {
    **CLI_COMMANDS,
    'SELECT': 'Выбрать данные',
    'INSERT': 'Вставить данные',
    'UPDATE': 'Обновить данные',
    'DELETE': 'Удалить данные',
    'FROM': 'Из какой таблицы?',
    'WHERE': 'Условие фильтрации',
    'TABLE': 'Сущность: Таблица',
}

# Плейсхолдеры (Призрачный текст)
PLACEHOLDERS = {
    'SELECT': ' * FROM <table_name>',
    'FROM': ' <table_name>',
    'INSERT INTO': ' <table_name> (cols) VALUES (...)',
    'UPDATE': ' <table_name> SET ...',
    'DELETE FROM': ' <table_name> WHERE ...',
    'WHERE': ' <condition>',
}

def get_completer_map():
    return {
        'check': None,
        'tables': None,
        'auth': None,
        'clear': None,
        'help': None,
        'exit': None,
        'query': SQL_HIERARCHY,
    }
