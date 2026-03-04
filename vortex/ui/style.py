# -*- coding: utf-8 -*-
from prompt_toolkit.styles import Style as PromptStyle

prompt_style = PromptStyle.from_dict({
    "prompt": "bold cyan",
    "at": "#888888",
    "host": "italic yellow",
    "bottom-toolbar": "#ffffff bg:#222222",
    "completion-menu.completion": "bg:#333333 #ffffff",
    "completion-menu.completion.current": "bg:#00aaaa #000000",
    "completion-menu.meta.completion": "bg:#444444 #aaaaaa",
})
