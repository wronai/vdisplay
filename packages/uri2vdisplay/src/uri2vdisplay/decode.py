from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def uri_to_dsl(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme != "vdisplay":
        raise ValueError(f"unsupported scheme: {parsed.scheme}")

    path = parsed.path.strip("/")
    if path.startswith("cmd/"):
        verb = path.split("/", 1)[1].upper()
    else:
        verb = (path or "INFO").upper()

    qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    parts = [verb]
    flag_map = {
        "display": "DISPLAY",
        "source": "SOURCE",
        "target": "TARGET",
        "out": "OUT",
        "title": "TITLE",
        "width": "WIDTH",
        "height": "HEIGHT",
    }
    for key, flag in flag_map.items():
        if key in qs:
            parts.extend([flag, qs[key]])
    return " ".join(parts)
