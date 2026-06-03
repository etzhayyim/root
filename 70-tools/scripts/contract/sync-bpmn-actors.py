#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Sync BPMN files on disk → `vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding`.

Pairs with `audit-bpmn-actors.py`: the audit tool tells you what's drifted;
this tool applies the canonical fix. After a successful `--apply`, running
the audit with `--only-drift --strict` against the same files should exit 0
for rows this tool owns.

Convention (canonical 2026-04-23 per ADR-0056 addendum):
  process_def vid  at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/{slug}-v{N}
  binding vid     at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/{ns-action}-v{N}

Where:
  slug       = kebab-case of the BPMN <bpmn:process id="…">
  ns-action  = last two NSID segments joined with '-' (e.g. bot-ping)
  {N}        = integer version (default 1)

Metadata discovery per BPMN file:
  1. If the <bpmn:process> has a <bpmn:documentation> child containing a
     JSON object, that JSON wins. Supported keys: `nsid`, `version`,
     `resultTimeoutMs`.
  2. Otherwise the NSID is derived from the path as
     `com.etzhayyim.apps.{parent-dir}.{camelCase(filename-no-ext)}`.
  3. Timer-start processes (startEvent with timerEventDefinition) never
     get a binding — they fire on Zeebe's schedule, not XRPC.

Behavior:
  - If canonical process_def vid exists:
      XML differs  → UPDATE xml + xml_byte_size (same vid, same version)
      XML matches  → skip (unchanged)
  - If canonical process_def vid missing → INSERT with deployed_at=NULL
    (the F5 watcher picks it up on the next 30s tick).
  - Bindings are only created when: not a timer-start, no existing binding
    row for that NSID (any vid). Keeps the tool safe against the existing
    F4 drift — if something is already bound under a non-canonical vid,
    leave it for manual migration.

Never deletes, never touches rows with status='archived'. This tool
adds/updates only.

Env:
  RW_URL   postgresql://…  ;  default from Keychain etzhayyim.rw/ROOT_URL

Usage:
  sync-bpmn-actors.py                # dry-run diff (default)
  sync-bpmn-actors.py --apply        # write
  sync-bpmn-actors.py --only NS      # scope to files under 00-contracts/bpmn/com/etzhayyim/{NS}/
  sync-bpmn-actors.py --json         # machine output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[3]
BPMN_ROOT = REPO_ROOT / "00-contracts" / "bpmn"

NS_BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMN_REPO_PREFIX = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn"

DEFAULT_RESULT_TIMEOUT_MS = 60_000


# ─── Keychain / psql ───────────────────────────────────────────────────


def rw_url() -> str:
    if url := os.environ.get("RW_URL"):
        return url
    out = subprocess.check_output(
        ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
        text=True,
    ).strip()
    if not out:
        raise SystemExit("RW_URL not in env and not in Keychain (etzhayyim.rw/ROOT_URL)")
    return out


# ─── Canonical vertex_id helpers ───────────────────────────────────────


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


NSID_SEGMENT_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*$")


def is_valid_nsid(nsid: str) -> bool:
    """AT Protocol NSID: dot-joined alphanumeric segments, each starting
    with a letter. No underscores, no hyphens. Full spec is stricter; we
    only need the segment shape for auto-derivation."""
    parts = nsid.split(".")
    if len(parts) < 3:
        return False
    return all(NSID_SEGMENT_RE.match(p) for p in parts)


def derive_nsid_from_path(path: Path) -> str | None:
    """`00-contracts/bpmn/com/etzhayyim/{ns}/{action}.bpmn` → `com.etzhayyim.apps.{ns}.{camelCase(action)}`.
    Returns None if the derived NSID wouldn't be valid (e.g. the dir name
    contains a hyphen which NSIDs don't allow). Caller should emit a
    skip action in that case — a BPMN `<bpmn:documentation>` override is
    the only way forward for such files."""
    try:
        rel = path.relative_to(BPMN_ROOT).parts
    except ValueError:
        return None
    if len(rel) < 2:
        return None
    ns = rel[-2]
    stem = path.stem
    candidate = f"com.etzhayyim.apps.{ns}.{stem}"
    return candidate if is_valid_nsid(candidate) else None


# ─── BPMN parse ────────────────────────────────────────────────────────


@dataclass
class ParsedBpmn:
    path: Path
    rel_path: str
    process_id: str
    version: int
    has_timer_start: bool
    nsid: str | None
    result_timeout_ms: int
    documentation_override: bool
    xml: str
    xml_byte_size: int


def parse_bpmn(path: Path) -> ParsedBpmn | ValueError:
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        return ValueError(f"ParseError: {e}")
    root = tree.getroot()
    proc = root.find(f"{{{NS_BPMN}}}process")
    if proc is None:
        return ValueError("no <bpmn:process>")
    proc_id = proc.get("id") or ""
    if not proc_id:
        return ValueError("<bpmn:process> missing id")

    has_timer = False
    for start in proc.iter(f"{{{NS_BPMN}}}startEvent"):
        if start.find(f"{{{NS_BPMN}}}timerEventDefinition") is not None:
            has_timer = True
            break

    doc_el = proc.find(f"{{{NS_BPMN}}}documentation")
    override_nsid = None
    override_version = None
    override_timeout = None
    documentation_override = False
    if doc_el is not None and doc_el.text:
        text = doc_el.text.strip()
        if text.startswith("{"):
            try:
                meta = json.loads(text)
                if isinstance(meta, dict):
                    documentation_override = True
                    override_nsid = meta.get("nsid")
                    override_version = meta.get("version")
                    override_timeout = meta.get("resultTimeoutMs")
            except json.JSONDecodeError:
                pass

    nsid = override_nsid or derive_nsid_from_path(path)
    version = int(override_version) if isinstance(override_version, int) else 1
    timeout = int(override_timeout) if isinstance(override_timeout, int) else DEFAULT_RESULT_TIMEOUT_MS

    xml = path.read_text(encoding="utf-8")
    return ParsedBpmn(
        path=path,
        rel_path=str(path.relative_to(REPO_ROOT)),
        process_id=proc_id,
        version=version,
        has_timer_start=has_timer,
        nsid=None if has_timer else nsid,
        result_timeout_ms=timeout,
        documentation_override=documentation_override,
        xml=xml,
        xml_byte_size=len(xml),
    )


# ─── DB read/write ─────────────────────────────────────────────────────


def psql_run(sql: str, params: list[Any] | None = None) -> list[list[str]]:
    """Run a SELECT via psql -tA, return tab-split rows. (Reads only.)"""
    args = ["psql", rw_url(), "-tA", "-F", "\t"]
    if params is None:
        args += ["-c", sql]
    else:
        import shlex
        expanded = sql
        for p in params:
            if isinstance(p, int):
                expanded = expanded.replace("?", str(p), 1)
            elif p is None:
                expanded = expanded.replace("?", "NULL", 1)
            else:
                expanded = expanded.replace("?", "'" + str(p).replace("'", "''") + "'", 1)
        args += ["-c", expanded]
    out = subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=30)
    rows: list[list[str]] = []
    for line in out.splitlines():
        if line:
            rows.append(line.split("\t"))
    return rows


def load_existing_defs() -> dict[str, dict[str, Any]]:
    """vid → row (xml_byte_size included; xml fetched on-demand per row)."""
    rows = psql_run(
        "SELECT vertex_id, bpmn_process_id, COALESCE(version,1), "
        "COALESCE(xml_byte_size,0), COALESCE(status,'active') "
        "FROM vertex_bpmn_process_def"
    )
    return {
        r[0]: {
            "vertex_id": r[0],
            "bpmn_process_id": r[1],
            "version": int(r[2]),
            "xml_byte_size": int(r[3]),
            "status": r[4],
        }
        for r in rows
    }


def load_existing_bindings() -> dict[str, list[dict[str, Any]]]:
    """nsid → list of rows (there may be >1 during F4 drift)."""
    rows = psql_run(
        "SELECT vertex_id, nsid, bpmn_process_id, COALESCE(bpmn_version,1), "
        "COALESCE(result_timeout_ms,0), COALESCE(status,'active') "
        "FROM vertex_bpmn_lexicon_binding"
    )
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(r[1], []).append({
            "vertex_id": r[0],
            "nsid": r[1],
            "bpmn_process_id": r[2],
            "bpmn_version": int(r[3]),
            "result_timeout_ms": int(r[4]),
            "status": r[5],
        })
    return out


def apply_def_insert(parsed: ParsedBpmn, vid: str) -> None:
    import psycopg2  # lazy import — only needed in --apply
    conn = psycopg2.connect(rw_url())
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO vertex_bpmn_process_def ("
                "vertex_id, bpmn_process_id, version, xml, xml_byte_size, "
                "source_path, status, created_at) "
                "SELECT %s, %s, %s, %s, %s, %s, 'active', "
                "to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') "
                "WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = %s)",
                (vid, parsed.process_id, parsed.version, parsed.xml,
                 parsed.xml_byte_size, parsed.rel_path, vid),
            )
    finally:
        conn.close()


def apply_def_update_xml(parsed: ParsedBpmn, vid: str) -> None:
    import psycopg2
    conn = psycopg2.connect(rw_url())
    try:
        with conn, conn.cursor() as cur:
            # Updating xml also clears deployed_at so the watcher re-deploys
            # the new content to Zeebe. `xml` is a reserved SQL keyword —
            # RW's parser rejects `SET xml = …` without quoting, so we
            # quote every column in the SET list uniformly.
            cur.execute(
                'UPDATE vertex_bpmn_process_def '
                'SET "xml" = %s, "xml_byte_size" = %s, "source_path" = %s, '
                '    "deployed_at" = NULL, "deployed_zeebe_key" = NULL '
                'WHERE "vertex_id" = %s',
                (parsed.xml, parsed.xml_byte_size, parsed.rel_path, vid),
            )
    finally:
        conn.close()


def apply_bind_insert(parsed: ParsedBpmn, vid: str) -> None:
    import psycopg2
    if parsed.nsid is None:
        return
    conn = psycopg2.connect(rw_url())
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO vertex_bpmn_lexicon_binding ("
                "vertex_id, nsid, bpmn_process_id, bpmn_version, "
                "result_timeout_ms, status, created_at) "
                "SELECT %s, %s, %s, %s, %s, 'active', "
                "to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') "
                "WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = %s)",
                (vid, parsed.nsid, parsed.process_id, parsed.version,
                 parsed.result_timeout_ms, vid),
            )
    finally:
        conn.close()


# ─── Planning ──────────────────────────────────────────────────────────


@dataclass
class Action:
    kind: str            # "def-insert" | "def-update" | "bind-insert" | "skip"
    vid: str
    reason: str
    parsed: ParsedBpmn | None = None


# Two-tier XML drift detection:
#   1. byte-size delta ≥ 64 → fast positive (real content edit).
#   2. byte-size delta < 64 → fetch the live xml and do exact compare.
# The byte-size-only path used to miss small-but-real edits (e.g. swapping
# an ioMapping target from `eventType`→`actor`+`action`, ~30 bytes).
XML_UPDATE_FAST_DELTA = 64


def _fetch_xml(vid: str) -> str:
    # XML can contain tabs/newlines that confuse the psql -tA split path,
    # so go through psycopg2 (param-safe, multi-line-safe).
    import psycopg2
    conn = psycopg2.connect(rw_url())
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "xml" FROM vertex_bpmn_process_def WHERE vertex_id = %s LIMIT 1', (vid,))
            row = cur.fetchone()
    finally:
        conn.close()
    return row[0] if row and row[0] else ""


def compare_xml_size(parsed: ParsedBpmn, existing: dict[str, Any]) -> bool:
    """Return True if XML differs from the row in DB."""
    delta = abs(parsed.xml_byte_size - int(existing.get("xml_byte_size") or 0))
    if delta >= XML_UPDATE_FAST_DELTA:
        return True
    # Small delta — could be whitespace OR a real small edit. Fetch + compare.
    return _fetch_xml(existing["vertex_id"]) != parsed.xml


def plan(parseds: list[ParsedBpmn], allow_def_update: bool = False) -> list[Action]:
    existing_defs = load_existing_defs()
    existing_binds_by_nsid = load_existing_bindings()
    # index bindings by bpmn_process_id too so we can detect
    # "process already bound under a different NSID" cases
    binds_by_process_id: dict[str, list[dict[str, Any]]] = {}
    for rows in existing_binds_by_nsid.values():
        for r in rows:
            binds_by_process_id.setdefault(r["bpmn_process_id"], []).append(r)
    # Archived process_ids (any version) are off-limits for new bindings —
    # they've been explicitly retired.
    archived_process_ids = {
        d["bpmn_process_id"] for d in existing_defs.values() if d.get("status") == "archived"
    }

    plan: list[Action] = []

    for p in parseds:
        vid = canonical_def_vid(p.process_id, p.version)
        if vid not in existing_defs:
            plan.append(Action("def-insert", vid,
                               f"{p.process_id} v{p.version} — new process_def",
                               parsed=p))
        else:
            row = existing_defs[vid]
            if row["status"] == "archived":
                plan.append(Action("skip", vid,
                                   f"{p.process_id} v{p.version} — archived",
                                   parsed=p))
            elif compare_xml_size(p, row):
                if allow_def_update:
                    plan.append(Action("def-update", vid,
                                       f"{p.process_id} v{p.version} — XML size {row['xml_byte_size']}→{p.xml_byte_size}",
                                       parsed=p))
                else:
                    plan.append(Action("skip", vid,
                                       f"{p.process_id} v{p.version} — XML drift "
                                       f"({row['xml_byte_size']}→{p.xml_byte_size}); "
                                       f"pass --allow-def-update to write (or bump version)",
                                       parsed=p))
            else:
                plan.append(Action("skip", vid,
                                   f"{p.process_id} v{p.version} — unchanged",
                                   parsed=p))

        # Binding safety guards:
        #  1. Timer-start processes never get a binding.
        #  2. If this process_id already has ANY binding (under any NSID),
        #     DO NOT add a second one — a different NSID may be what the
        #     owner deliberately chose (epfo.amendEcr vs path-derived
        #     epfo.amend, etc). Respect the existing binding.
        #  3. Only auto-bind when process_id is brand new in the binding
        #     table AND the file-derived NSID isn't already owned by a
        #     different process (prevents overwriting routing).
        if p.nsid:
            canonical = canonical_bind_vid(p.nsid, p.version)
            existing_for_proc = binds_by_process_id.get(p.process_id, [])
            existing_for_nsid = existing_binds_by_nsid.get(p.nsid, [])
            if p.process_id in archived_process_ids:
                plan.append(Action("skip", canonical,
                                   f"{p.nsid} — {p.process_id} is archived, not binding",
                                   parsed=p))
            elif existing_for_proc:
                plan.append(Action("skip", canonical,
                                   f"{p.nsid} — {p.process_id} already bound as "
                                   f"'{existing_for_proc[0]['nsid']}', skip",
                                   parsed=p))
            elif existing_for_nsid:
                plan.append(Action("skip", canonical,
                                   f"{p.nsid} — already bound to '{existing_for_nsid[0]['bpmn_process_id']}', skip",
                                   parsed=p))
            else:
                plan.append(Action("bind-insert", canonical,
                                   f"{p.nsid} → {p.process_id} (timeout {p.result_timeout_ms}ms)",
                                   parsed=p))

    return plan


# ─── Main ──────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="execute the plan (default: dry-run)")
    ap.add_argument("--only", help="restrict to files under 00-contracts/bpmn/com/etzhayyim/{only}/")
    ap.add_argument("--allow-def-update", action="store_true",
                    help="permit UPDATE xml on existing (process_id, version) rows. "
                         "Off by default — safer path is to bump the BPMN version.")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    scope = BPMN_ROOT / "com" / "etzhayyim"
    if args.only:
        scope = scope / args.only

    parseds: list[ParsedBpmn] = []
    errors: list[dict[str, str]] = []
    for p in sorted(scope.rglob("*.bpmn")):
        res = parse_bpmn(p)
        if isinstance(res, ValueError):
            errors.append({"path": str(p.relative_to(REPO_ROOT)), "error": str(res)})
            continue
        parseds.append(res)

    actions = plan(parseds, allow_def_update=args.allow_def_update)

    counts = {
        "files_scanned":      len(parseds),
        "parse_errors":       len(errors),
        "def_inserts":        sum(1 for a in actions if a.kind == "def-insert"),
        "def_updates":        sum(1 for a in actions if a.kind == "def-update"),
        "bind_inserts":       sum(1 for a in actions if a.kind == "bind-insert"),
        "skipped":            sum(1 for a in actions if a.kind == "skip"),
    }

    report = {
        "mode":    "apply" if args.apply else "dry-run",
        "scope":   str(scope.relative_to(REPO_ROOT)),
        "counts":  counts,
        "errors":  errors,
        "actions": [
            {"kind": a.kind, "vid": a.vid, "reason": a.reason}
            for a in actions
        ],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"sync-bpmn-actors: mode={report['mode']} scope={report['scope']}")
        print(f"  files={counts['files_scanned']}  errors={counts['parse_errors']}")
        print(f"  def-inserts={counts['def_inserts']}  def-updates={counts['def_updates']}  "
              f"bind-inserts={counts['bind_inserts']}  skipped={counts['skipped']}")
        if errors:
            print("\nerrors:")
            for e in errors:
                print(f"  ! {e['path']}  {e['error']}")
        if counts["def_inserts"] or counts["def_updates"] or counts["bind_inserts"]:
            print("\nchanges:")
            for a in actions:
                if a.kind == "skip":
                    continue
                print(f"  {a.kind:12s} {a.vid}")
                print(f"               {a.reason}")

    if not args.apply:
        if counts["def_inserts"] or counts["def_updates"] or counts["bind_inserts"]:
            if not args.json:
                print("\n(dry-run — pass --apply to write)")
        return 0

    # Apply
    applied = 0
    for a in actions:
        if a.kind == "def-insert":
            apply_def_insert(a.parsed, a.vid)   # type: ignore[arg-type]
            applied += 1
        elif a.kind == "def-update":
            apply_def_update_xml(a.parsed, a.vid)   # type: ignore[arg-type]
            applied += 1
        elif a.kind == "bind-insert":
            apply_bind_insert(a.parsed, a.vid)   # type: ignore[arg-type]
            applied += 1
    if applied:
        # RisingWave INSERTs are visibility-async — without FLUSH, immediate
        # SELECTs (the audit script that often runs right after this) miss
        # the rows we just wrote. FLUSH waits for the barrier so downstream
        # tools see a consistent post-apply DB.
        import psycopg2
        try:
            conn = psycopg2.connect(rw_url())
            try:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute("FLUSH")
            finally:
                conn.close()
        except Exception as e:
            print(f"warning: post-apply FLUSH failed ({e}) — rows may be invisible to immediate readers", file=sys.stderr)
    if not args.json:
        print(f"\napplied {applied} action(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
