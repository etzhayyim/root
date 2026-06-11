#!/usr/bin/env python3
"""Parity + invariant drift-lock for the 助 (tasuke) browser-local app (app/index.html).

The browser app reimplements the core in JS so a victim needs no install. This guards that it can
never drift from the kotoba ontology, AND that it keeps its load-bearing promises STRUCTURALLY:
  - its closed vocab (scam-kinds / doc-kinds / free-window codes) == the ontology;
  - it makes NO network call (no fetch / XHR / form action / external src) — the G6/G7 on-device,
    no-server-key, PII-never-leaves-the-device guarantee, as a property of the file;
  - it states free (¥0), member-submitted, and on-device.
"""
from __future__ import annotations

import pathlib
import re

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_APP = _ROOT / "app" / "index.html"
_ONTOLOGY = _ROOT.parents[1] / "00-contracts" / "schemas" / "cybercrime-victim-support-ontology.kotoba.edn"


def _html() -> str:
    return _APP.read_text(encoding="utf-8")


def _js_array(name: str) -> list[str]:
    m = re.search(rf"const {name}\s*=\s*\[(.*?)\];", _html(), re.S)
    assert m, f"{name} array not found in app"
    return re.findall(r'"([^"]+)"', m.group(1))


def _onto_kw(key: str) -> set[str]:
    return {k.lstrip(":") for k in load_edn(_ONTOLOGY)[key]}


# ── vocab parity with the ontology ───────────────────────────────────────────
def test_app_scam_kinds_match_ontology():
    assert set(_js_array("SCAM_KINDS")) == _onto_kw(":ontology/scam-kinds")


def test_app_doc_kinds_match_ontology():
    assert set(_js_array("DOC_KINDS")) == _onto_kw(":ontology/doc-kinds")


def test_app_window_codes_match_ontology():
    assert set(_js_array("WINDOW_CODES")) == _onto_kw(":ontology/referral-windows")


# ── the on-device / no-server-key guarantee, as a property of the file ───────
def test_app_makes_no_network_call():
    html = _html()
    for forbidden in ("fetch(", "XMLHttpRequest", "navigator.sendBeacon", "<form action", "websocket"):
        assert forbidden not in html.lower(), f"app must not {forbidden!r} (G6/G7 on-device, no upload)"
    # no external script/style/img src — fully self-contained
    assert not re.search(r'src\s*=\s*"https?://', html), "app must load nothing external"


# ── it states the charter promises the victim relies on ──────────────────────
def test_app_states_free_member_submitted_on_device():
    html = _html()
    assert "¥0" in html and "無料" in html
    assert "本人作成・本人提出" in html or "本人が作成・署名・提出" in html
    assert "端末" in html and "出ません" in html          # PII never leaves the device
    assert "did:web:etzhayyim.com:actor:tasuke" in html    # it is the etzhayyim.com actor


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_app_parity.py")
    sys.exit(1 if failed else 0)
