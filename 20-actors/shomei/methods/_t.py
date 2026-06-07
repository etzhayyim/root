"""Tiny standalone test harness (no pytest) — shared by shomei test_*.py. ADR-2606072100.

Each test file builds a list of (name, fn) and calls run(name, cases). A case passes if it returns
without raising; failures print and the process exits non-zero. Mirrors the keizu/ake convention so
`./run_tests.sh` aggregates every suite.
"""
from __future__ import annotations

import sys
import traceback


def run(suite: str, cases: list[tuple]) -> None:
    passed = failed = 0
    for name, fn in cases:
        try:
            fn()
            passed += 1
        except Exception:
            failed += 1
            print(f"  FAIL {name}")
            traceback.print_exc()
    total = passed + failed
    print(f"[{suite}] {passed}/{total} passed")
    if failed:
        sys.exit(1)


def expect_raises(fn, *, contains: str = "") -> None:
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        if contains and contains not in str(e):
            raise AssertionError(f"raised but missing {contains!r}: {e}") from None
        return
    raise AssertionError("expected an exception, none raised")
