# -*- coding: utf-8 -*-
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.align import Align
from rich.live import Live
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import prompt as pk_prompt
from prompt_toolkit.styles import Style as PStyle

console = Console()

def pager(items, title, columns, page_size=10, description=None):
    """
    VORTEX UI ENGINE - Universal Interactive Selector.
    
    columns: list of dicts:
        {
            'name': str, 
            'key': str, 
            'style': str, 
            'no_wrap': bool, 
            'min_width': int (скрыть если экран меньше),
            'render': function(val, item) -> str (optional)
        }
    """
    current_page = 0
    cursor_pos = 0
    total_items = len(items)
    
    if total_items == 0:
        console.print("[yellow]No items found.[/yellow]")
        return None

    st = PStyle.from_dict({"prompt": "bold cyan"})

    with console.screen():
        while True:
            width = console.size.width
            total_pages = (total_items + page_size - 1) // page_size
            start = current_page * page_size
            end = min(start + page_size, total_items)
            page_items = items[start:end]
            page_count = len(page_items)
            
            if cursor_pos >= page_count: 
                cursor_pos = max(0, page_count - 1)

            console.clear()

            # Фильтруем колонки по ширине экрана (Responsive)
            active_cols = [c for c in columns if width >= c.get('min_width', 0)]

            # Создаем таблицу
            t = Table(
                box=box.ROUNDED, 
                expand=True, 
                border_style="blue",
                header_style="bold cyan",
                show_edge=True
            )
            
            t.add_column("#", style="dim", width=4, justify="right")
            for col in active_cols:
                t.add_column(col['name'], style=col.get('style', ''), no_wrap=col.get('no_wrap', False))

            for i, item in enumerate(page_items):
                abs_idx = start + i + 1
                row_style = "reverse" if i == cursor_pos else ""
                
                row_data = []
                for col in active_cols:
                    val = item.get(col['key'], '')
                    
                    # Если есть кастомный рендерер для этой колонки
                    if 'render' in col:
                        val = col['render'](val, item)
                    elif isinstance(val, bool):
                        val = "[bold green]✔[/bold green]" if val else "[bold red]✘[/bold red]"
                    
                    row_data.append(str(val))
                
                t.add_row(str(abs_idx), *row_data, style=row_style)

            # Формируем UI
            ui_panel = Panel(
                t,
                title=f"[bold white] {title} [/bold white]",
                subtitle=f"[bold cyan] Page {current_page + 1}/{total_pages} [/bold cyan]",
                border_style="cyan",
                padding=(0, 1)
            )

            # Навигация
            nav = [
                "[bold cyan]↑/↓[/bold cyan] Move",
                "[bold cyan]←/→[/bold cyan] Page",
                "[bold cyan]Enter[/bold cyan] Select",
                "[bold cyan]Q[/bold cyan] Quit"
            ]
            
            footer_text = " | ".join(nav)
            if description:
                footer_text = f"{description}\n{footer_text}"
                
            footer = Panel(Align.center(footer_text), border_style="dim")

            console.print(ui_panel)
            console.print(footer)

            # Обработка ввода
            kb = KeyBindings()
            @kb.add('up')
            def _(event):
                nonlocal cursor_pos
                if cursor_pos > 0: cursor_pos -= 1
                event.app.exit(result=("up", None))
            
            @kb.add('down')
            def _(event):
                nonlocal cursor_pos
                if cursor_pos < page_count - 1: cursor_pos += 1
                event.app.exit(result=("down", None))
            
            @kb.add('left')
            def _(event): event.app.exit(result=("prev", None))
            
            @kb.add('right')
            def _(event): event.app.exit(result=("next", None))
            
            @kb.add('escape')
            @kb.add('q')
            def _(event): event.app.exit(result=("quit", None))

            @kb.add('enter')
            def _(event):
                text = event.app.current_buffer.text.strip()
                event.app.exit(result=("input", text) if text else ("select", cursor_pos))

            try:
                res = pk_prompt("Enter ID or command: ", key_bindings=kb, style=st)
                if not res: continue
                action, value = res
            except (KeyboardInterrupt, EOFError): return None

            if action == "quit": return None
            elif action == "prev":
                if current_page > 0: current_page -= 1; cursor_pos = 0
            elif action == "next":
                if current_page < total_pages - 1: current_page += 1; cursor_pos = 0
            elif action == "select":
                return page_items[value]
            elif action == "input":
                if value == 'q': return None
                if value.isdigit():
                    idx = int(value)
                    if 1 <= idx <= total_items: return items[idx-1]
                    else: console.print(f"[red]Invalid ID: {idx}[/red]")
