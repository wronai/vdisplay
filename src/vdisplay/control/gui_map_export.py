"""Export GUI Map Pack to operator markdown and SVG atlas (PR-26)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from .gui_map import GuiMapElement, GuiMapPack, GuiMapRegion


def render_map_markdown(pack: GuiMapPack, *, title: str | None = None) -> str:
    heading = title or f"GUI Map — {pack.monitor or 'screen'}"
    lines = [f"# {heading}", ""]
    if pack.monitor:
        rot = f", rotated {pack.rotation}" if pack.rotation and pack.rotation != "normal" else ""
        lines.append(f"- Monitor: `{pack.monitor}`{rot}")
    lines.append(f"- Elements: {len(pack.elements)}")
    lines.append(f"- Regions: {len(pack.regions)}")
    lines.append("")
    lines.append("## Regions")
    lines.append("")
    for region in pack.regions.values():
        lines.extend(_region_markdown(region, pack))
        lines.append("")
    lines.append("## Elements")
    lines.append("")
    for element in pack.elements.values():
        lines.extend(_element_markdown(element))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _region_markdown(region: GuiMapRegion, pack: GuiMapPack) -> list[str]:
    bounds = region.scope_bounds
    lines = [
        f"### Region: `{region.id}`",
        f"- Label: {region.label}",
        f"- Scope bounds: {bounds.x},{bounds.y} {bounds.width}x{bounds.height}",
    ]
    if region.anchors:
        lines.append(f"- Anchor texts: {', '.join(region.anchors[:8])}")
    if region.fingerprint:
        lines.append(f"- Fingerprint: `{region.fingerprint}`")
    if region.elements:
        lines.append("- Elements:")
        for element_id in region.elements[:20]:
            element = pack.elements.get(element_id)
            label = element.identity.name if element else element_id
            lines.append(f"  - `{element_id}` — {label}")
    return lines


def _element_markdown(element: GuiMapElement) -> list[str]:
    raw = element.raw_bounds
    action = element.action_bounds
    click = element.click_point
    lines = [
        f"### Element: `{element.id}`",
        f"- Role: {element.role}",
        f"- Raw bounds: {raw.x},{raw.y} {raw.width}x{raw.height}",
        f"- Action bounds: {action.x},{action.y} {action.width}x{action.height}",
        f"- Click point: {click.x},{click.y}",
    ]
    if element.anchors:
        lines.append(f"- Anchors: {', '.join(element.anchors)}")
    if element.identity.name_prefix:
        lines.append(f"- Preferred verify: identity(name_prefix=\"{element.identity.name_prefix}\")")
    if element.tile_fingerprint:
        lines.append(f"- Tile fingerprint: `{element.tile_fingerprint}`")
    if element.notes:
        lines.append(f"- Notes: {element.notes}")
    lines.append(
        f"- Example: `vdisplay control click --backend vision --map map.json --target {element.id}`"
    )
    return lines


def render_map_svg(
    png: bytes,
    pack: GuiMapPack,
    *,
    show_raw: bool = True,
    show_action: bool = True,
) -> bytes:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow required for map SVG export") from exc

    image = Image.open(io.BytesIO(png)).convert("RGBA")
    width, height = image.size
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<pattern id="bg" patternUnits="userSpaceOnUse" width="1" height="1">',
        f'<image href="data:image/png;base64,{_png_b64(png)}" width="{width}" height="{height}"/>',
        "</pattern>",
        "</defs>",
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
    ]
    for region in pack.regions.values():
        bounds = region.scope_bounds
        parts.append(
            f'<rect id="region-{region.id}" x="{bounds.x}" y="{bounds.y}" '
            f'width="{bounds.width}" height="{bounds.height}" '
            f'fill="none" stroke="#00b4ff" stroke-width="2" stroke-dasharray="8 4" opacity="0.8"/>'
        )
        parts.append(
            f'<text x="{bounds.x + 4}" y="{max(12, bounds.y + 14)}" fill="#00b4ff" '
            f'font-size="12" font-family="monospace">{region.id}</text>'
        )
    for index, element in enumerate(pack.elements.values(), start=1):
        parts.extend(_element_svg(element, index=index, show_raw=show_raw, show_action=show_action))
    parts.append("</svg>")
    return "\n".join(parts).encode("utf-8")


def _element_svg(element: GuiMapElement, *, index: int, show_raw: bool, show_action: bool) -> list[str]:
    parts: list[str] = []
    element_id = element.id.replace('"', "")
    if show_raw:
        raw = element.raw_bounds
        parts.append(
            f'<rect id="{element_id}-raw" x="{raw.x}" y="{raw.y}" '
            f'width="{raw.width}" height="{raw.height}" '
            f'fill="none" stroke="#888" stroke-width="1" stroke-dasharray="4 3" opacity="0.9"/>'
        )
    if show_action:
        action = element.action_bounds
        parts.append(
            f'<rect id="{element_id}-action" x="{action.x}" y="{action.y}" '
            f'width="{action.width}" height="{action.height}" '
            f'fill="rgba(0,220,80,0.12)" stroke="#00dc50" stroke-width="2"/>'
        )
        click = element.click_point
        parts.append(
            f'<circle id="{element_id}-click" cx="{click.x}" cy="{click.y}" r="4" fill="#00dc50"/>'
        )
    label = (element.identity.name or element.id)[:32].replace("&", "&amp;").replace("<", "&lt;")
    anchor_y = element.action_bounds.y if show_action else element.raw_bounds.y
    parts.append(
        f'<text id="{element_id}-label" x="{element.action_bounds.x + 4}" '
        f'y="{max(12, anchor_y + 14)}" fill="#00dc50" font-size="11" font-family="monospace">'
        f"{index}. {label}</text>"
    )
    return parts


def _png_b64(png: bytes) -> str:
    import base64

    return base64.b64encode(png).decode("ascii")


def write_map_artifacts(
    pack: GuiMapPack,
    *,
    json_path: str | Path,
    md_path: str | Path | None = None,
    svg_path: str | Path | None = None,
    png: bytes | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    from .gui_map import save_gui_map

    json_path = Path(json_path)
    save_gui_map(json_path, pack)
    written: dict[str, Any] = {"json": str(json_path.resolve())}
    if md_path is not None:
        md_path = Path(md_path)
        md_path.write_text(render_map_markdown(pack, title=title), encoding="utf-8")
        written["md"] = str(md_path.resolve())
    if svg_path is not None and png is not None:
        svg_path = Path(svg_path)
        svg_path.write_bytes(render_map_svg(png, pack))
        written["svg"] = str(svg_path.resolve())
    return written
