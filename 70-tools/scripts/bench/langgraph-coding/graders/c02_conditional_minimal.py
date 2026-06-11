"""c02_conditional_minimal — minimal add_conditional_edges (no complexity)."""

from __future__ import annotations

import re

from ._lib import exec_code, extract_code


def check(generation: str) -> tuple[bool, str]:
    code = extract_code(generation)
    if code is None:
        return False, "no python code block found"
    if "add_conditional_edges" not in code:
        return False, "missing add_conditional_edges"
    rc, out, err = exec_code(code, timeout_s=15)
    if rc != 0:
        return False, f"exec rc={rc} stderr={err[:200]!r}"
    if "yes" not in out.lower():
        return False, f"expected 'yes' in stdout, got {out[:200]!r}"
    return True, "ok"
