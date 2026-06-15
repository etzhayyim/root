#!/usr/bin/env python3
"""
Wave 11 cross-artifact consistency verifier.

For every Wave 11 / 11b clj+datomic actor, asserts that the independently
generated artifacts agree — drift between any pair is a bug:

  manifest.entities  ≡  cljc (def entities …)  ≡  cljc schema :db/ident idents
                     ≡  cljc handlers table     ≡  test ENTITIES
  manifest.endpointCount == 5 × |entities|      (CRUD per entity)
  openapi paths          == 2 × |entities|      (/v1/<p> and /v1/<p>/{id})
  cljc route entries     == 5 × |entities|
  manifest.wasmCid       == CID(schema + actor.cljc + deps.edn)   (bundle integrity)
  runtime == kotoba-clj, lang == clojure                          (no python residue)
  src/main.py absent                                              (python fully removed)

Exit non-zero on any inconsistency. `--test` also runs each bb contract suite.
"""

import os
import re
import sys
import json
import subprocess
import importlib.util

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
ACTORS_DIR = os.path.join(ROOT, "20-actors")

_spec = importlib.util.spec_from_file_location(
    "clj", os.path.join(TOOLS_DIR, "scaffold_wave11_clj_datomic.py"))
clj = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(clj)

HANDLES = list(clj.COHORT.keys())


def _entities_from_def(src):
    m = re.search(r"\(def entities #\{([^}]*)\}\)", src)
    return set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()


def _entities_from_schema(src, handle):
    return set(re.findall(rf":{re.escape(handle)}\.(\w+)/id\b", src))


def _handler_collections(src):
    m = re.search(r"\(def \^:private handlers\s*\{(.*?)\}\)\s*\n\n", src, re.S)
    body = m.group(1) if m else ""
    return set(re.findall(r'"(\w+)"\s+\{:create', body))


def _route_creates(src):
    return len(re.findall(r":op :create", src))


def _test_entities(tsrc):
    m = re.search(r"\(def ENTITIES \[([^\]]*)\]\)", tsrc)
    return set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()


def check(handle):
    adir = os.path.join(ACTORS_DIR, f"{handle}-compat")
    errs = []
    man = json.load(open(os.path.join(adir, "manifest.json")))
    api = json.load(open(os.path.join(adir, "openapi.json")))
    actor_path = os.path.join(adir, "src", handle, "actor.cljc")
    test_path = os.path.join(adir, "tests", handle, "actor_test.cljc")
    src = open(actor_path).read()
    tsrc = open(test_path).read()

    man_ents = set(man["entities"])
    n = len(man["entities"])
    sets = {
        "manifest": man_ents,
        "cljc-def": _entities_from_def(src),
        "cljc-schema": _entities_from_schema(src, handle),
        "test": _test_entities(tsrc),
    }
    for name, s in sets.items():
        if s != man_ents:
            errs.append(f"entity set mismatch ({name}={sorted(s)} vs manifest={sorted(man_ents)})")

    handler_colls = _handler_collections(src)
    if len(handler_colls) != n:
        errs.append(f"handlers={len(handler_colls)} != {n} entities")

    creates = _route_creates(src)
    if creates != n:
        errs.append(f"route :create entries={creates} != {n}")

    if man["capabilities"]["api"]["endpointCount"] != 5 * n:
        errs.append(f"manifest.endpointCount={man['capabilities']['api']['endpointCount']} != {5*n}")

    if len(api["paths"]) != 2 * n:
        errs.append(f"openapi paths={len(api['paths'])} != {2*n}")

    cid = clj.cid_v1_raw(clj.clj_program_bundle(adir, handle))
    if cid != man["wasmCid"]:
        errs.append(f"CID drift: bundle={cid} manifest={man['wasmCid']}")

    if man.get("runtime") != "kotoba-clj" or man.get("lang") != "clojure":
        errs.append(f"runtime/lang not clj ({man.get('runtime')}/{man.get('lang')})")

    if os.path.exists(os.path.join(adir, "src", "main.py")):
        errs.append("python src/main.py still present")

    if "(defn dispatch" not in src:
        errs.append("dispatch fn missing")

    return n, errs


def run_bb_test(handle):
    adir = os.path.join(ACTORS_DIR, f"{handle}-compat")
    expr = (f"(require '{handle}.actor-test) "
            f"(let [r (clojure.test/run-tests '{handle}.actor-test)] "
            f"(System/exit (+ (:fail r) (:error r))))")
    p = subprocess.run(["bb", "--classpath", "src:tests", "-e", expr],
                       cwd=adir, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip().splitlines()[-1:] or [""]


def write_index():
    """Emit a corpus-shaped index for the 26 clj actors (apex Worker merge candidate).
    Mirrors 00-contracts/schemas/cleanroom-actors.index.json entry shape."""
    actors = []
    for h in HANDLES:
        man = json.load(open(os.path.join(ACTORS_DIR, f"{h}-compat", "manifest.json")))
        actors.append({
            "handle": man["handle"], "did": man["did"], "wasmCid": man["wasmCid"],
            "kind": man["kind"], "wasmProvenance": man["wasmProvenance"], "tier": man["tier"],
            "title": man["title"], "category": "compute_photonics",
            "capabilities": list(man["capabilities"].keys()),
            "exec": man["exec"], "runtime": man["runtime"],
            "lang": man.get("lang"), "persistence": man.get("persistence"),
        })
    doc = {
        "schemaVersion": "1.0", "graph": "actors-v1",
        "adr": ["260607", "2606014500", "2605262130", "2605312345"],
        "wave": "11/11b/11c — compute & photonics (clj/Datomic)",
        "runtime": "kotoba-clj", "exec": "fleet|jvm-bb|browser-local-cljs",
        "count": len(actors), "tierCounts": {"L4": len(actors)}, "actors": actors,
    }
    out = os.path.join(ROOT, "00-contracts", "schemas", "cleanroom-actors-wave11.index.json")
    with open(out, "w") as f:
        json.dump(doc, f, indent=2)
    return out, len(actors)


def main():
    run_tests = "--test" in sys.argv
    do_index = "--index" in sys.argv
    total_errs = 0
    print(f"Wave 11 consistency verifier — {len(HANDLES)} actors"
          + (" (+ bb contract tests)" if run_tests else "") + "\n")
    for h in HANDLES:
        n, errs = check(h)
        tag = "OK" if not errs else "FAIL"
        extra = ""
        if run_tests and not errs:
            ok, last = run_bb_test(h)
            if not ok:
                errs.append(f"bb test failed: {last[-1] if last else ''}")
                tag = "FAIL"
            else:
                extra = " · tests green"
        total_errs += len(errs)
        print(f"  [{tag:4}] {h:<20} {n} entities, {5*n} endpoints{extra}")
        for e in errs:
            print(f"          ✗ {e}")
    print()
    if total_errs:
        print(f"FAILED: {total_errs} inconsistencies")
        sys.exit(1)
    print(f"ALL CONSISTENT: {len(HANDLES)} actors, {sum(len(clj.COHORT[h][2]) for h in HANDLES)} entities")
    if do_index:
        out, n = write_index()
        print(f"INDEX WRITTEN: {n} actors → {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
