"""warifu lexicon 整合 validator — wire lexicons + cell lexicons vs the code SoT.

Runnable standalone (no pytest required):
    python 20-actors/warifu/test_lexicons.py

Checks (ADR-2605302000):
  - every lexicon is valid JSON with `lexicon:1`, a top-level `id`, and `defs.main`
  - the lexicon `id` matches its filename stem
  - any `purpose` enum equals the canonical PHASE1 ∪ PHASE2 set from authorize.py
    (no purpose may be added to a lexicon without being in the code allow-list, and vice versa)
  - any `feeUsdc` schema is pinned `const: 0` (決済手数料ゼロ at the contract surface)
  - the dispute `reasonCode` / `status` enums match dispute.py REASON_CODES / DisputeStatus
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent          # 20-actors/warifu
REPO = ROOT.parents[1]                                   # repo root
WIRE = REPO / "10-protocol" / "warifu"
CELL_LEX = ROOT / "cells" / "lex"

# --- load the code SoT (cells package, relative imports) ---------------------------------
_spec = importlib.util.spec_from_file_location(
    "warifu_cells", ROOT / "cells" / "__init__.py",
    submodule_search_locations=[str(ROOT / "cells")],
)
wc = importlib.util.module_from_spec(_spec)
sys.modules["warifu_cells"] = wc
_spec.loader.exec_module(wc)

PHASE1 = set(wc.authorize.__globals__["PHASE1_PURPOSES"])
PHASE2 = set(wc.authorize.__globals__["PHASE2_GATED_PURPOSES"])
CANONICAL_PURPOSES = PHASE1 | PHASE2
REASON_CODES = set(wc.dispute.__globals__["REASON_CODES"])
DISPUTE_STATUSES = {s.value for s in wc.dispute.__globals__["DisputeStatus"]}

PASS = 0
def check(name, cond):
    global PASS
    assert cond, f"FAIL: {name}"
    PASS += 1
    print(f"  ok {name}")


def find_keys(obj, key):
    """Yield every value stored under `key` anywhere in a nested dict/list."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from find_keys(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_keys(v, key)


def find_property_schemas(obj, prop):
    """Yield schema dicts declared as `properties.<prop>` anywhere in the tree."""
    if isinstance(obj, dict):
        props = obj.get("properties")
        if isinstance(props, dict) and prop in props:
            yield props[prop]
        for v in obj.values():
            yield from find_property_schemas(v, prop)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_property_schemas(v, prop)


def run():
    files = sorted(WIRE.glob("*.json")) + sorted(CELL_LEX.glob("*.json"))
    check("found all 10 warifu lexicons", len(files) == 10)

    purpose_enum_seen = 0
    fee_schema_seen = 0
    dispute_checked = 0

    for f in files:
        doc = json.loads(f.read_text())
        stem = f.stem  # e.g. com.etzhayyim.card.authorize  /  warifu.authorize
        check(f"{stem}: lexicon==1", doc.get("lexicon") == 1)
        check(f"{stem}: id matches filename", doc.get("id") == stem)
        check(f"{stem}: has defs.main", isinstance(doc.get("defs", {}).get("main"), dict))

        # purpose enums must equal the canonical allow-list
        for sch in find_property_schemas(doc, "purpose"):
            if "enum" in sch:
                purpose_enum_seen += 1
                got = set(sch["enum"])
                check(f"{stem}: purpose enum == canonical allow-list", got == CANONICAL_PURPOSES)

        # every feeUsdc schema must be const 0
        for sch in find_property_schemas(doc, "feeUsdc"):
            fee_schema_seen += 1
            check(f"{stem}: feeUsdc const 0", sch.get("const") == 0)

        # dispute enums must match code
        if stem.endswith("dispute"):
            dispute_checked += 1
            for sch in find_property_schemas(doc, "reasonCode"):
                check(f"{stem}: reasonCode enum == dispute.py", set(sch.get("enum", [])) == REASON_CODES)
            for sch in find_property_schemas(doc, "status"):
                check(f"{stem}: status enum == DisputeStatus", set(sch.get("enum", [])) == DISPUTE_STATUSES)

    check("purpose enums were present in >=2 lexicons (wire+cell authorize)", purpose_enum_seen >= 2)
    check("feeUsdc const seen in >=2 lexicons", fee_schema_seen >= 2)
    check("both dispute lexicons validated", dispute_checked == 2)
    check("canonical set = phase1 ∪ phase2 (non-empty)", len(CANONICAL_PURPOSES) >= 6)

    print(f"warifu lexicons: {PASS} checks passed")


if __name__ == "__main__":
    run()
