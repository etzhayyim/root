#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Validate ADR front-matter + supersession graph + registry consistency.

Designed to run as a lefthook pre-commit / pre-push hook. Exits non-zero
on any violation. Fast enough for pre-commit (< 1s on 90 ADRs).

Checks per ADR file:
  V1  required keys present (id, title, status, doc_type)
  V2  status ∈ {active, proposed, accepted, deprecated, superseded}
  V3  status == superseded  →  superseded_by must be non-empty
  V4  supersedes: [X]       →  X file must exist AND X.superseded_by must
                              contain self (graph closure)
  V5  amends: [X]           →  X file must exist
  V6  id matches file stem  →  `id: adr-<NUM>-xxx` file `<NUM>-xxx.md`,
                              <NUM> ∈ { NNNN | YYMMDDHHMM } (timestamp form new)
  V7  every on-disk ADR has a matching registry entry (regen drift check)

Scope: only `90-docs/adr/*.md` by default. Pass --only <path glob> to scope.

Usage:
  70-tools/scripts/docs/validate-adrs.py                   # validate all
  70-tools/scripts/docs/validate-adrs.py --only 90-docs/adr/0056-*.md
  70-tools/scripts/docs/validate-adrs.py --changed-from-stdin    # lefthook
  70-tools/scripts/docs/validate-adrs.py --skip-registry-check   # fast
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
ADR_DIR = REPO / "90-docs" / "adr"
REGISTRY = REPO / "90-docs" / "_registry" / "docs.json"

VALID_STATUSES = {"active", "proposed", "accepted", "deprecated", "superseded"}

# Import the registry regen's parser to stay in sync.
sys.path.insert(0, str(Path(__file__).parent))
from importlib import util as _util
_spec = _util.spec_from_file_location(
    "regen_registry", Path(__file__).parent / "regen-registry.py",
)
_regen = _util.module_from_spec(_spec)                                   # type: ignore[arg-type]
_spec.loader.exec_module(_regen)                                         # type: ignore[union-attr]
parse_frontmatter = _regen.parse_frontmatter


# ─── Loader ────────────────────────────────────────────────────────────


def load_adr(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    fm = parse_frontmatter(text)
    if not fm:
        return None
    fm["_path"] = path
    return fm


def load_all_adrs() -> dict[str, dict[str, Any]]:
    """Map id → front-matter for every ADR on disk. id collisions keep
    the first one seen (caller decides which file is authoritative)."""
    out: dict[str, dict[str, Any]] = {}
    for p in sorted(ADR_DIR.glob("*.md")):
        if p.name in ("README.md", "template.md"):
            continue
        fm = load_adr(p)
        if fm and fm.get("id"):
            out.setdefault(fm["id"], fm)
    return out


# ─── Check harness ─────────────────────────────────────────────────────


class Violations:
    def __init__(self) -> None:
        self.by_file: dict[str, list[str]] = {}

    def add(self, path: Path, rule: str, detail: str) -> None:
        rel = path.relative_to(REPO).as_posix()
        self.by_file.setdefault(rel, []).append(f"{rule}: {detail}")

    def report(self) -> int:
        if not self.by_file:
            return 0
        total = sum(len(v) for v in self.by_file.values())
        print(f"\n{total} violation(s) across {len(self.by_file)} file(s):", file=sys.stderr)
        for f, msgs in sorted(self.by_file.items()):
            print(f"  {f}:", file=sys.stderr)
            for m in msgs:
                print(f"    - {m}", file=sys.stderr)
        return 1


# ─── Per-ADR checks ────────────────────────────────────────────────────


REQUIRED_KEYS = ("id", "title", "status", "doc_type")


def check_one(path: Path, fm: dict[str, Any], all_by_id: dict[str, dict[str, Any]],
              v: Violations) -> None:
    # V1 required keys
    for k in REQUIRED_KEYS:
        if not fm.get(k):
            v.add(path, "V1", f"missing required key `{k}`")

    # V2 status value
    status = fm.get("status")
    if status and status not in VALID_STATUSES:
        v.add(path, "V2",
              f"invalid status `{status}` (expected one of {sorted(VALID_STATUSES)})")

    # V3 superseded ⇒ superseded_by non-empty
    sb = fm.get("superseded_by") or []
    if status == "superseded" and not sb:
        v.add(path, "V3", "status is 'superseded' but `superseded_by` is empty")

    # V4 supersedes closure — for each [X], X must exist + X.superseded_by⊇self
    for sid in (fm.get("supersedes") or []):
        if not isinstance(sid, str):
            continue
        if sid not in all_by_id:
            v.add(path, "V4",
                  f"supersedes `{sid}` but no ADR with that id on disk")
            continue
        other = all_by_id[sid]
        other_sb = other.get("superseded_by") or []
        self_id = fm.get("id")
        if self_id not in other_sb:
            v.add(path, "V4",
                  f"supersedes `{sid}` but `{sid}` does not list `{self_id}` in its `superseded_by`")

    # V5 amends closure (lighter — just existence, amend is directional)
    for aid in (fm.get("amends") or []):
        if isinstance(aid, str) and aid not in all_by_id and not aid.startswith("self-"):
            v.add(path, "V5", f"amends `{aid}` but no ADR with that id on disk")

    # V6 id↔filename — accept either legacy 4-digit sequential OR the
    # 10-digit YYMMDDHHMM timestamp form (new convention 2026-04-23 onward,
    # see ADR 2604231348 timestamp-numbering-policy).
    expected_prefix = f"adr-{path.stem}"
    actual_id = fm.get("id") or ""
    if actual_id and not actual_id.startswith(expected_prefix):
        m = re.match(r"^adr-(\d{4}|\d{10})-", actual_id)
        file_m = re.match(r"^(\d{4}|\d{10})-", path.name)
        if m and file_m and m.group(1) != file_m.group(1):
            v.add(path, "V6",
                  f"id `{actual_id}` number doesn't match filename `{path.stem}`")


# ─── Registry drift ────────────────────────────────────────────────────


def check_registry(adrs: dict[str, dict[str, Any]], v: Violations) -> None:
    if not REGISTRY.exists():
        v.add(REGISTRY, "V7", "registry file not found")
        return
    try:
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as e:
        v.add(REGISTRY, "V7", f"registry parse failed: {e}")
        return
    registry_ids = {e.get("id") for e in reg.get("entries", [])}
    missing = [aid for aid in adrs.keys() if aid not in registry_ids]
    if missing:
        preview = ", ".join(missing[:5])
        more = f" +{len(missing) - 5} more" if len(missing) > 5 else ""
        v.add(REGISTRY, "V7",
              f"{len(missing)} ADR(s) on disk missing from registry ({preview}{more}) — "
              f"run 70-tools/scripts/docs/regen-registry.py")


# ─── Main ──────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="glob filter relative to repo root")
    ap.add_argument("--changed-from-stdin", action="store_true",
                    help="read newline-delimited changed file paths from stdin "
                         "(lefthook pre-commit mode)")
    ap.add_argument("--skip-registry-check", action="store_true",
                    help="skip V7 (registry drift)")
    args = ap.parse_args()

    # Always load all ADRs — graph closure needs the full set even when
    # validating a subset.
    all_by_id = load_all_adrs()

    # Resolve the scope of files we actually check per-file rules on.
    scope_paths: list[Path] = []
    if args.changed_from_stdin:
        for line in sys.stdin.read().splitlines():
            line = line.strip()
            if not line:
                continue
            p = (REPO / line).resolve()
            try:
                p.relative_to(ADR_DIR)
            except ValueError:
                continue  # not an ADR file
            if p.exists():
                scope_paths.append(p)
    elif args.only:
        scope_paths = list(REPO.glob(args.only))
        scope_paths = [p for p in scope_paths if ADR_DIR in p.parents]
    else:
        scope_paths = [p for p in sorted(ADR_DIR.glob("*.md"))
                       if p.name not in ("README.md", "template.md")]

    v = Violations()
    checked = 0
    for p in scope_paths:
        fm = load_adr(p)
        if not fm:
            v.add(p, "V1", "frontmatter missing or unparseable")
            continue
        check_one(p, fm, all_by_id, v)
        checked += 1

    # Registry drift is global, not per-file — only run when scope is global
    # or when explicitly wanted. For lefthook pre-commit on an ADR change we
    # want it to run (regenerate is cheap).
    if not args.skip_registry_check and (not args.only or scope_paths):
        check_registry(all_by_id, v)

    rc = v.report()
    if rc == 0:
        print(f"ok — {checked} ADR(s) validated, supersession graph closed, registry in sync.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
