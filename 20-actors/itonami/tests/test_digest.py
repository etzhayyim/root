#!/usr/bin/env python3
"""itonami 営み — R4 daily digest + Murakumo narration tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import inspect as vis  # noqa: E402
import digest  # noqa: E402

OPS = ACTOR_DIR / "data" / "seed-factory-ops.kotoba.edn"
DET = ACTOR_DIR / "data" / "seed-vision-detections.kotoba.edn"


def _build():
    stations, ticks = load(OPS)
    detections = vis.load_detections(DET)
    return digest.build_digest(stations, ticks, detections)


def test_digest_fuses_all_four_cells():
    d = _build()
    assert "line" in d and "oee" in d["line"]               # analyze
    assert "energy" in d and "energy_reduction_frac" in d["energy"]   # optimize
    assert "bottleneck" in d and d["bottleneck"]["bottleneck"] == ":st.frame-weld"
    assert d["quality"]["station"] == ":st.cab-weld"        # inspect
    assert d["quality"]["top_defect"] == ":weld-porosity"


def test_fallback_narration_is_deterministic_and_factual():
    d = _build()
    a = digest.fallback_narration(d)
    b = digest.fallback_narration(d)
    assert a == b
    assert "OEE" in a and "%" in a
    assert "Frame Weld Cell" in a  # the bottleneck is named
    assert "vision inspection" in a


def test_narration_carries_no_worker_dimension():
    """G2: the narration prompt and text must never mention a worker/person."""
    d = _build()
    for text in (digest.narration_prompt(d), digest.fallback_narration(d)):
        low = text.lower()
        for forbidden in ("worker", "operator", "person", "employee", "staff"):
            assert forbidden not in low, f"narration leaked {forbidden!r}"


def test_narration_is_murakumo_only():
    """G7: narration backend is fixed to Murakumo; no external-LLM endpoint appears."""
    d = _build()
    assert digest.NARRATION_BACKEND == "murakumo"
    assert "127.0.0.1" in digest.MURAKUMO_GATEWAY
    blob = (digest.narration_prompt(d) + digest.MURAKUMO_GATEWAY).lower()
    for forbidden in ("openai", "anthropic", "vertex", "runpod", "bedrock", "api.openai"):
        assert forbidden not in blob


def test_narrate_falls_back_when_murakumo_unreachable():
    d = _build()
    def boom(_prompt):
        raise ConnectionError("murakumo down")
    out = digest.narrate(d, murakumo_call=boom)
    assert out["backend"] == "fallback-deterministic"
    assert out["text"] == digest.fallback_narration(d)


def test_narrate_uses_murakumo_when_available():
    d = _build()
    seen = {}
    def fake_murakumo(prompt):
        seen["prompt"] = prompt
        return "narrated by murakumo"
    out = digest.narrate(d, murakumo_call=fake_murakumo)
    assert out["backend"] == "murakumo"
    assert out["text"] == "narrated by murakumo"
    assert "line OEE" in seen["prompt"]  # the facts were passed through


def test_emit_transient_only():
    d = _build()
    out = digest.emit(d, digest.narrate(d), tx=9)
    assert ":ops/digest-line-oee" in out
    assert ":ops/digest-narration-backend" in out
    for line in out.splitlines():
        if line.startswith("[") and ":ops/digest" in line:
            assert ":derived]" in line and ":bond/is-transient true" in line, line
    assert ":add]" not in out


def test_determinism():
    d = _build()
    a = digest.emit(d, digest.narrate(d), tx=1)
    d2 = _build()
    b = digest.emit(d2, digest.narrate(d2), tx=1)
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
