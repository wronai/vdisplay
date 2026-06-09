"""Explicit verify strategies per provider/application profile."""

from __future__ import annotations

from enum import StrEnum


class VerifyStrategy(StrEnum):
    NONE = "none"
    STRUCTURE = "structure"
    TEXT = "text"
    DOM = "dom"
    SCREENSHOT = "screenshot"
    OCR = "ocr"
    HYBRID = "hybrid"
