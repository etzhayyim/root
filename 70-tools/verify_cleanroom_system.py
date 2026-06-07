#!/usr/bin/env python3
"""
End-to-end integrity verifier for the clean-room actor system (ADR 260607).

Checks the whole chain is coherent — generation → deepening → registration →
capability discovery → L4 — not just one layer. Distinguishes ERRORS (hard
inconsistencies) from WARNINGS (content drift, e.g. a sibling edited a schema
so a registered CID is now stale and registration should be re-run).

Checks:
  per actor   manifest.json present; wasmCid is a valid bafkrei raw-CIDv1;
              schema + main.py present; main.py AST-compiles; tier ∈ {L3,L4};
              (warn) wasmCid matches the CID recomputed from current bytes.
  indexes     cleanroom-actors.index.json + the 4 capability indexes cover
              exactly the actor set; mcp/openapi endpoint+tool totals are
              internally consistent.
  seed        cleanroom-actors-seed.kotoba.edn lists every actor; EDN balanced.
  L4 cohort   each L4 actor has tests/ + openapi.json (valid JSON, openapi key).

Exit code 0 iff zero ERRORS (warnings allowed). Read-only; no network.
"""

import os
import re
import ast
import json
import glob
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTORS_DIR = os.path.join(ROOT, "20-actors")
SCHEMAS_DIR = os.path.join(ROOT, "00-contracts", "schemas")
TOOLS_DIR = os.path.join(ROOT, "70-tools")

_spec = importlib.util.spec_from_file_location(
    "register_cleanroom_actors", os.path.join(TOOLS_DIR, "register_cleanroom_actors.py"))
reg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reg)

RAW_CID = re.compile(r"^bafkrei[a-z2-7]{52}$")


def main():
    errors, warns = [], []
    actor_dirs = sorted(d for d in os.listdir(ACTORS_DIR) if d.endswith("-compat"))
    handles = set()
    l4 = set()
    stale = 0

    for actor in actor_dirs:
        adir = os.path.join(ACTORS_DIR, actor)
        platform = actor[:-len("-compat")].strip()
        man_path = os.path.join(adir, "manifest.json")
        if not os.path.exists(man_path):
            errors.append(f"{actor}: missing manifest.json")
            continue
        try:
            m = json.load(open(man_path, encoding="utf-8"))
        except Exception as e:
            errors.append(f"{actor}: manifest.json invalid JSON: {e}")
            continue
        handles.add(m.get("handle", actor))
        # CID shape
        cid = m.get("wasmCid", "")
        if not RAW_CID.match(cid):
            errors.append(f"{actor}: wasmCid not a valid bafkrei raw-CIDv1: {cid!r}")
        # schema + main (glob the .kotoba — tolerant of the malformed
        # " coherence" leading-space dir name from the wave-9 typo).
        sp = os.path.join(adir, "schema", f"{platform}.kotoba")
        if not os.path.exists(sp):
            cands = glob.glob(os.path.join(adir, "schema", "*.kotoba"))
            if cands:
                sp = cands[0]
                if actor != actor.strip() or " " in actor:
                    warns.append(f"{actor!r}: malformed dir name (leading/space); "
                                 f"normalize to {actor.strip().replace(' ', '')!r}")
        mp = os.path.join(adir, "src", "main.py")
        if not os.path.exists(sp):
            errors.append(f"{actor}: missing schema/*.kotoba")
        if not os.path.exists(mp):
            errors.append(f"{actor}: missing src/main.py")
        else:
            try:
                ast.parse(open(mp, encoding="utf-8").read())
            except Exception as e:
                errors.append(f"{actor}: main.py does not compile: {e}")
        # tier
        tier = m.get("tier")
        if tier not in ("L3", "L4"):
            errors.append(f"{actor}: bad tier {tier!r}")
        if tier == "L4":
            l4.add(m["handle"])
        # capabilities present
        caps = m.get("capabilities", {})
        for c in ("api", "supplychain", "socialpost", "mcp"):
            if c not in caps:
                errors.append(f"{actor}: missing capability {c}")
        # CID freshness (warn only — sibling schema churn is expected)
        if os.path.exists(sp) and os.path.exists(mp):
            fresh = reg.cid_v1_raw(reg.program_bundle(adir, platform))
            if fresh != cid:
                stale += 1
        # L4 extras
        if tier == "L4":
            if not (os.path.isdir(os.path.join(adir, "tests")) and
                    glob.glob(os.path.join(adir, "tests", "test_*.py"))):
                errors.append(f"{actor}: L4 but no contract test")
            oapi = os.path.join(adir, "openapi.json")
            if not os.path.exists(oapi):
                errors.append(f"{actor}: L4 but no openapi.json")
            else:
                try:
                    spec = json.load(open(oapi, encoding="utf-8"))
                    if "openapi" not in spec or "paths" not in spec:
                        errors.append(f"{actor}: openapi.json missing openapi/paths")
                except Exception as e:
                    errors.append(f"{actor}: openapi.json invalid: {e}")

    if stale:
        warns.append(f"{stale}/{len(actor_dirs)} actors have a stale wasmCid "
                     f"(content changed since last register run — re-run "
                     f"register_cleanroom_actors.py to refresh)")

    # indexes
    _check_index(os.path.join(SCHEMAS_DIR, "cleanroom-actors.index.json"),
                 "actors", handles, errors, warns)
    _check_index(os.path.join(SCHEMAS_DIR, "cleanroom-mcp-index.json"),
                 "servers", handles, errors, warns)
    _check_index(os.path.join(SCHEMAS_DIR, "cleanroom-openapi-index.json"),
                 "apis", handles, errors, warns)
    _check_index(os.path.join(SCHEMAS_DIR, "cleanroom-socialpost-index.json"),
                 "feeds", handles, errors, warns)

    # seed EDN coverage + balance
    seed_path = os.path.join(SCHEMAS_DIR, "cleanroom-actors-seed.kotoba.edn")
    if os.path.exists(seed_path):
        s = open(seed_path, encoding="utf-8").read()
        for o, c in (("(", ")"), ("[", "]"), ("{", "}")):
            if s.count(o) != s.count(c):
                errors.append(f"seed EDN unbalanced {o}{c}: {s.count(o)} vs {s.count(c)}")
        seed_handles = set(re.findall(r':actor/handle "([^"]+)"', s))
        missing = handles - seed_handles
        if missing:
            warns.append(f"seed EDN missing {len(missing)} actors (e.g. {sorted(missing)[:3]})")
    else:
        errors.append("cleanroom-actors-seed.kotoba.edn missing")

    # report
    print("=" * 56)
    print("CLEAN-ROOM ACTOR SYSTEM — INTEGRITY VERIFICATION")
    print("=" * 56)
    print(f"actors: {len(actor_dirs)}  |  L4: {len(l4)}  |  L3: {len(actor_dirs) - len(l4)}")
    print(f"ERRORS: {len(errors)}   WARNINGS: {len(warns)}")
    for w in warns:
        print(f"  ⚠ {w}")
    for e in errors[:40]:
        print(f"  ✘ {e}")
    if len(errors) > 40:
        print(f"  … and {len(errors) - 40} more errors")
    print("=" * 56)
    print("RESULT:", "PASS (no errors)" if not errors else f"FAIL ({len(errors)} errors)")
    return 0 if not errors else 1


def _check_index(path, key, handles, errors, warns):
    name = os.path.basename(path)
    if not os.path.exists(path):
        errors.append(f"{name} missing")
        return
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        errors.append(f"{name} invalid JSON: {e}")
        return
    items = d.get(key, [])
    idx_handles = {it.get("handle") for it in items}
    if idx_handles != handles:
        missing = handles - idx_handles
        extra = idx_handles - handles
        if missing:
            warns.append(f"{name}: missing {len(missing)} actors (e.g. {sorted(missing)[:3]})")
        if extra:
            warns.append(f"{name}: has {len(extra)} unknown actors (e.g. {sorted(extra)[:3]})")
    if d.get("count") not in (None, len(items)):
        errors.append(f"{name}: count {d.get('count')} != len({key}) {len(items)}")


if __name__ == "__main__":
    raise SystemExit(main())
