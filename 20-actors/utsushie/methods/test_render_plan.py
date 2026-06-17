#!/usr/bin/env python3
"""utsushie 写し絵 — tests for the offline render-plan builder + R0 render guard.

Standalone-runnable (`python3 test_render_plan.py`) AND pytest-compatible.
Asserts the U1–U6 charter gates are enforced in code (mirroring lex/video.edn).
"""
from __future__ import annotations

from render_plan import build_plan, render, CharterRefusal, EXCERPT_MAX

_ART = {
    "articleId": "a1", "kind": "mirror", "section": "国際",
    "headline": "見出し", "excerpt": "短い要約。",
    "url": "https://example.org/a", "outlet": "outlet.x",
}


def test_build_plan_ok():
    p = build_plan(_ART, langs=["ja", "en"])
    assert p["sourceArticleId"] == "a1"
    assert p["kind"] == "mirror"
    assert p["langs"] == ["ja", "en"]
    assert p["narrator"] == "synthetic-neutral"
    assert p["blobMime"] == "video/mp4"


def test_narration_bounded_to_excerpt():
    p = build_plan(_ART)
    assert len(p["narrationScript"]) <= EXCERPT_MAX  # U2 / G4


def test_all_gate_witnesses_false():
    p = build_plan(_ART)
    assert p["gates"] == {
        "verdict": False, "fullTextNarration": False, "depictsPerson": False,
        "voiceClone": False, "engagementOptimized": False,
        "externalGpuRender": False, "serverHeldKey": False,
    }


def test_g11_refuses_original_kind():
    try:
        build_plan({**_ART, "kind": "original"})
        assert False, "expected CharterRefusal for kind=original"
    except CharterRefusal as e:
        assert "G11" in str(e)


def test_g4_refuses_oversized_excerpt():
    big = {**_ART, "excerpt": "x" * (EXCERPT_MAX + 1)}
    try:
        build_plan(big)
        assert False, "expected CharterRefusal for full-text narration"
    except CharterRefusal as e:
        assert "U2" in str(e) or "G4" in str(e)


def test_u3_refuses_person_depiction():
    try:
        build_plan({**_ART, "depictsPerson": True})
        assert False, "expected anti-deepfake refusal"
    except CharterRefusal as e:
        assert "anti-deepfake" in str(e)


def test_u3_refuses_voice_clone():
    try:
        build_plan({**_ART, "voiceClone": True})
        assert False, "expected anti-deepfake refusal"
    except CharterRefusal as e:
        assert "anti-deepfake" in str(e)


def test_mirror_requires_url():
    try:
        build_plan({**_ART, "url": ""})
        assert False, "expected refusal: mirror needs a link-out"
    except CharterRefusal as e:
        assert "G4" in str(e)


def test_render_is_r0_gated():
    try:
        render({})
        assert False, "expected RuntimeError at R0"
    except RuntimeError as e:
        assert "G8" in str(e) and "Murakumo" in str(e)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"utsushie/render_plan: {len(fns)} tests passed")


if __name__ == "__main__":
    _run()
