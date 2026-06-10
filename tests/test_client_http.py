from __future__ import annotations

import json
import urllib.error

import pytest

from vdisplay.client_http import AgentHttpTransport
from vdisplay.exceptions import VDisplayError


def test_build_request_includes_auth_and_json_body() -> None:
    transport = AgentHttpTransport("http://127.0.0.1:8765", token="secret")
    request = transport.build_request(
        "POST",
        "/controls/list",
        body={"selector": {"css": "#go"}},
    )
    assert request.full_url == "http://127.0.0.1:8765/controls/list"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer secret"
    assert request.data is not None
    assert json.loads(request.data.decode("utf-8")) == {"selector": {"css": "#go"}}


def test_request_json_flattens_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    envelope = json.dumps(
        {
            "ok": True,
            "action": "health",
            "data": {"status": "ok"},
        }
    ).encode("utf-8")

    class FakeResponse:
        def read(self) -> bytes:
            return envelope

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: FakeResponse())
    payload = AgentHttpTransport("http://127.0.0.1:8765", token="").request_json("GET", "/health")
    assert payload["status"] == "ok"
    assert payload["ok"] is True


def test_raise_on_error_payload() -> None:
    with pytest.raises(VDisplayError, match="boom"):
        AgentHttpTransport.raise_on_error({"ok": False, "error": {"message": "boom"}})


def test_http_error_message_prefers_json_detail() -> None:
    class FakeHTTPError(urllib.error.HTTPError):
        def read(self) -> bytes:
            return b'{"error": "bad request"}'

    message = AgentHttpTransport.http_error_message(
        FakeHTTPError("http://127.0.0.1:8765/health", 400, "Bad Request", {}, None)
    )
    assert message == "bad request"
