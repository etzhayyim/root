#!/usr/bin/env python3
# ruff: noqa: E501,T201
"""
maps3d static validation — runs offline, no Zeebe / RisingWave needed.

Layer 1 of three. Asserts that the lexicon contracts, BPMN process,
worker source, and migration are internally consistent before anything
hits the cluster.

Checks:
  1. Every `00-contracts/lexicons/com/etzhayyim/apps/maps3d/*.json` has the
     required shape (lexicon=1, id matches filename, defs.main.type
     ∈ {query, procedure}, parameters or input present, output present).
  2. `00-contracts/bpmn/com/etzhayyim/maps3d/processTile.bpmn` is well-formed
     XML, every sequenceFlow source/target exists, every exclusive
     gateway has at least 2 outgoing flows, the boundary timer is
     attached to Task_Colmap, and every `zeebe:taskDefinition type` is
     either a `generic.*` primitive or a `maps3d.*` NSID that has a
     matching lexicon JSON.
  3. Every `worker.task('maps3d.*')` registration in the LangServer
     workers under `50-infra/k8s/maps3d/workers/*.py` has a matching
     lexicon JSON, and every maps3d NSID referenced from the BPMN is
     handled by exactly one worker.
  4. Migration `30-graph/graph-schema/migrations/20260426010000_maps3d_photogrammetry.ts`
     creates `vertex_maps3d_tile` and `vertex_langgraph_state` and
     seeds the BPMN process_def + lexicon_binding rows.

Usage:
    70-tools/scripts/test/maps3d-static-validation.py
    70-tools/scripts/test/maps3d-static-validation.py --json
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LEX_DIR = REPO / "00-contracts/lexicons/com/etzhayyim/apps/maps3d"
BPMN_PATH = REPO / "00-contracts/bpmn/com/etzhayyim/maps3d/processTile.bpmn"
WORKER_DIR = REPO / "50-infra/k8s/maps3d/workers"
MIGRATION = REPO / "30-graph/graph-schema/migrations/20260426010000_maps3d_photogrammetry.ts"

NS_BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS_ZEEBE = "http://camunda.org/schema/zeebe/1.0"


@dataclass
class Result:
    passes: list[str] = field(default_factory=list)
    fails: list[str] = field(default_factory=list)

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def fail(self, msg: str) -> None:
        self.fails.append(msg)


# ─── 1. Lexicons ─────────────────────────────────────────────────────


def check_lexicons(r: Result) -> set[str]:
    """Return the set of NSIDs that have a valid lexicon JSON."""
    valid_nsids: set[str] = set()
    if not LEX_DIR.is_dir():
        r.fail(f"lexicon dir missing: {LEX_DIR}")
        return valid_nsids
    files = sorted(LEX_DIR.glob("*.json"))
    if not files:
        r.fail(f"no lexicon JSONs in {LEX_DIR}")
        return valid_nsids
    for p in files:
        try:
            doc = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            r.fail(f"{p.name}: invalid JSON ({e})")
            continue
        nsid = doc.get("id")
        expected = f"com.etzhayyim.apps.maps3d.{p.stem}"
        if doc.get("lexicon") != 1:
            r.fail(f"{p.name}: lexicon != 1")
            continue
        if nsid != expected:
            r.fail(f"{p.name}: id={nsid!r} does not match path-derived {expected!r}")
            continue
        defs = doc.get("defs") or {}
        main = defs.get("main") or {}
        kind = main.get("type")
        if kind not in ("query", "procedure"):
            r.fail(f"{p.name}: defs.main.type={kind!r} (expected query|procedure)")
            continue
        if kind == "query" and not main.get("parameters"):
            r.fail(f"{p.name}: query missing parameters")
            continue
        if kind == "procedure" and not main.get("input"):
            r.fail(f"{p.name}: procedure missing input")
            continue
        if not main.get("output"):
            r.fail(f"{p.name}: missing output")
            continue
        if not main.get("description"):
            r.fail(f"{p.name}: missing description")
            continue
        valid_nsids.add(nsid)
        r.ok(f"lexicon {p.name} ✓ ({kind})")
    return valid_nsids


# ─── 2. BPMN ─────────────────────────────────────────────────────────


def _qn(tag: str) -> str:
    """Build {ns}localname matcher."""
    if ":" not in tag:
        return f"{{{NS_BPMN}}}{tag}"
    pre, local = tag.split(":", 1)
    ns = {"bpmn": NS_BPMN, "zeebe": NS_ZEEBE}[pre]
    return f"{{{ns}}}{local}"


def check_bpmn(r: Result, lexicon_nsids: set[str]) -> tuple[set[str], set[str]]:
    """Return (all maps3d NSIDs referenced, all generic.* task types)."""
    if not BPMN_PATH.is_file():
        r.fail(f"BPMN missing: {BPMN_PATH}")
        return set(), set()
    try:
        tree = ET.parse(BPMN_PATH)
    except ET.ParseError as e:
        r.fail(f"BPMN parse: {e}")
        return set(), set()
    root = tree.getroot()
    process = root.find(_qn("bpmn:process"))
    if process is None:
        r.fail("BPMN: <bpmn:process> not found")
        return set(), set()

    # Collect IDs of every flow node.
    node_ids: set[str] = set()
    for tag in ("startEvent", "endEvent", "serviceTask", "exclusiveGateway", "boundaryEvent"):
        for el in process.iter(_qn(f"bpmn:{tag}")):
            nid = el.attrib.get("id")
            if nid:
                node_ids.add(nid)

    # sequenceFlow source/target must point at known nodes.
    flows = list(process.iter(_qn("bpmn:sequenceFlow")))
    bad_flows = []
    for f in flows:
        s, t = f.attrib.get("sourceRef"), f.attrib.get("targetRef")
        if s not in node_ids or t not in node_ids:
            bad_flows.append((f.attrib.get("id"), s, t))
    if bad_flows:
        for fid, s, t in bad_flows:
            r.fail(f"BPMN flow {fid}: dangling sourceRef={s!r} targetRef={t!r}")
    else:
        r.ok(f"BPMN sequenceFlows ✓ ({len(flows)} flows, all wired)")

    # Each exclusiveGateway needs at least 2 outgoing.
    for gw in process.iter(_qn("bpmn:exclusiveGateway")):
        gid = gw.attrib.get("id")
        outs = [f for f in flows if f.attrib.get("sourceRef") == gid]
        if len(outs) < 2:
            r.fail(f"BPMN gateway {gid}: only {len(outs)} outgoing flow(s)")
        else:
            r.ok(f"BPMN gateway {gid} ✓ ({len(outs)} outgoing)")

    # Boundary timer attached to Task_Colmap.
    found_boundary = False
    for be in process.iter(_qn("bpmn:boundaryEvent")):
        if be.attrib.get("attachedToRef") == "Task_Colmap":
            timer = be.find(_qn("bpmn:timerEventDefinition"))
            if timer is not None:
                found_boundary = True
                r.ok(f"BPMN boundary timer on Task_Colmap ✓ ({be.attrib.get('id')})")
                break
    if not found_boundary:
        r.fail("BPMN: no timer boundaryEvent attached to Task_Colmap")

    # Collect every zeebe:taskDefinition type.
    bpmn_nsids: set[str] = set()
    generic_types: set[str] = set()
    for ext in process.iter(_qn("bpmn:extensionElements")):
        for td in ext.iter(_qn("zeebe:taskDefinition")):
            t = td.attrib.get("type")
            if not t:
                continue
            if t.startswith("maps3d."):
                bpmn_nsids.add(f"com.etzhayyim.apps.{t}")
            elif t.startswith("generic."):
                generic_types.add(t)
            else:
                r.fail(f"BPMN: unknown taskDefinition type={t!r}")
    r.ok(f"BPMN task types: {len(bpmn_nsids)} maps3d.* + {len(generic_types)} generic.*")

    # Every BPMN-referenced maps3d NSID must have a lexicon.
    missing = bpmn_nsids - lexicon_nsids
    if missing:
        for n in sorted(missing):
            r.fail(f"BPMN references {n} but no lexicon JSON exists")
    else:
        r.ok("BPMN ↔ Lexicon NSID coverage ✓")

    # Lexicon NSIDs that are NOT referenced by the BPMN are fine if they
    # describe inner-task contracts only (not BPMN entry points). We
    # list them as informational but never fail on them.
    not_in_bpmn = lexicon_nsids - bpmn_nsids - {"com.etzhayyim.apps.maps3d.processTile"}
    if not_in_bpmn:
        for n in sorted(not_in_bpmn):
            # processTile is the BPMN entry, not a task type, so its
            # `type` attribute won't match.  Inner NSIDs SHOULD be in
            # the BPMN if they correspond to service tasks.  Diagnose.
            short = n.removeprefix("com.etzhayyim.apps.")
            r.fail(f"Lexicon {n} has no BPMN service task (orphan) — expected `type=\"{short}\"` somewhere")

    return bpmn_nsids, generic_types


# ─── 3. Worker registrations ─────────────────────────────────────────


def _python_task_decorators(path: Path) -> set[str]:
    """Return the set of task types registered via `@task(worker, '...')`
    or `worker.task(task_type='...')` in a Python source file."""
    src = path.read_text()
    tree = ast.parse(src)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # @task(worker, "maps3d.X")
            f = node.func
            if isinstance(f, ast.Name) and f.id == "task":
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    v = node.args[1].value
                    if isinstance(v, str):
                        found.add(v)
            # worker.task(task_type="maps3d.X")
            if isinstance(f, ast.Attribute) and f.attr == "task":
                for kw in node.keywords:
                    if kw.arg == "task_type" and isinstance(kw.value, ast.Constant):
                        v = kw.value.value
                        if isinstance(v, str):
                            found.add(v)
    return found


def check_workers(r: Result, lexicon_nsids: set[str], bpmn_nsids: set[str]) -> None:
    if not WORKER_DIR.is_dir():
        r.fail(f"workers dir missing: {WORKER_DIR}")
        return
    handlers: dict[str, list[str]] = {}
    for p in sorted(WORKER_DIR.glob("*.py")):
        # Skip private modules (`_common.py`, `_colmap.py`, ...), the
        # package marker, and test files — none of these register
        # Zeebe job handlers.
        if p.name.startswith("_") or p.name == "__init__.py" or p.name.startswith("test_"):
            continue
        try:
            tasks = _python_task_decorators(p)
        except SyntaxError as e:
            r.fail(f"{p.name}: syntax error {e}")
            continue
        if not tasks:
            r.fail(f"{p.name}: no @task decorators found (worker without tasks?)")
            continue
        for t in tasks:
            handlers.setdefault(t, []).append(p.name)

    # Every BPMN maps3d task must be handled by exactly one worker.
    expected = {n.removeprefix("com.etzhayyim.apps.") for n in bpmn_nsids}
    for t in sorted(expected):
        owners = handlers.get(t, [])
        if not owners:
            r.fail(f"BPMN task `{t}` has no worker handler")
        elif len(owners) > 1:
            r.fail(f"BPMN task `{t}` handled by multiple workers: {owners}")
        else:
            r.ok(f"worker {owners[0]} ⇒ {t} ✓")

    # Every worker task must have a matching lexicon JSON.
    for t, owners in sorted(handlers.items()):
        nsid = f"com.etzhayyim.apps.{t}"
        if nsid not in lexicon_nsids:
            r.fail(
                f"worker {owners[0]} registers `{t}` but no lexicon JSON "
                f"({LEX_DIR.relative_to(REPO)}/{t.split('.')[-1]}.json)"
            )


# ─── 4. Migration ────────────────────────────────────────────────────


def check_migration(r: Result) -> None:
    if not MIGRATION.is_file():
        r.fail(f"migration missing: {MIGRATION}")
        return
    src = MIGRATION.read_text()
    expected = [
        # Tables.
        ("CREATE TABLE", "vertex_maps3d_tile"),
        ("CREATE TABLE", "vertex_langgraph_state"),
        # BPMN registry.
        ("INSERT INTO vertex_bpmn_process_def", "maps3d_process_tile"),
        ("INSERT INTO vertex_bpmn_lexicon_binding", "com.etzhayyim.apps.maps3d.processTile"),
    ]
    for keyword, marker in expected:
        # Loose match — keyword + marker on same logical statement.
        # Migrations split across lines so we just check both appear.
        if keyword not in src or marker not in src:
            r.fail(f"migration: missing {keyword} for {marker!r}")
        else:
            r.ok(f"migration ✓ {keyword} {marker}")
    # `up()` and `down()` are required.
    if not re.search(r"export async function up\b", src):
        r.fail("migration: no `export async function up`")
    else:
        r.ok("migration: up() ✓")
    if not re.search(r"export async function down\b", src):
        r.fail("migration: no `export async function down`")
    else:
        r.ok("migration: down() ✓")


# ─── Entry ───────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit JSON report on stdout")
    args = ap.parse_args()

    r = Result()
    print(f"# maps3d static validation — repo {REPO.name}")
    print()

    lexicon_nsids = check_lexicons(r)
    bpmn_nsids, _ = check_bpmn(r, lexicon_nsids)
    check_workers(r, lexicon_nsids, bpmn_nsids)
    check_migration(r)

    if args.json:
        print(json.dumps({"passes": r.passes, "fails": r.fails}, indent=2))
    else:
        for p in r.passes:
            print(f"  PASS  {p}")
        for f in r.fails:
            print(f"  FAIL  {f}")
        print()
        print(f"== {len(r.passes)} passed · {len(r.fails)} failed ==")

    return 0 if not r.fails else 1


if __name__ == "__main__":
    sys.exit(main())
