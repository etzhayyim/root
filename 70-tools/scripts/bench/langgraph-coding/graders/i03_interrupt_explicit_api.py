"""i03_interrupt_explicit_api — explicit on the correct compile() vs invoke() split."""

from __future__ import annotations

import re

from ._lib import exec_code, extract_code


def check(generation: str) -> tuple[bool, str]:
    code = extract_code(generation)
    if code is None:
        return False, "no python code block found"
    for name, pat in [("interrupt", r"\binterrupt\s*\("),
                       ("MemorySaver", r"MemorySaver"),
                       ("compile(checkpointer", r"compile\([^)]*checkpointer"),
                       ("invoke(...config", r"invoke\([^)]*config\s*=")]:
        if not re.search(pat, code):
            return False, f"missing pattern: {name}"
    # baseline i01 antipattern
    if re.search(r"compile\([^)]*config\s*=", code):
        return False, "antipattern: compile(config=...) detected"
    rc, out, err = exec_code(code, timeout_s=20)
    if rc != 0:
        return False, f"exec rc={rc} stderr={err[:200]!r}"
    if "99" not in out:
        return False, f"expected '99' in stdout, got {out[:200]!r}"
    return True, "ok"
