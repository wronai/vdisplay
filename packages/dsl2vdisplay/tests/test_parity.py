from dsl2vdisplay import dispatch


def test_parity_info_text_vs_dict() -> None:
    r1 = dispatch("INFO")
    r2 = dispatch({"verb": "INFO"})
    assert r1.ok == r2.ok
    assert r1.action == r2.action


def test_health() -> None:
    r = dispatch("HEALTH")
    assert r.ok is True
    assert r.action == "health"
