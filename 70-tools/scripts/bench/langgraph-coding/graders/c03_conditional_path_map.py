"""c03_conditional_path_map — add_conditional_edges with path_map dict (3-way)."""

from __future__ import annotations

import re

from ._lib import exec_code, extract_code


def check(generation: str) -> tuple[bool, str]:
    code = extract_code(generation)
    if code is None:
        return False, "no python code block found"
    if "add_conditional_edges" not in code:
        return False, "missing add_conditional_edges"
    # path_map / mapping dict is the standard way to translate router-string -> node
    if not re.search(r"\{\s*['\"]\w+['\"]\s*:", code):
        return False, "missing path-map-like dict literal"
    rc, out, err = exec_code(code, timeout_s=15)
    if rc != 0:
        return False, f"exec rc={rc} stderr={err[:200]!r}"
    # n=-3 → neg, n=0 → zero, n=7 → pos. Expect "neg zero pos" in some order.
    if not all(w in out.lower() for w in ("neg", "zero", "pos")):
        return False, f"expected neg/zero/pos in stdout, got {out[:200]!r}"
    return True, "ok"
