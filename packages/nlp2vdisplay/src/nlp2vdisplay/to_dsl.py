from __future__ import annotations

import re


def nl_to_dsl(prompt: str) -> str:
    text = prompt.strip().lower()
    if not text:
        return "INFO"
    if "output" in text or "monitor" in text or "ekran" in text:
        return "OUTPUTS DISPLAY :0"
    if "window" in text or "okno" in text:
        return "WINDOWS"
    if "screenshot" in text or "zrzut" in text:
        m = re.search(r"(\S+\.png)", prompt)
        out = m.group(1) if m else "screen.png"
        return f"SCREENSHOT OUT {out} DISPLAY :99"
    if "mirror" in text or "lustrz" in text:
        return "MIRROR SOURCE primary"
    if "firefox" in text:
        return "ADOPT TITLE Firefox"
    if "validate" in text or "sprawdź" in text:
        return "VALIDATE"
    return "INFO"
