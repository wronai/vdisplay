"""Merge multi-source pointer probes into a single ``PointerSample``."""

from __future__ import annotations

from typing import Any

from .context import WindowContextResolver, pick_context_coordinates
from .pointer_types import PointerSample
from .pointer_probes import (
    is_wayland_session,
    pointer_probe_errors,
    trustworthy_absolute,
    window_title,
)


def _pointer():
    """Public pointer facade (tests monkeypatch attributes here)."""
    from . import pointer as mod

    return mod


def pick_primary(sources: dict[str, tuple[int, int]], *, wayland: bool) -> str | None:
    order = (
        ("evdev", "gnome", "evdev-rel", "gtk", "xdotool")
        if wayland
        else ("xdotool", "gnome", "gtk", "evdev", "evdev-rel")
    )
    for name in order:
        if name in sources:
            return name
    return next(iter(sources), None)


def stale_sources(history: dict[str, list[tuple[int, int]]], *, min_samples: int = 6) -> tuple[str, ...]:
    stale: list[str] = []
    for name, samples in history.items():
        if len(samples) < min_samples:
            continue
        if len({sample for sample in samples[-min_samples:]}) == 1:
            stale.append(name)
    return tuple(stale)


def enrich_pointer_context(
    sample_kwargs: dict[str, Any],
    *,
    sources: dict[str, tuple[int, int]],
    stale: tuple[str, ...],
    primary: str | None,
    window_id: str | None,
    display: str | None,
    window_resolver: WindowContextResolver | None,
    evdev_relative_only: bool,
) -> None:
    ctx = pick_context_coordinates(sources, stale_sources=stale, primary=primary)
    if ctx is None:
        return
    cx, cy, csrc = ctx
    sample_kwargs["context_x"] = cx
    sample_kwargs["context_y"] = cy
    sample_kwargs["context_source"] = csrc
    sample_kwargs["monitor"] = _pointer().monitor_at(cx, cy, display=display)

    if window_resolver is None:
        return
    win_info = window_resolver.resolve(cx, cy, window_id)
    if win_info is None:
        return
    sample_kwargs["window_id"] = str(win_info.get("window_id") or window_id or "")
    sample_kwargs["window_title"] = (
        win_info.get("title") or win_info.get("name") or sample_kwargs.get("window_title")
    )
    sample_kwargs["app_label"] = win_info.get("app_label")
    sample_kwargs["process_name"] = win_info.get("process_name")
    if evdev_relative_only and csrc.endswith("*"):
        sample_kwargs.setdefault(
            "error",
            "evdev-rel is relative motion; screen/window from stale xdotool hint",
        )


def collect_pointer_sources(
    *,
    display: str | None,
    use_gtk: bool,
    gtk_every: int,
    tick: int,
    evdev_xy: tuple[int, int] | None,
    evdev_relative_only: bool,
    history: dict[str, list[tuple[int, int]]],
) -> tuple[dict[str, tuple[int, int]], str | None]:
    sources: dict[str, tuple[int, int]] = {}
    window_id: str | None = None
    wayland = is_wayland_session()

    if evdev_xy is not None:
        key = "evdev-rel" if evdev_relative_only else "evdev"
        sources[key] = evdev_xy
        history.setdefault(key, []).append(evdev_xy)

    probes = _pointer()
    if wayland and tick % max(1, gtk_every) == 0:
        gnome = probes.probe_gnome_shell_pointer()
        if gnome is not None and trustworthy_absolute("gnome", gnome):
            sources["gnome"] = gnome
            history.setdefault("gnome", []).append(gnome)

    if use_gtk and tick % max(1, gtk_every) == 0:
        gtk = probes.probe_gtk_subprocess()
        if gtk is not None and trustworthy_absolute("gtk", gtk):
            sources["gtk"] = gtk
            history.setdefault("gtk", []).append(gtk)

    xdotool = probes.probe_xdotool(display=display)
    if xdotool is not None:
        sources["xdotool"] = (xdotool[0], xdotool[1])
        window_id = xdotool[2]
        history.setdefault("xdotool", []).append(sources["xdotool"])
        for name, samples in list(history.items()):
            if len(samples) > 24:
                history[name] = samples[-24:]

    return sources, window_id


def resolve_primary_source(
    sources: dict[str, tuple[int, int]],
    stale: tuple[str, ...],
    *,
    wayland: bool,
) -> str | None:
    live_sources = {name: xy for name, xy in sources.items() if name not in stale}
    primary = pick_primary(live_sources, wayland=wayland)
    if primary is None:
        primary = pick_primary(live_sources or sources, wayland=wayland)
    if primary is None or (primary in stale and "evdev-rel" not in live_sources and "evdev" not in live_sources):
        if "evdev-rel" in live_sources:
            return "evdev-rel"
        if "evdev" in live_sources:
            return "evdev"
    return primary


def _empty_pointer_sample(errors: dict[str, str]) -> PointerSample:
    hint = "no live pointer source"
    detail = "; ".join(f"{k}={v}" for k, v in errors.items() if v)
    return PointerSample(x=None, y=None, error=f"{hint} ({detail})" if detail else hint)


def sample_pointer(
    *,
    display: str | None = None,
    use_gtk: bool = True,
    gtk_every: int = 1,
    tick: int = 0,
    evdev_xy: tuple[int, int] | None = None,
    evdev_relative_only: bool = False,
    source_history: dict[str, list[tuple[int, int]]] | None = None,
    window_resolver: WindowContextResolver | None = None,
) -> PointerSample:
    history = source_history if source_history is not None else {}
    wayland = is_wayland_session()
    sources, window_id = collect_pointer_sources(
        display=display,
        use_gtk=use_gtk,
        gtk_every=gtk_every,
        tick=tick,
        evdev_xy=evdev_xy,
        evdev_relative_only=evdev_relative_only,
        history=history,
    )

    if not sources:
        return _empty_pointer_sample(pointer_probe_errors())

    stale = stale_sources(history)
    primary = resolve_primary_source(sources, stale, wayland=wayland)

    if primary is None or (primary in stale and primary not in {"evdev-rel", "evdev"}):
        return _build_stale_pointer_sample(sources, stale, window_id, evdev_relative_only)

    return _build_live_pointer_sample(
        sources,
        primary,
        stale,
        window_id,
        display=display,
        window_resolver=window_resolver,
        evdev_relative_only=evdev_relative_only,
    )


def _build_stale_pointer_sample(
    sources: dict[str, tuple[int, int]],
    stale: tuple[str, ...],
    window_id: str | None,
    evdev_relative_only: bool,
) -> PointerSample:
    err_bits = ["no live pointer on Wayland (xdotool is stale)"]
    if evdev_relative_only:
        err_bits.append("evdev-rel is movement-only until seeded by gnome/gtk")
    errors = pointer_probe_errors()
    detail = "; ".join(f"{k}={v}" for k, v in errors.items() if v)
    if detail:
        err_bits.append(detail)
    return PointerSample(
        x=None,
        y=None,
        window_id=window_id,
        sources=sources,
        primary=None,
        stale_sources=stale,
        error=" — ".join(err_bits),
    )


def _build_live_pointer_sample(
    sources: dict[str, tuple[int, int]],
    primary: str,
    stale: tuple[str, ...],
    window_id: str | None,
    *,
    display: str | None,
    window_resolver: Any,
    evdev_relative_only: bool,
) -> PointerSample:
    x, y = sources[primary]
    title = window_title(window_id, display=display)
    error = None
    if evdev_relative_only and primary.startswith("evdev"):
        error = "evdev-rel is relative motion, not absolute screen coords"

    sample_kwargs: dict[str, Any] = {
        "x": x,
        "y": y,
        "window_id": window_id,
        "sources": sources,
        "window_title": title,
        "primary": primary,
        "stale_sources": stale,
        "error": error,
    }
    if primary.startswith("evdev") and not evdev_relative_only:
        sample_kwargs["monitor"] = _pointer().monitor_at(x, y, display=display)

    enrich_pointer_context(
        sample_kwargs,
        sources=sources,
        stale=stale,
        primary=primary,
        window_id=window_id,
        display=display,
        window_resolver=window_resolver,
        evdev_relative_only=evdev_relative_only,
    )
    if sample_kwargs.get("monitor") is None and not primary.startswith("evdev"):
        sample_kwargs["monitor"] = _pointer().monitor_at(x, y, display=display)

    return PointerSample(**sample_kwargs)
