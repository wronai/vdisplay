"""CLI command registry — each module registers parser + handler via set_defaults."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from . import (
    agent,
    all_cmd,
    control,
    diagnose,
    info,
    mirror,
    monitors,
    nlp,
    relay,
    sampler,
    screenshot,
    virtual,
    windows,
)

_COMMAND_MODULES: list[Callable[[argparse._SubParsersAction], None]] = [
    monitors.register,
    windows.register,
    all_cmd.register,
    all_cmd.register_outputs,
    virtual.register,
    mirror.register,
    relay.register,
    control.register,
    diagnose.register,
    sampler.register,
    screenshot.register,
    nlp.register,
    agent.register,
    info.register,
]


def register_all(sub: argparse._SubParsersAction) -> None:
    for register in _COMMAND_MODULES:
        register(sub)
