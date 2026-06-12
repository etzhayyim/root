"""_t.py — minimal stdlib test harness (no pytest)."""
from __future__ import annotations


def expect_raises(fn, *, contains: str = ""):
    try:
        fn()
    except Exception as e:  # noqa: BLE001 — the test asserts an exception is raised
        if contains and contains not in str(e):
            raise AssertionError(f"raised {e!r} but expected substring {contains!r}") from None
        return
    raise AssertionError(f"expected an exception (containing {contains!r}) but none was raised")


def run(label: str, tests: list) -> None:
    passed = 0
    for name, fn in tests:
        fn()
        passed += 1
    print(f"[{label}] {passed}/{len(tests)} passed")
