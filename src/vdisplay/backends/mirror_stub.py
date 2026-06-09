from __future__ import annotations

from .base import BaseBackend
from ..models import Capabilities, SessionInfo

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0dIDATx\x9cc````\x00\x00\x00\x05\x00\x01"
    b"\x0d\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class MirrorStubBackend(BaseBackend):
    name = "mirror-stub"

    def __init__(self, source: str = "primary", target: str = "virtual:1") -> None:
        super().__init__()
        self.source = source
        self.target = target

    def capabilities(self) -> Capabilities:
        return Capabilities(capture=True, input_control=False, mirror_config=True, isolation=False)

    def info(self) -> SessionInfo:
        return SessionInfo(
            kind="mirror",
            backend=self.name,
            active=self._active,
            source=self.source,
            target=self.target,
        )

    def screenshot_bytes(self) -> bytes:
        return PNG_1X1
