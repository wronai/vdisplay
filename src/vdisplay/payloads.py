"""Backward-compatible payload helpers — delegate to application services."""

from __future__ import annotations

from typing import Any

from .application.services import discovery


def monitors_payload(display: str | None = None, *, include_all: bool = True) -> dict[str, Any]:
    return discovery.list_monitors(display, include_all=include_all)


def local_windows_payload(
    display: str | None = None,
    *,
    include_all: bool = True,
    apps_only: bool | None = None,
    include_internal: bool | None = None,
    min_width: int = 0,
    min_height: int = 0,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> dict[str, Any]:
    return discovery.list_windows_local(
        display,
        include_all=include_all,
        apps_only=apps_only,
        include_internal=include_internal,
        min_width=min_width,
        min_height=min_height,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )


def windows_payload(
    display: str | None = None,
    *,
    include_all: bool = True,
    apps_only: bool | None = None,
    include_internal: bool | None = None,
    min_width: int = 0,
    min_height: int = 0,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> dict[str, Any]:
    return discovery.list_windows_payload(
        display,
        include_all=include_all,
        apps_only=apps_only,
        include_internal=include_internal,
        min_width=min_width,
        min_height=min_height,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )


def adopted_payload(display: str | None = None) -> list[dict[str, Any]]:
    return discovery.list_adopted(display)


def all_payload(
    display: str | None = None,
    *,
    include_all: bool = True,
    apps_only: bool | None = None,
    include_internal: bool | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> dict[str, Any]:
    return discovery.list_all(
        display,
        include_all=include_all,
        apps_only=apps_only,
        include_internal=include_internal,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )
