from vdisplay import MirrorSession, VirtualDisplaySession, WindowRelaySession, platform_summary


def test_imports():
    assert VirtualDisplaySession is not None
    assert MirrorSession is not None
    assert WindowRelaySession is not None


def test_platform_summary():
    summary = platform_summary()
    assert "platform" in summary
    assert "virtual_backend" in summary


def test_capabilities():
    virtual = VirtualDisplaySession.create()
    mirror = MirrorSession.create()
    relay = WindowRelaySession.create()
    assert virtual.capabilities()["launch"] is True
    assert mirror.capabilities()["mirror_config"] is True
    assert relay.capabilities()["window_adopt"] is True
