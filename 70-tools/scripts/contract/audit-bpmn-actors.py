#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Audit the BPMN-as-actor registration state. Read-only.

Compares git state (`00-contracts/bpmn/**/*.bpmn`) against the live
`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` tables and
surfaces drift that accumulates when multiple parties register actors
with different vertex_id conventions.

Checks:

  F1  git-only process       — BPMN file on disk with no matching
                               `bpmn_process_id` row (= unregistered)
  F2  db-only process        — `bpmn_process_id` row whose BPMN file
                               isn't in git (orphan: archived file,
                               test fixture, or stale row)
  F3  duplicate process      — multiple rows per `bpmn_process_id`
                               (version bumps expected; N>3 = suspect)
  F4  duplicate binding      — multiple rows per NSID in
                               `vertex_bpmn_lexicon_binding` — any
                               N>1 is a bug, nsid is the routing key
  F5  undeployed process     — `deployed_at IS NULL` (watcher stuck
                               or the BPMN was rejected by Zeebe)

Exit code 0 if any of F1/F4/F5 is non-empty (drift that the operator
should act on); warnings only for F2/F3.

Env:
  KOTOBA_URL    postgresql://… ;  default from Keychain etzhayyim.rw/ROOT_URL

Usage:
    70-tools/scripts/contract/audit-bpmn-actors.py
    70-tools/scripts/contract/audit-bpmn-actors.py --json
    70-tools/scripts/contract/audit-bpmn-actors.py --only-drift
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[3]
BPMN_ROOT = REPO_ROOT / "00-contracts" / "bpmn"

NS_BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"

# Canonical vertex_id format (2026-04-23 decision, see ADR-0056 addendum).
#
#   process_def  at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/{slug}-v{N}
#   binding      at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/{ns-action}-v{N}
#
# - `slug` in process_def is the kebab-case form of `bpmn_process_id`
#   (underscores → hyphens).
# - `{ns-action}` in binding is `{second-to-last}-{last}` segments of the
#   NSID (e.g. `com.etzhayyim.apps.bot.ping` → `bot-ping`).
#
# Any other vertex_id shape in these two tables is `--strict` drift.
CANONICAL_DEF_VID_RE = re.compile(
    r"^at://did:web:bpmn\.etzhayyim\.ai/com\.etzhayyim\.apps\.bpmn\.processDef/[a-z0-9][a-zA-Z0-9-]*-v\d+$"
)
CANONICAL_BIND_VID_RE = re.compile(
    r"^at://did:web:bpmn\.etzhayyim\.ai/com\.etzhayyim\.apps\.bpmn\.binding/[a-z0-9][a-zA-Z0-9-]*-v\d+$"
)


# ─── psql helper ───────────────────────────────────────────────────────


def rw_url() -> str:
    if url := os.environ.get("KOTOBA_URL"):
        return url
    try:
        out = subprocess.check_output(
            ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
            text=True,
        ).strip()
        if out:
            return out
    except subprocess.CalledProcessError:
        pass
    raise SystemExit("KOTOBA_URL not in env and not in Keychain (etzhayyim.rw/ROOT_URL)")


def query(sql: str) -> list[list[str]]:
    out = subprocess.check_output(
        ["psql", rw_url(), "-tA", "-F", "\t", "-c", sql],
        text=True, stderr=subprocess.PIPE, timeout=30,
    )
    rows: list[list[str]] = []
    for line in out.splitlines():
        if not line:
            continue
        rows.append(line.split("\t"))
    return rows


# ─── BPMN file scan ────────────────────────────────────────────────────


def scan_bpmn_files() -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for p in sorted(BPMN_ROOT.rglob("*.bpmn")):
        rel = p.relative_to(REPO_ROOT).as_posix()
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError as e:
            files.append({"path": rel, "parse_error": str(e)})
            continue

        procs: list[dict[str, Any]] = []
        for proc in root.iter(f"{{{NS_BPMN}}}process"):
            proc_id = proc.get("id") or ""
            has_timer = False
            for start in proc.iter(f"{{{NS_BPMN}}}startEvent"):
                if start.find(f"{{{NS_BPMN}}}timerEventDefinition") is not None:
                    has_timer = True
                    break
            procs.append({
                "id": proc_id,
                "is_executable": proc.get("isExecutable") == "true",
                "has_timer_start": has_timer,
            })

        files.append({
            "path": rel,
            "process_count": len(procs),
            "processes": procs,
            "byte_size": p.stat().st_size,
        })
    return files


# ─── DB scan ────────────────────────────────────────────────────────────


def scan_db() -> tuple[list[dict], list[dict]]:
    defs_raw = query(
        "SELECT vertex_id, bpmn_process_id, COALESCE(version, 0), "
        "CASE WHEN deployed_at IS NULL THEN 'false' ELSE 'true' END, "
        "COALESCE(status, ''), COALESCE(source_path, ''), "
        "COALESCE(xml_byte_size, 0), COALESCE(deployed_zeebe_key, 0) "
        "FROM vertex_bpmn_process_def"
    )
    defs = [
        {
            "vertex_id": r[0],
            "bpmn_process_id": r[1],
            "version": int(r[2] or 0),
            "deployed": r[3] == "true",
            "status": r[4],
            "source_path": r[5],
            "xml_byte_size": int(r[6] or 0),
            "deployed_zeebe_key": int(r[7] or 0),
        }
        for r in defs_raw
    ]

    binds_raw = query(
        "SELECT vertex_id, nsid, bpmn_process_id, COALESCE(bpmn_version, 0), "
        "COALESCE(result_timeout_ms, 0), COALESCE(status, '') "
        "FROM vertex_bpmn_lexicon_binding"
    )
    binds = [
        {
            "vertex_id": r[0],
            "nsid": r[1],
            "bpmn_process_id": r[2],
            "bpmn_version": int(r[3] or 0),
            "result_timeout_ms": int(r[4] or 0),
            "status": r[5],
        }
        for r in binds_raw
    ]
    return defs, binds


# ─── Drift computation ─────────────────────────────────────────────────


def compute_drift(
    files: list[dict[str, Any]], defs: list[dict[str, Any]], binds: list[dict[str, Any]]
) -> dict[str, Any]:
    git_process_ids: dict[str, list[dict[str, Any]]] = defaultdict(list)
    parse_errors: list[dict[str, Any]] = []
    for f in files:
        if "parse_error" in f:
            parse_errors.append(f)
            continue
        for p in f["processes"]:
            git_process_ids[p["id"]].append({"path": f["path"], **p})

    db_process_ids: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in defs:
        db_process_ids[d["bpmn_process_id"]].append(d)

    # F1 — BPMN in git, no DB row
    git_only: list[dict[str, Any]] = []
    for pid, entries in git_process_ids.items():
        if pid not in db_process_ids:
            for e in entries:
                git_only.append({"bpmn_process_id": pid, **e})

    # F2 — DB row, no BPMN file with that process id
    db_only: list[dict[str, Any]] = []
    for pid, rows in db_process_ids.items():
        if pid not in git_process_ids:
            for r in rows:
                db_only.append(r)

    # F3 — multiple DB rows per process (N>1 info, N>3 warning)
    duplicate_defs: list[dict[str, Any]] = []
    for pid, rows in db_process_ids.items():
        if len(rows) > 1:
            duplicate_defs.append({
                "bpmn_process_id": pid,
                "count": len(rows),
                "vertex_ids": sorted(r["vertex_id"] for r in rows),
            })

    # F4 — multiple binding rows per NSID
    binds_by_nsid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for b in binds:
        binds_by_nsid[b["nsid"]].append(b)
    duplicate_bindings: list[dict[str, Any]] = []
    for nsid, rows in binds_by_nsid.items():
        if len(rows) > 1:
            duplicate_bindings.append({
                "nsid": nsid,
                "count": len(rows),
                "vertex_ids": sorted(r["vertex_id"] for r in rows),
                "process_ids": sorted({r["bpmn_process_id"] for r in rows}),
            })

    # F5 — undeployed (deployed_at IS NULL)
    undeployed = [d for d in defs if not d["deployed"] and d.get("status") != "archived"]

    # Cross-reference: bindings to process ids that don't exist
    db_pids = set(db_process_ids.keys())
    orphan_bindings = [b for b in binds if b["bpmn_process_id"] not in db_pids]

    # Informational: timer-start BPMNs (no binding expected)
    timer_processes: list[dict[str, Any]] = []
    for pid, entries in git_process_ids.items():
        for e in entries:
            if e.get("has_timer_start"):
                timer_processes.append({"bpmn_process_id": pid, "path": e["path"]})

    # F6 — non-canonical vertex_id (enforced only by --strict).
    # Archived rows are tombstoned; their vid shape doesn't matter
    # because the dispatcher + watcher both filter on status='active'.
    noncanonical_defs = [
        d for d in defs
        if d.get("status") != "archived" and not CANONICAL_DEF_VID_RE.match(d["vertex_id"])
    ]
    noncanonical_binds = [
        b for b in binds
        if b.get("status") != "archived" and not CANONICAL_BIND_VID_RE.match(b["vertex_id"])
    ]

    return {
        "parse_errors":        parse_errors,
        "git_only":            sorted(git_only, key=lambda x: x["bpmn_process_id"]),
        "db_only":             sorted(db_only, key=lambda x: (x["bpmn_process_id"], x["vertex_id"])),
        "duplicate_defs":      sorted(duplicate_defs, key=lambda x: -x["count"]),
        "duplicate_bindings":  sorted(duplicate_bindings, key=lambda x: -x["count"]),
        "undeployed":          sorted(undeployed, key=lambda x: x["vertex_id"]),
        "orphan_bindings":     sorted(orphan_bindings, key=lambda x: x["nsid"]),
        "timer_processes":     sorted(timer_processes, key=lambda x: x["bpmn_process_id"]),
        "noncanonical_defs":   sorted(noncanonical_defs, key=lambda x: x["vertex_id"]),
        "noncanonical_binds":  sorted(noncanonical_binds, key=lambda x: x["vertex_id"]),
        "counts": {
            "git_files":       len(files),
            "git_processes":   sum(len(e) for e in git_process_ids.values()),
            "db_defs":         len(defs),
            "db_bindings":     len(binds),
            "distinct_nsids":  len(binds_by_nsid),
        },
    }


# ─── Pretty printer ────────────────────────────────────────────────────


def print_report(d: dict[str, Any], only_drift: bool = False, strict: bool = False) -> int:
    counts = d["counts"]
    print(f"git: {counts['git_files']} files, {counts['git_processes']} processes")
    print(f"db:  {counts['db_defs']} process_def rows, {counts['db_bindings']} bindings ({counts['distinct_nsids']} distinct NSIDs)")
    print()

    problems = 0

    if d["parse_errors"]:
        print(f"[parse errors] {len(d['parse_errors'])}")
        for e in d["parse_errors"]:
            print(f"  - {e['path']}: {e['parse_error']}")
        problems += len(d["parse_errors"])
        print()

    if d["git_only"]:
        print(f"[F1 git-only ({len(d['git_only'])})] BPMN on disk, no process_def row:")
        for e in d["git_only"]:
            print(f"  - {e['bpmn_process_id']:34s} {e['path']}")
        problems += len(d["git_only"])
        print()

    if d["undeployed"]:
        print(f"[F5 undeployed ({len(d['undeployed'])})] watcher hasn't stamped deployed_at:")
        for r in d["undeployed"]:
            print(f"  - {r['vertex_id']:60s} process={r['bpmn_process_id']}")
        problems += len(d["undeployed"])
        print()

    if d["duplicate_bindings"]:
        print(f"[F4 duplicate bindings ({len(d['duplicate_bindings'])})] multiple rows for same NSID — routing ambiguous:")
        for e in d["duplicate_bindings"]:
            print(f"  - {e['nsid']:42s} ×{e['count']}  → {','.join(e['process_ids'])}")
            for vid in e["vertex_ids"]:
                print(f"      vid: {vid}")
        problems += len(d["duplicate_bindings"])
        print()

    if d["orphan_bindings"]:
        print(f"[orphan bindings ({len(d['orphan_bindings'])})] binding → non-existent process_def:")
        for b in d["orphan_bindings"]:
            print(f"  - {b['nsid']:42s} → {b['bpmn_process_id']} (no matching process_def row)")
        problems += len(d["orphan_bindings"])
        print()

    if strict:
        nc_def = d["noncanonical_defs"]
        nc_bind = d["noncanonical_binds"]
        if nc_def or nc_bind:
            print(f"[F6 non-canonical vertex_ids ({len(nc_def) + len(nc_bind)})] — canonical form is")
            print(f"     at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.{{processDef|binding}}/{{slug}}-v{{N}}")
            for d_ in nc_def:
                print(f"  def   {d_['vertex_id']}")
            for b_ in nc_bind:
                print(f"  bind  {b_['vertex_id']}  ({b_.get('nsid','?')})")
            problems += len(nc_def) + len(nc_bind)
            print()

    if only_drift:
        return 0 if problems == 0 else 1

    if d["duplicate_defs"]:
        print(f"[F3 multi-version process_defs ({len(d['duplicate_defs'])})] informational — version bumps expected:")
        for e in d["duplicate_defs"]:
            tag = "warn" if e["count"] > 3 else "info"
            print(f"  [{tag}] {e['bpmn_process_id']:34s} ×{e['count']}")
            for vid in e["vertex_ids"]:
                print(f"      vid: {vid}")
        print()

    if d["db_only"]:
        print(f"[F2 db-only ({len(d['db_only'])})] process_def row, no BPMN file in git:")
        for r in d["db_only"]:
            print(f"  - {r['bpmn_process_id']:34s} v{r['version']}  src={r.get('source_path') or '(blank)'}")
        print()

    if d["timer_processes"]:
        print(f"[timer-start processes ({len(d['timer_processes'])})] no lexicon binding expected (fired by Zeebe timer):")
        for e in d["timer_processes"]:
            print(f"  - {e['bpmn_process_id']:34s} {e['path']}")
        print()

    if problems == 0:
        print("no drift detected in {F1, F4, F5, parse_errors, orphan_bindings}. ✓")
        return 0
    return 1


# ─── main ──────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="emit full JSON report")
    ap.add_argument("--only-drift", action="store_true",
                    help="suppress F2/F3/timer sections (CI-friendly)")
    ap.add_argument("--strict", action="store_true",
                    help="also flag non-canonical vertex_id shapes (F6)")
    args = ap.parse_args()

    files = scan_bpmn_files()
    defs, binds = scan_db()
    drift = compute_drift(files, defs, binds)

    if args.json:
        print(json.dumps(drift, indent=2, sort_keys=True))
        hard = list(drift["git_only"]) + list(drift["duplicate_bindings"]) \
            + list(drift["undeployed"]) + list(drift["parse_errors"]) \
            + list(drift["orphan_bindings"])
        if args.strict:
            hard += list(drift["noncanonical_defs"]) + list(drift["noncanonical_binds"])
        return 1 if hard else 0

    return print_report(drift, only_drift=args.only_drift, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
