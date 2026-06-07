#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Migrate non-canonical `vertex_id`s in `vertex_bpmn_process_def` and
`vertex_bpmn_lexicon_binding` to the canonical AT-URI form (ADR-0056
addendum). Additive + transactional — never mutates XML or routing,
only renames the primary-key row.

Canonical scheme:
  process_def  at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/{slug}-v{N}
  binding      at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/{ns-action}-v{N}

Pattern per row:

  if canonical vid already exists:
      # the parallel registration already happened; the non-canonical
      # row is a redundant duplicate, drop it
      DELETE non-canonical

  else:
      BEGIN
      INSERT canonical row with same (bpmn_process_id, version, xml,
             xml_byte_size, source_path, status, deployed_at,
             deployed_zeebe_key, created_at, …)
      DELETE non-canonical
      COMMIT

Safety:
  - `status='archived'` rows are never touched (already retired).
  - Dry-run by default. `--apply` needed to write.
  - Runs each row's INSERT+DELETE in its own transaction; partial
    failure only leaves the row in its original state.
  - Preserves `deployed_at` + `deployed_zeebe_key` so Zeebe doesn't
    see a re-deploy, and the F5 watcher doesn't retry.

Env:
  KOTOBA_URL    postgresql://…  ;  default from Keychain etzhayyim.rw/ROOT_URL

Usage:
  migrate-bpmn-vertex-ids.py                          # dry-run (default)
  migrate-bpmn-vertex-ids.py --defs-only              # only process_def
  migrate-bpmn-vertex-ids.py --binds-only             # only lexicon_binding
  migrate-bpmn-vertex-ids.py --apply                  # write
  migrate-bpmn-vertex-ids.py --json                   # machine output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any

BPMN_REPO_PREFIX = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn"

CANONICAL_DEF_VID_RE = re.compile(
    r"^at://did:web:bpmn\.etzhayyim\.ai/com\.etzhayyim\.apps\.bpmn\.processDef/[a-z0-9][a-zA-Z0-9-]*-v\d+$"
)
CANONICAL_BIND_VID_RE = re.compile(
    r"^at://did:web:bpmn\.etzhayyim\.ai/com\.etzhayyim\.apps\.bpmn\.binding/[a-z0-9][a-zA-Z0-9-]*-v\d+$"
)


def rw_url() -> str:
    if url := os.environ.get("KOTOBA_URL"):
        return url
    out = subprocess.check_output(
        ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
        text=True,
    ).strip()
    if not out:
        raise SystemExit("KOTOBA_URL not in env and not in Keychain (etzhayyim.rw/ROOT_URL)")
    return out


def slugify(process_id: str) -> str:
    return process_id.replace("_", "-")


def canonical_def_vid(process_id: str, version: int) -> str:
    return f"{BPMN_REPO_PREFIX}.processDef/{slugify(process_id)}-v{version}"


def nsid_tail(nsid: str) -> str:
    parts = nsid.split(".")
    if len(parts) < 2:
        return nsid.replace(".", "-")
    return f"{parts[-2]}-{parts[-1]}"


def canonical_bind_vid(nsid: str, version: int = 1) -> str:
    return f"{BPMN_REPO_PREFIX}.binding/{nsid_tail(nsid)}-v{version}"


def plan_defs() -> list[dict[str, Any]]:
    """Return actions to canonicalize vertex_bpmn_process_def."""
    import psycopg2
    actions: list[dict[str, Any]] = []
    with psycopg2.connect(rw_url()) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT vertex_id, bpmn_process_id, version, COALESCE(status, 'active') "
            "FROM vertex_bpmn_process_def"
        )
        all_rows = cur.fetchall()
        existing_vids = {r[0] for r in all_rows}
        for vid, proc_id, version, status in all_rows:
            if CANONICAL_DEF_VID_RE.match(vid):
                continue
            if status == "archived":
                actions.append({"kind": "skip-archived", "from": vid,
                                "reason": f"{proc_id} v{version} archived"})
                continue
            new_vid = canonical_def_vid(proc_id, int(version or 1))
            if new_vid == vid:
                continue  # shouldn't happen, but be defensive
            if new_vid in existing_vids:
                actions.append({"kind": "delete-duplicate", "from": vid,
                                "canonical": new_vid,
                                "reason": f"{proc_id} v{version} canonical already present"})
            else:
                actions.append({"kind": "rename", "from": vid, "to": new_vid,
                                "reason": f"{proc_id} v{version}"})
    return actions


def plan_binds() -> list[dict[str, Any]]:
    import psycopg2
    actions: list[dict[str, Any]] = []
    with psycopg2.connect(rw_url()) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT vertex_id, nsid, bpmn_process_id, "
            "COALESCE(bpmn_version, 1), COALESCE(status, 'active') "
            "FROM vertex_bpmn_lexicon_binding"
        )
        all_rows = cur.fetchall()
        existing_vids = {r[0] for r in all_rows}
        for vid, nsid, proc_id, bver, status in all_rows:
            if CANONICAL_BIND_VID_RE.match(vid):
                continue
            if status == "archived":
                actions.append({"kind": "skip-archived", "from": vid,
                                "reason": f"{nsid} archived"})
                continue
            new_vid = canonical_bind_vid(nsid, int(bver or 1))
            if new_vid == vid:
                continue
            if new_vid in existing_vids:
                actions.append({"kind": "delete-duplicate", "from": vid,
                                "canonical": new_vid,
                                "reason": f"{nsid} canonical already present"})
            else:
                actions.append({"kind": "rename", "from": vid, "to": new_vid,
                                "reason": f"{nsid} → {proc_id}"})
    return actions


def apply_defs(actions: list[dict[str, Any]]) -> int:
    import psycopg2
    applied = 0
    for a in actions:
        if a["kind"] == "skip-archived":
            continue
        conn = psycopg2.connect(rw_url())
        try:
            with conn, conn.cursor() as cur:
                if a["kind"] == "delete-duplicate":
                    cur.execute(
                        "DELETE FROM vertex_bpmn_process_def WHERE vertex_id = %s",
                        (a["from"],),
                    )
                    applied += 1
                elif a["kind"] == "rename":
                    # Copy full row verbatim except vertex_id.
                    cur.execute(
                        "INSERT INTO vertex_bpmn_process_def ("
                        "vertex_id, bpmn_process_id, version, xml, xml_byte_size, "
                        "source_path, deployed_at, deployed_zeebe_key, status, "
                        "created_at, org_id, user_id, actor_id, "
                        "sensitivity_ord, owner_did) "
                        "SELECT %s, bpmn_process_id, version, xml, xml_byte_size, "
                        "source_path, deployed_at, deployed_zeebe_key, status, "
                        "created_at, org_id, user_id, actor_id, "
                        "sensitivity_ord, owner_did "
                        "FROM vertex_bpmn_process_def WHERE vertex_id = %s",
                        (a["to"], a["from"]),
                    )
                    cur.execute(
                        "DELETE FROM vertex_bpmn_process_def WHERE vertex_id = %s",
                        (a["from"],),
                    )
                    applied += 1
        finally:
            conn.close()
    return applied


def apply_binds(actions: list[dict[str, Any]]) -> int:
    import psycopg2
    applied = 0
    for a in actions:
        if a["kind"] == "skip-archived":
            continue
        conn = psycopg2.connect(rw_url())
        try:
            with conn, conn.cursor() as cur:
                if a["kind"] == "delete-duplicate":
                    cur.execute(
                        "DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = %s",
                        (a["from"],),
                    )
                    applied += 1
                elif a["kind"] == "rename":
                    cur.execute(
                        "INSERT INTO vertex_bpmn_lexicon_binding ("
                        "vertex_id, nsid, bpmn_process_id, bpmn_version, "
                        "result_timeout_ms, status, created_at, "
                        "org_id, user_id, actor_id, sensitivity_ord, owner_did) "
                        "SELECT %s, nsid, bpmn_process_id, bpmn_version, "
                        "result_timeout_ms, status, created_at, "
                        "org_id, user_id, actor_id, sensitivity_ord, owner_did "
                        "FROM vertex_bpmn_lexicon_binding WHERE vertex_id = %s",
                        (a["to"], a["from"]),
                    )
                    cur.execute(
                        "DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = %s",
                        (a["from"],),
                    )
                    applied += 1
        finally:
            conn.close()
    return applied


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="execute (default: dry-run)")
    ap.add_argument("--defs-only", action="store_true", help="only vertex_bpmn_process_def")
    ap.add_argument("--binds-only", action="store_true", help="only vertex_bpmn_lexicon_binding")
    ap.add_argument("--json", action="store_true", help="machine output")
    args = ap.parse_args()

    do_defs = not args.binds_only
    do_binds = not args.defs_only

    def_actions = plan_defs() if do_defs else []
    bind_actions = plan_binds() if do_binds else []

    def _count(actions: list[dict[str, Any]]) -> dict[str, int]:
        out: dict[str, int] = {}
        for a in actions:
            out[a["kind"]] = out.get(a["kind"], 0) + 1
        return out

    report = {
        "mode":          "apply" if args.apply else "dry-run",
        "defs":          {"total": len(def_actions), **_count(def_actions)},
        "binds":         {"total": len(bind_actions), **_count(bind_actions)},
        "def_actions":   def_actions,
        "bind_actions":  bind_actions,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"migrate-bpmn-vertex-ids: mode={report['mode']}")
        if do_defs:
            print(f"  process_def:  {report['defs']}")
        if do_binds:
            print(f"  binding:      {report['binds']}")
        for label, actions in (("process_def", def_actions), ("binding", bind_actions)):
            if not actions:
                continue
            print(f"\n{label} actions:")
            for a in actions:
                if a["kind"] == "rename":
                    print(f"  rename    {a['from']}")
                    print(f"     →      {a['to']}")
                    print(f"            ({a['reason']})")
                elif a["kind"] == "delete-duplicate":
                    print(f"  delete    {a['from']}   (canonical exists: {a['canonical']})")
                elif a["kind"] == "skip-archived":
                    print(f"  skip      {a['from']}   (archived)")

    if not args.apply:
        if def_actions or bind_actions:
            if not args.json:
                print("\n(dry-run — pass --apply to write)")
        return 0

    applied_defs = apply_defs(def_actions) if do_defs else 0
    applied_binds = apply_binds(bind_actions) if do_binds else 0
    if not args.json:
        print(f"\napplied: defs={applied_defs}  binds={applied_binds}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
