# -*- coding: utf-8 -*-
from prompt_toolkit.completion import NestedCompleter, Completion, Completer, CompleteEvent
from prompt_toolkit.document import Document
from typing import Iterable

from vortex_commands import ALL_DESCRIPTIONS, get_completer_map

class CustomCompleter(Completer):
    def __init__(self):
        self.nested = NestedCompleter.from_nested_dict(get_completer_map())

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        for completion in self.nested.get_completions(document, complete_event):
            meta = ALL_DESCRIPTIONS.get(completion.text.upper(), "")
            yield Completion(completion.text, start_position=completion.start_position, display_meta=meta)
