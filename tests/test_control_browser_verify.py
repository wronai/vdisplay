"""DOM verify for browser actions (PR-13)."""

from __future__ import annotations

from vdisplay.control.providers.browser_playwright import BrowserPlaywrightProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.control.verifier import VerifierPipeline, VerifyContext
from fixtures.fake_browser import FakePage


def test_dom_verify_set_value() -> None:
    page = FakePage()
    provider = BrowserPlaywrightProvider(page=page)
    selector = ControlSelector(dom_css='input[name="query"]')
    matches = provider.find(selector)
    target = matches[0]
    before = provider.snapshot()

    provider.set_value(target.id, "hello")
    after = provider.snapshot()

    pipeline = VerifierPipeline()
    result = pipeline.verify_after_action(
        VerifyContext(
            action_provider=provider,
            before_snapshot=before,
            target=target,
            action="set_value",
            selector=selector,
            value="hello",
            verify_semantic=True,
            verify_mode="dom",
        )
    )
    assert result.verified is True
    assert result.mode in {"dom", "semantic"}
    assert result.semantic is not None
    assert result.semantic.get("verified") is True
