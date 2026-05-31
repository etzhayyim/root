"""i02_interrupt_minimal — minimal interrupt+resume (probes basic API knowledge)."""

from __future__ import annotations

import re

from ._lib import exec_code, extract_code


def check(generation: str) -> tuple[bool, str]:
    code = extract_code(generation)
    if code is None:
        return False, "no python code block found"
    for name, pat in [("interrupt", r"\binterrupt\s*\("),
                       ("MemorySaver", r"MemorySaver"),
                       ("Command", r"\bCommand\s*\(")]:
        if not re.search(pat, code):
            return False, f"missing: {name}"
    # the antipattern from baseline i01: compile(config=...) — flag if present
    if re.search(r"compile\([^)]*config\s*=", code):
        return False, "antipattern: compile(config=...) — config goes on invoke()/stream()"
    rc, out, err = exec_code(code, timeout_s=20)
    if rc != 0:
        return False, f"exec rc={rc} stderr={err[:200]!r}"
    if "hello" not in out.lower():
        return False, f"expected 'hello' in stdout, got {out[:200]!r}"
    return True, "ok"
