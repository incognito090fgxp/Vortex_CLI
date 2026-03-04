# -*- coding: utf-8 -*-
from prompt_toolkit.completion import NestedCompleter, Completion, Completer, CompleteEvent
from prompt_toolkit.document import Document
from typing import Iterable

from .commands import ALL_DESCRIPTIONS, get_completer_map

class CustomCompleter(Completer):
    def __init__(self):
        self.nested = NestedCompleter.from_nested_dict(get_completer_map())

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        for completion in self.nested.get_completions(document, complete_event):
            text_before_cursor = document.text_before_cursor.strip().upper()
            words = text_before_cursor.split()
            
            meta = ""
            if words:
                full_cmd_key = f"{words[0]} {completion.text.upper()}"
                meta = ALL_DESCRIPTIONS.get(full_cmd_key, "")
            
            if not meta:
                meta = ALL_DESCRIPTIONS.get(completion.text.upper(), "")
                
            yield Completion(completion.text, start_position=completion.start_position, display_meta=meta)
