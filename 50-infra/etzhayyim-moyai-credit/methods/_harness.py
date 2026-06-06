"""Tiny standalone test harness (the repo's pytest plugin env is unreliable; each suite is
self-running, prints its own count, and exits non-zero on first failure)."""

from __future__ import annotations

import sys
import traceback
from typing import Callable, List, Tuple


def run_suite(name: str, tests: List[Tuple[str, Callable[[], None]]]) -> None:
    passed = 0
    for label, fn in tests:
        try:
            fn()
            passed += 1
        except Exception:  # noqa: BLE001 — test harness wants the full trace
            print(f"FAIL [{name}] {label}")
            traceback.print_exc()
            print(f"\n{name}: {passed}/{len(tests)} passed (FAILED at {label})")
            sys.exit(1)
    print(f"{name}: {passed}/{len(tests)} passed")


def approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol
