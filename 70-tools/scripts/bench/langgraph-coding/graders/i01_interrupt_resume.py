"""i01_interrupt_resume — interrupt() + Command(resume=...) + MemorySaver."""

from __future__ import annotations

import re

from ._lib import exec_code, extract_code


def check(generation: str) -> tuple[bool, str]:
    code = extract_code(generation)
    if code is None:
        return False, "no python code block found"

    for name, pat in [("interrupt", r"\binterrupt\s*\("),
                       ("MemorySaver", r"MemorySaver"),
                       ("Command", r"\bCommand\s*\("),
                       ("resume", r"resume")]:
        if not re.search(pat, code):
            return False, f"missing: {name}"

    rc, out, err = exec_code(code, timeout_s=20)
    if rc != 0:
        return False, f"exec rc={rc} stderr={err[:200]!r}"
    if not re.search(r"\b42\b", out):
        return False, f"expected '42' in stdout, got {out[:200]!r}"
    return True, "ok"
