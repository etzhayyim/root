#!/usr/bin/env python3
"""Parser tests for _edn.py — the EDN reader every seed/ontology load depends on.

The membrane's whole hermeticity rests on this reader: a silently-wrong literal (a float read
as a string, a bareword swallowed) would corrupt a triage score or a route before any test
caught it. These pin the atom-level reads (true/false/nil, int, float, keyword-as-string,
bareword fallback, escaped string) plus nested map/vector structure. Mirrors test__edn.cljc.
"""
from __future__ import annotations

import pathlib
import tempfile

from _edn import _parse, _tokens, load_edn


def _parse_str(s: str):
    return _parse(_tokens(s))


def test_reads_true_false_nil():
    assert _parse_str("[true false nil]") == [True, False, None]


def test_reads_int_and_float_and_negative():
    assert _parse_str("[1 2.5 -3 0.65]") == [1, 2.5, -3, 0.65]


def test_keyword_stays_a_colon_string_and_bareword_falls_through_to_string():
    # a leading-colon token is kept verbatim as ":ns/name" (the repo convention)
    assert _parse_str(":edit/op") == ":edit/op"
    # a bare symbol that is neither int nor float falls through to a plain string
    assert _parse_str("org.corp.x") == "org.corp.x"


def test_reads_escaped_string():
    assert _parse_str(r'"a \"q\" b"') == 'a "q" b'


def test_reads_nested_map_and_vector_with_comments_and_commas():
    src = """; a leading comment
    {:edit/id "e1", :edit/tags [:a :b],
     :edit/ok true :edit/n 3}"""
    assert _parse_str(src) == {
        ":edit/id": "e1", ":edit/tags": [":a", ":b"],
        ":edit/ok": True, ":edit/n": 3,
    }


def test_load_edn_reads_a_file():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "x.edn"
        p.write_text('{:k [1 2.5 true nil "s"]}', encoding="utf-8")
        assert load_edn(p) == {":k": [1, 2.5, True, None, "s"]}


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test__edn.py")
    sys.exit(1 if failed else 0)
