from __future__ import annotations

import json
from importlib import resources
from typing import Any


def _load_schema(name: str) -> dict[str, Any]:
    raw = resources.files("dsl2vdisplay").joinpath(f"schema/commands/{name}.schema.json").read_text()
    return json.loads(raw)


_SCHEMAS: dict[str, dict[str, Any]] | None = None


def all_schemas() -> dict[str, dict[str, Any]]:
    global _SCHEMAS
    if _SCHEMAS is None:
        names = ["health", "info", "outputs", "screenshot", "mirror", "validate"]
        _SCHEMAS = {n.upper(): _load_schema(n) for n in names}
    return _SCHEMAS


def schema_for_verb(verb: str) -> dict[str, Any] | None:
    return all_schemas().get(verb.upper())


def validate_command_dict(cmd: dict[str, Any]) -> list[str]:
    verb = str(cmd.get("verb", "")).upper()
    schema = schema_for_verb(verb)
    if schema is None:
        return [f"unknown verb: {verb}"]
    try:
        import jsonschema
        jsonschema.validate(cmd, schema)
        return []
    except Exception as exc:
        return [str(exc)]
