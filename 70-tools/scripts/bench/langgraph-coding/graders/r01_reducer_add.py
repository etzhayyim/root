"""r01_reducer_add — Annotated reducer with operator.add for list concatenation."""

from __future__ import annotations

import re

from ._lib import exec_code, extract_code


def check(generation: str) -> tuple[bool, str]:
    code = extract_code(generation)
    if code is None:
        return False, "no python code block found"

    for name, pat in [("Annotated", r"Annotated"),
                       ("operator", r"operator"),
                       ("StateGraph", r"StateGraph")]:
        if not re.search(pat, code):
            return False, f"missing: {name}"

    rc, out, err = exec_code(code, timeout_s=15)
    if rc != 0:
        return False, f"exec rc={rc} stderr={err[:200]!r}"
    if "[1, 2, 3]" not in out:
        return False, f"expected '[1, 2, 3]' in stdout, got {out[:200]!r}"
    return True, "ok"
