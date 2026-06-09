from __future__ import annotations

from vdisplay.control.models import (
    ControlAction,
    ControlActionKind,
    ControlBounds,
    ControlNode,
    ControlRole,
    ElementCapabilities,
)


def test_element_capabilities_roundtrip() -> None:
    caps = ElementCapabilities(
        activate=True,
        focus=True,
        set_value=True,
        text_read=True,
        text_write=True,
        select=True,
        toggle=False,
        expand=True,
    )
    restored = ElementCapabilities.from_dict(caps.to_dict())
    assert restored == caps


def test_control_node_serializes_capabilities_and_actions() -> None:
    node = ControlNode(
        id="atspi:1/0/1",
        backend="atspi",
        role=ControlRole.BUTTON,
        name="Increment",
        provider_ref="/org/a11y/atspi/accessible/123",
        actions=[
            ControlAction(kind=ControlActionKind.INVOKE, name="click", description="Press"),
        ],
        capabilities=ElementCapabilities(activate=True, focus=True, toggle=True),
        bounds=ControlBounds(0, 0, 100, 30),
    )
    payload = node.to_dict()
    assert payload["provider_ref"] == "/org/a11y/atspi/accessible/123"
    assert payload["capabilities"]["activate"] is True
    assert payload["capabilities"]["toggle"] is True
    assert payload["actions"][0]["name"] == "click"


def test_atspi_snapshot_deserializes_actions_and_capabilities(monkeypatch) -> None:
    from vdisplay.control.providers.atspi import _snapshot_from_dict

    snapshot = _snapshot_from_dict(
        {
            "backend": "atspi",
            "nodes": {
                "atspi:1/0": {
                    "id": "atspi:1/0",
                    "backend": "atspi",
                    "role": "button",
                    "name": "Save",
                    "provider_ref": "/org/a11y/atspi/accessible/999",
                    "actions": [{"kind": "invoke", "name": "press", "description": "Activate"}],
                    "capabilities": {
                        "activate": True,
                        "focus": True,
                        "set_value": False,
                        "text_read": False,
                        "text_write": False,
                        "select": False,
                        "toggle": True,
                        "expand": False,
                    },
                    "state": {"role_name": "push button", "focused": False},
                }
            },
            "root_ids": ["atspi:1/0"],
        }
    )
    node = snapshot.nodes["atspi:1/0"]
    assert node.provider_ref == "/org/a11y/atspi/accessible/999"
    assert node.actions[0].name == "press"
    assert node.capabilities is not None
    assert node.capabilities.activate is True
    assert node.capabilities.toggle is True
