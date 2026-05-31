#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Regenerate `90-docs/_registry/docs.json` from disk front-matter.

The registry is a sidecar index used by documentation consumers and the
drift-check in `validate-adrs.py`. Markdown bodies remain canonical; this
script scans them and emits a normalized JSON table so a human or a CI
gate can see the full picture in one file.

Covered keys per entry:
    id, path, title, status, doc_type, topic, authoritative,
    authoritative_for, related, supersedes, superseded_by, amends,
    amended_by, last_verified

Idempotent. Sorts entries by `id`. Preserves existing non-ADR rows
(e.g. explanation / how-to / tutorial docs) — they're parsed the same
way.

Usage:
    70-tools/scripts/docs/regen-registry.py
    70-tools/scripts/docs/regen-registry.py --check   # exits 1 on drift
    70-tools/scripts/docs/regen-registry.py --json    # plan-only
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
REGISTRY = REPO / "90-docs" / "_registry" / "docs.json"
DOCS_ROOT = REPO / "90-docs"

# Keys we surface in the registry. Keep this list minimal and stable.
SURFACED_KEYS = (
    "id", "path", "title", "status", "doc_type", "topic",
    "authoritative", "authoritative_for", "related",
    "supersedes", "superseded_by", "amends", "amended_by",
    "depends_on",  # added cycle 64 for relation integrity coverage
    "last_verified",
)

# Valid status values. Anything else → validator flags it.
VALID_STATUSES = {"active", "proposed", "accepted", "deprecated", "superseded"}

# Valid doc_type values per 90-docs/CLAUDE.md.
VALID_DOC_TYPES = {"explanation", "reference", "how-to", "tutorial", "adr"}


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    """Tiny YAML-ish front-matter parser (flat keys + list-of-scalars).

    Avoids a PyYAML dependency to keep the script hermetic. Doesn't
    handle nested mappings, but the repo's ADR frontmatters are flat
    with only list-of-strings at most.
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    block = text[3:end].strip("\n")
    out: dict[str, Any] = {}
    current_key = None
    for raw in block.splitlines():
        # strip inline comments conservatively (only after whitespace + '#')
        line = re.sub(r"\s+#.*$", "", raw)
        if not line.strip():
            current_key = None
            continue
        if line.startswith("  - ") or line.startswith("- "):
            item = line.lstrip(" -").strip().strip('"').strip("'")
            if current_key:
                out.setdefault(current_key, []).append(item)
            continue
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            current_key = None
            continue
        k, v = m.group(1), m.group(2).strip()
        if v == "" or v == "[]":
            # Empty scalar opens a list (next lines may be `- item` entries);
            # `[]` closes the list immediately.
            out[k] = []
            current_key = None if v == "[]" else k
            continue
        # scalar with possible quotes
        stripped = v.strip('"').strip("'")
        if stripped.lower() in ("true", "false"):
            out[k] = stripped.lower() == "true"
        else:
            out[k] = stripped
        current_key = None
    return out


def scan_docs() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for md in sorted(DOCS_ROOT.rglob("*.md")):
        # skip registry sidecars
        if "_registry" in md.parts:
            continue
        # skip CLAUDE.md — rule file, not a registered doc
        if md.name == "CLAUDE.md":
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = parse_frontmatter(text)
        if not fm or not fm.get("id"):
            continue
        rel = md.relative_to(REPO).as_posix()
        entry: dict[str, Any] = {"path": rel}
        for k in SURFACED_KEYS:
            if k == "path":
                continue
            if k in fm:
                entry[k] = fm[k]
        # Default shape defensiveness
        entry.setdefault("authoritative", False)
        for list_key in ("authoritative_for", "related", "supersedes",
                         "superseded_by", "amends", "amended_by"):
            if list_key not in entry or entry[list_key] is None:
                entry[list_key] = []
        entries.append(entry)
    entries.sort(key=lambda e: e.get("id", ""))
    return entries


def load_existing() -> dict[str, Any] | None:
    if not REGISTRY.exists():
        return None
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_registry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 2,
        "updated_at": datetime.date.today().isoformat(),
        "entries": entries,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if on-disk registry differs from what we'd regenerate")
    ap.add_argument("--json", action="store_true",
                    help="emit the planned registry as JSON (stdout) instead of writing")
    args = ap.parse_args()

    entries = scan_docs()
    new_reg = build_registry(entries)

    if args.json:
        print(json.dumps(new_reg, indent=2, ensure_ascii=False))
        return 0

    if args.check:
        old = load_existing() or {}
        # compare entries only (updated_at is volatile)
        old_entries = old.get("entries", [])
        if json.dumps(old_entries, sort_keys=True, ensure_ascii=False) \
                != json.dumps(entries, sort_keys=True, ensure_ascii=False):
            print(f"registry drift detected: disk={len(entries)} entries, file={len(old_entries)} entries",
                  file=sys.stderr)
            print("run: 70-tools/scripts/docs/regen-registry.py", file=sys.stderr)
            return 1
        print(f"registry in sync ({len(entries)} entries)")
        return 0

    # write
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(
        json.dumps(new_reg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {REGISTRY.relative_to(REPO)} with {len(entries)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
