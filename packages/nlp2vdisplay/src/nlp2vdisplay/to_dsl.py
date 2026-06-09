from __future__ import annotations

import re


def parse_display(text: str) -> str | None:
    return __import__("vdisplay.nlp", fromlist=["parse_display"]).parse_display(text)


def nl_to_dsl(prompt: str) -> str:
    from vdisplay.nlp import nl_to_dsl as _nl_to_dsl

    return _nl_to_dsl(prompt)
