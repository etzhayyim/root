"""Offline tests for the Murakumo-only charter guard (ADR-2605215000)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kotoba_e2e.murakumo as M  # noqa: E402


def _raises(fn):
    try:
        fn()
        return False
    except M.CharterInferenceViolation:
        return True


def test_loopback_allowed():
    M.assert_murakumo_only("http://127.0.0.1:4000/v1")
    M.assert_murakumo_only("http://localhost:4000/v1")


def test_lan_fleet_allowed():
    M.assert_murakumo_only("http://192.168.1.70:11434/v1")
    M.assert_murakumo_only("https://node.murakumo.etzhayyim.com/v1")


def test_commercial_endpoints_refused():
    assert _raises(lambda: M.assert_murakumo_only("https://api.openai.com/v1"))
    assert _raises(lambda: M.assert_murakumo_only("https://api.anthropic.com/v1"))
    assert _raises(lambda: M.assert_murakumo_only("https://generativelanguage.googleapis.com/v1"))
    assert _raises(lambda: M.assert_murakumo_only("https://my.openai.azure.com/v1"))
    assert _raises(lambda: M.assert_murakumo_only("https://api.runpod.ai/v2/x"))


def test_arbitrary_public_host_refused():
    # not loopback, not LAN, not a fleet domain → refused even if not on the
    # known-commercial list (allowlist, not denylist).
    assert _raises(lambda: M.assert_murakumo_only("https://example.com/v1"))
    assert _raises(lambda: M.assert_murakumo_only("https://8.8.8.8/v1"))


def test_api_key_from_env(monkeypatch=None):
    os.environ["KOTOBA_INFERENCE_API_KEY"] = "sk-test-loopback"
    try:
        assert M.resolve_api_key() == "sk-test-loopback"
    finally:
        del os.environ["KOTOBA_INFERENCE_API_KEY"]


def test_defaults_are_loopback():
    # base_url default must be the loopback gateway (never a public default).
    os.environ.pop("MURAKUMO_BASE_URL", None)
    assert "127.0.0.1:4000" in M.base_url()
    M.assert_murakumo_only(M.base_url())  # the default must itself pass the guard


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"✓ {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
