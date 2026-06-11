"""s01_stategraph_basic — minimal StateGraph + 1 increment node."""

from __future__ import annotations

import re

from ._lib import exec_code, extract_code


def check(generation: str) -> tuple[bool, str]:
    code = extract_code(generation)
    if code is None:
        return False, "no python code block found"

    for name, pat in [
        ("StateGraph", r"from\s+langgraph\.graph\s+import[^\n]*StateGraph"),
        ("TypedDict", r"from\s+typing\s+import[^\n]*TypedDict"),
    ]:
        if not re.search(pat, code):
            return False, f"missing import: {name}"

    rc, out, err = exec_code(code, timeout_s=15)
    if rc != 0:
        return False, f"exec rc={rc} stderr={err[:200]!r}"
    if "1" not in out:
        return False, f"expected '1' in stdout, got {out[:200]!r}"
    return True, "ok"
