#!/usr/bin/env python3
"""CI grep gate — forbid Modal Labs server references in kotoba_murakumo source.

Enforces ADR-2605282000 N1: NEVER call Modal Labs servers (modal.com /
api.modal.com) from any kotoba_murakumo runtime code path.

Allow-list (matched after the violation regex, so an excluded file never
triggers): README.md trademark notice + ADR-2605282000 trademark mention.

Exit codes:
    0 — clean (no violations)
    1 — at least one violation found

Usage::

    python3 70-tools/scripts/lint/verify_no_modal_labs_calls.py
    python3 70-tools/scripts/lint/verify_no_modal_labs_calls.py --root <path>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Repo-root-relative path to the runtime source tree we guard.
# kotoba_murakumo was integrated into the kotoba submodule (ADR re-integration,
# 2026-06-07); it now lives at 40-engine/kotoba/py/kotoba_murakumo/.
_PACKAGE_ROOT = Path("40-engine/kotoba/py/kotoba_murakumo/kotoba_murakumo")

# Patterns that constitute a violation of ADR-2605282000 N1.
# Word-boundary anchors keep false positives off (e.g. "promodal" doesn't match).
_VIOLATION_RE = re.compile(
    r"(?:\bhttps?://(?:api\.)?modal\.com\b"
    r"|\bapi\.modal\.com\b"
    r"|\bmodal\.com/[A-Za-z0-9_\-/]+"
    r"|\bfrom\s+modal\s+import\b"
    r"|\bimport\s+modal\s*$"
    r"|\bimport\s+modal\s+as\b)",
    re.MULTILINE,
)

# Suffixes we walk.
_EXTS = {".py"}


def find_violations(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    pkg = root / _PACKAGE_ROOT
    if not pkg.exists():
        # Repo layout sanity check; not a violation by itself.
        print(f"warning: {pkg} not found (expected when running outside repo)",
              file=sys.stderr)
        return findings

    for path in sorted(pkg.rglob("*")):
        if not path.is_file() or path.suffix not in _EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in _VIOLATION_RE.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            findings.append((path.relative_to(root), line_no, m.group(0)))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parents[3],
        type=Path,
        help="repo root (default: auto-detect from script location)",
    )
    args = parser.parse_args()

    findings = find_violations(args.root)
    if not findings:
        print("no-modal-labs-calls gate: clean (kotoba_murakumo runtime "
              "source does not reference modal.com / api.modal.com / modal import)")
        return 0

    print("ADR-2605282000 N1 violation: kotoba_murakumo source references "
          "Modal Labs (forbidden per Murakumo-only invariant ADR-2605215000):",
          file=sys.stderr)
    for path, line_no, match in findings:
        print(f"  {path}:{line_no}: {match!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
