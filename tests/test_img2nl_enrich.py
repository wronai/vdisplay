from __future__ import annotations

import io

import pytest

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.application.executor import execute
from vdisplay.application.services import img2nl_enrich


def _make_png(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_enrich_screenshot_payload_adds_nl(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(_make_png(64, 48, (20, 40, 200)))

    monkeypatch.setattr(
        img2nl_enrich,
        "describe_screenshot_image",
        lambda path, locale=None: {
            "ok": True,
            "text": "Ekran z niebieskim tłem.",
            "locale": "pl",
            "scene_class": "flat_monochrome",
            "llm_hint": {"send_to_llm": False},
        },
    )

    payload = img2nl_enrich.enrich_screenshot_payload({"saved": str(png), "mode": "host"})
    assert payload["nl"] == "Ekran z niebieskim tłem."
    assert payload["img2nl"]["scene_class"] == "flat_monochrome"


def test_execute_screenshot_enriches_when_img2nl_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    png = tmp_path / "host.png"
    png.write_bytes(_make_png(32, 32, (0, 0, 0)))

    monkeypatch.setattr(
        "vdisplay.application.executor.execute_local",
        lambda cmd: {"saved": str(png), "mode": "host", "source": cmd.source},
    )
    monkeypatch.setattr(
        img2nl_enrich,
        "describe_screenshot_image",
        lambda path, locale=None: {
            "ok": True,
            "text": "Pusty ciemny ekran.",
            "locale": "pl",
            "scene_class": "empty_dark_screen",
            "llm_hint": {"send_to_llm": False},
        },
    )

    result = execute(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output=str(png),
            source="DP-1",
        )
    )
    assert result.ok is True
    assert result.data["nl"] == "Pusty ciemny ekran."
    assert result.data["img2nl"]["scene_class"] == "empty_dark_screen"


def test_execute_screenshot_skip_img2nl(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    png = tmp_path / "host.png"
    png.write_bytes(_make_png(16, 16, (255, 255, 255)))

    monkeypatch.setattr(
        "vdisplay.application.executor.execute_local",
        lambda cmd: {"saved": str(png), "mode": "host"},
    )

    def fail_analyze(*args, **kwargs):
        raise AssertionError("img2nl should be skipped")

    monkeypatch.setattr(img2nl_enrich, "describe_screenshot_image", fail_analyze)

    result = execute(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output=str(png),
            extra={"skip_img2nl": True},
        )
    )
    assert result.ok is True
    assert "nl" not in result.data
