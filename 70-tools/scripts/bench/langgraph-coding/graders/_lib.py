"""Shared helpers for langgraph-coding graders (ADR-2605250400 §1.5)."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_code(generation: str) -> str | None:
    """Extract Python code from a model generation. Robust to truncation.

    Order of attempts:
      1. Closed fence: ```python ... ```
      2. Open fence (truncated): ```python ... <end-of-string>
      3. Raw code (no fence) — heuristic: contains langgraph import
    """
    m = re.search(r"```(?:python)?\s*\n(.*?)\n```", generation, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"```(?:python)?\s*\n(.*)", generation, re.DOTALL)
    if m:
        return m.group(1)
    if "from langgraph" in generation or "import langgraph" in generation:
        return generation
    return None


def exec_code(code: str, timeout_s: int = 15) -> tuple[int, str, str]:
    """Exec generated code in a subprocess. Returns (returncode, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = Path(f.name)
    try:
        p = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True, text=True, timeout=timeout_s,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"
    finally:
        path.unlink(missing_ok=True)
