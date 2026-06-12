"""CLI command registry — each module registers parser + handler via set_defaults."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from . import (
    agent,
    all_cmd,
    app,
    auto,
    config,
    control,
    diagnose,
    electron_share,
    hmi,
    history,
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
    services,
    session,
    history,
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
    electron_share.register,
    services.register,
    app.register,
    auto.register,
    config.register,
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
    history.register,
]


def register_all(sub: argparse._SubParsersAction) -> None:
    for register in _COMMAND_MODULES:
        register(sub)
