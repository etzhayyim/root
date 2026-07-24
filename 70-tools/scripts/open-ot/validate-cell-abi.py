#!/usr/bin/env python3
"""open-ot CI validator: cells × Lexicons consistency.

Walks `orgs/etzhayyim/com-etzhayyim-app-open-ot/cells/*/manifest.json` and
`00-contracts/lexicons/com/etzhayyim/apps/openOt/*.json` and verifies:

- All Lexicon files load as valid JSON.
- Lexicon `id` field matches the filename: `com.etzhayyim.apps.openOt.<basename>`.
- No `type: "number"` anywhere in Lexicon (root CLAUDE.md guardrail —
  AT Lexicon prohibits float at the wire boundary).
- No inline `items: { "type": "object" }` in Lexicon — array-of-object
  must use `items: { "type": "ref", "ref": "#typeName" }` (root CLAUDE.md
  guardrail; PDS validator silently hangs otherwise).
- All cell `manifest.json` load as valid JSON.
- Each manifest has `iec61499_fbtype`, `abi.init_export`, `abi.tick_export`,
  `tick_max_emitted`, `ecc.states`, `ecc.initial`.
- Each manifest's `ecc.initial` exists in `ecc.states`.
- Every `data_in_schema` / `data_out_schema` field's `wire` value is in
  the permitted vocabulary.

Usage (CI):
    python3 70-tools/scripts/open-ot/validate-cell-abi.py
    # exits 0 on PASS, non-zero on FAIL.

Usage (testing with custom roots):
    python3 .../validate-cell-abi.py --cells-dir <path> --lexicon-dir <path>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CELLS_DIR = (
    REPO_ROOT / "orgs/etzhayyim/com-etzhayyim-app-open-ot/cells"
)
DEFAULT_LEXICON_DIR = REPO_ROOT / "00-contracts/lexicons/com/etzhayyim/apps/openOt"

# Permitted `wire` vocabulary for cell manifest data_in / data_out schemas.
# Keep in sync with `cells/*/manifest.json` schema documentation.
ALLOWED_WIRE = {
    "valueMicroUnit",
    "valueMilliUnit",  # milli-scaled physical value (soc-kalman)
    "valueMilliPct",
    "qualityEnum",
    "tripReasonEnum",
    "boolean",
    "counter",
    # later-wave cell vocab that had drifted ahead of this validator
    # (black-start-seq / ltc-tap-fsm / mppt-perturb-observe):
    "stageEnum",
    "blackStartCommandEnum",
    "tapCommandEnum",
    "perturbDirEnum",
    "durationMs",
    "integerSigned",
}

REQUIRED_MANIFEST_KEYS = {"iec61499_fbtype", "abi", "ecc", "tick_max_emitted"}
REQUIRED_ABI_KEYS = {"init_export", "tick_export"}


def check_lexicon(path: Path) -> list[str]:
    """Return list of error strings (empty on PASS)."""
    errs: list[str] = []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"{path.name}: invalid JSON: {exc}"]

    expected_id = f"com.etzhayyim.apps.openOt.{path.stem}"
    if data.get("id") != expected_id:
        errs.append(f"{path.name}: id={data.get('id')!r} != {expected_id!r}")

    # Recursive walk for guardrail violations.
    def walk(obj: object, path_in_doc: str) -> None:
        if isinstance(obj, dict):
            t = obj.get("type")
            if t == "number":
                errs.append(
                    f"{path.name}: forbidden `type: \"number\"` at {path_in_doc} "
                    f"(use integer with µ-unit scaling)"
                )
            if path_in_doc.endswith(".items") and t == "object":
                errs.append(
                    f"{path.name}: array-of-inline-object at {path_in_doc} "
                    f"(use `items: {{type: ref, ref: \"#typeName\"}}` + defs)"
                )
            for k, v in obj.items():
                walk(v, f"{path_in_doc}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path_in_doc}[{i}]")

    walk(data, "")
    return errs


def check_manifest(path: Path) -> list[str]:
    cell_dir = path.parent.name
    errs: list[str] = []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"{cell_dir}/manifest.json: invalid JSON: {exc}"]

    missing = REQUIRED_MANIFEST_KEYS - set(data.keys())
    if missing:
        errs.append(f"{cell_dir}: manifest missing keys: {sorted(missing)}")

    abi = data.get("abi", {}) or {}
    missing_abi = REQUIRED_ABI_KEYS - set(abi.keys())
    if missing_abi:
        errs.append(f"{cell_dir}: manifest.abi missing keys: {sorted(missing_abi)}")

    tme = data.get("tick_max_emitted")
    if not isinstance(tme, int) or tme < 0:
        errs.append(f"{cell_dir}: tick_max_emitted={tme!r} must be non-negative int")

    ecc = data.get("ecc", {}) or {}
    states = ecc.get("states", [])
    initial = ecc.get("initial")
    if not isinstance(states, list) or not states:
        errs.append(f"{cell_dir}: ecc.states must be a non-empty list")
    elif initial not in states:
        errs.append(f"{cell_dir}: ecc.initial={initial!r} not in states {states}")

    for section in ("data_in_schema", "data_out_schema"):
        for field in data.get(section, []) or []:
            wire = field.get("wire")
            if wire is not None and wire not in ALLOWED_WIRE:
                errs.append(
                    f"{cell_dir}: {section}.{field.get('name')!r} "
                    f"unknown wire={wire!r} (allowed: {sorted(ALLOWED_WIRE)})"
                )

    return errs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells-dir", type=Path, default=DEFAULT_CELLS_DIR)
    parser.add_argument("--lexicon-dir", type=Path, default=DEFAULT_LEXICON_DIR)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    all_errs: list[str] = []
    lex_count = 0
    for lex in sorted(args.lexicon_dir.glob("*.json")):
        lex_count += 1
        all_errs.extend(check_lexicon(lex))

    manifest_count = 0
    for manifest in sorted(args.cells_dir.glob("*/manifest.json")):
        manifest_count += 1
        all_errs.extend(check_manifest(manifest))

    if all_errs:
        for e in all_errs:
            print(f"FAIL: {e}", file=sys.stderr)
        print(
            f"\n{len(all_errs)} validation error(s) "
            f"across {lex_count} lexicons + {manifest_count} manifests",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"OK: {lex_count} lexicons + {manifest_count} manifests valid"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
