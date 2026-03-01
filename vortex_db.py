import os
import sys
import time
import psycopg
from dotenv import load_dotenv
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style as PromptStyle

# Загружаем переменные из .env
load_dotenv()

console = Console()

# Стили для промпта
prompt_style = PromptStyle.from_dict({
    'prompt': 'bold cyan',
    'at': 'dim white',
    'host': 'italic yellow',
})

class VortexCLI:
    def __init__(self):
        self.session = PromptSession(history=InMemoryHistory())
        self.completer = WordCompleter([
            'check', 'tables', 'query', 'clear', 'help', 'exit'
        ], ignore_case=True)
        self.ctrl_c_count = 0
        self.db_conn = None

    def get_connection(self):
        """Создает или возвращает существующее соединение."""
        if self.db_conn and not self.db_conn.closed:
            return self.db_conn
            
        try:
            self.db_conn = psycopg.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME", "postgres"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                autocommit=False
            )
            return self.db_conn
        except Exception as e:
            console.print(Panel(f"[bold red]❌ Ошибка подключения:[/bold red]\n{e}", title="Error", border_style="red"))
            return None

    def cmd_check(self):
        """Проверка связи."""
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
            p.add_task("Пинг БД...", total=None)
            conn = self.get_connection()
            if conn:
                console.print(f"[bold green]✅ Соединение активно![/bold green] [dim](DB: {os.getenv('DB_NAME')})[/dim]")

    def cmd_tables(self):
        """Список таблиц."""
        conn = self.get_connection()
        if not conn: return
        
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            rows = cur.fetchall()
            
            if not rows:
                console.print("[yellow]ℹ️ Таблиц не найдено.[/yellow]")
            else:
                table = Table(title="Public Tables", header_style="bold magenta")
                table.add_column("Name", style="cyan")
                for (name,) in rows:
                    table.add_row(name)
                console.print(table)

    def cmd_query(self, sql: str):
        """Выполнение SQL."""
        if not sql:
            console.print("[red]⚠️ Введите SQL запрос после команды query[/red]")
            return
            
        conn = self.get_connection()
        if not conn: return
        
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description:
                    table = Table(show_header=True, header_style="bold yellow")
                    for desc in cur.description:
                        table.add_column(desc[0])
                    
                    for row in cur.fetchmany(50): # Лимит 50 для превью
                        table.add_row(*[str(i) for i in row])
                    console.print(table)
                else:
                    conn.commit()
                    console.print("[green]✅ Выполнено (Commit).[/green]")
        except Exception as e:
            console.print(f"[bold red]❌ SQL Error:[/bold red] {e}")

    def show_help(self):
        help_text = """
        [bold cyan]Доступные команды:[/bold cyan]
        [bold white]check[/bold white]      - Проверить статус БД
        [bold white]tables[/bold white]     - Показать все таблицы
        [bold white]query <sql>[/bold white] - Выполнить SQL запрос
        [bold white]clear[/bold white]      - Очистить экран
        [bold white]help[/bold white]       - Эта справка
        [bold white]exit[/bold white]       - Выход (или дважды Ctrl+C)
        """
        console.print(Panel(help_text, title="Vortex Help", border_style="blue"))

    def run(self):
        console.print(Panel.fit("[bold cyan]🌀 VORTEX DB INTERACTIVE CLI[/bold cyan]\n[dim]Введите 'help' для списка команд[/dim]", border_style="cyan"))
        
        while True:
            try:
                # Формируем промпт: vortex@localhost>
                db_host = os.getenv('DB_HOST', 'localhost')
                message = [
                    ('class:prompt', 'vortex'),
                    ('class:at', '@'),
                    ('class:host', db_host),
                    ('class:prompt', '> '),
                ]
                
                text = self.session.prompt(message, completer=self.completer, style=prompt_style).strip()
                self.ctrl_c_count = 0 # Сбрасываем счетчик если ввод прошел

                if not text:
                    continue
                
                parts = text.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == 'exit':
                    break
                elif cmd == 'help':
                    self.show_help()
                elif cmd == 'check':
                    self.cmd_check()
                elif cmd == 'tables':
                    self.cmd_tables()
                elif cmd == 'query':
                    self.cmd_query(arg)
                elif cmd == 'clear':
                    console.clear()
                else:
                    # Если ввели просто SQL без 'query'
                    if text.lower().startswith(('select', 'insert', 'update', 'delete', 'create', 'drop')):
                        self.cmd_query(text)
                    else:
                        console.print(f"[red]❓ Неизвестная команда: {cmd}. Введите 'help'[/red]")

            except KeyboardInterrupt:
                self.ctrl_c_count += 1
                if self.ctrl_c_count >= 2:
                    console.print("\n[yellow]👋 Завершение работы...[/yellow]")
                    break
                console.print("\n[dim]Нажмите Ctrl+C еще раз для выхода[/dim]")
                continue
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]🔥 Ошибка:[/red] {e}")

        if self.db_conn:
            self.db_conn.close()

def main():
    cli = VortexCLI()
    cli.run()

if __name__ == "__main__":
    main()
