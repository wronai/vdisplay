"""CLI command registry — each module registers parser + handler via set_defaults."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from . import (
    agent,
    all_cmd,
    app,
    auto,
    control,
    diagnose,
    hmi,
    ide,
    info,
    map as map_cmd,
    mirror,
    monitors,
    nlp,
    observe,
    relay,
    sampler,
    screenshot,
    session,
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
    app.register,
    auto.register,
    ide.register,
    map_cmd.register,
    diagnose.register,
    sampler.register,
    screenshot.register,
    observe.register,
    hmi.register,
    nlp.register,
    agent.register,
    info.register,
    session.register,
]


def register_all(sub: argparse._SubParsersAction) -> None:
    for register in _COMMAND_MODULES:
        register(sub)
