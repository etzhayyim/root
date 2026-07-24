#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Validate every `60-apps/<app>/kotodama.jsonld` against
`90-docs/_registry/schemas/kotodama.schema.json`.

5th axis of registry enforcement (per ADR-2605271200 closure cycle 52
deferred follow-on; landed in cycle 53). Parallel pattern to:
  - cycles 27-30: deps.toml book-keeping (axis 1)
  - cycle 48: docs.json freshness (axis 2)
  - graph.edn freshness (axis 3; docs-graph-edn-freshness)
  - cycle 50-51: registry schema validation (axis 4)
  - **cycle 53: kotodama manifest validation (axis 5; this script)**

Requires `jsonschema` Python package. If not installed locally:
  - lefthook hook: warns + skips validation (operator non-blocking)
  - GitHub Actions: installs via pip + runs strict

Usage:
    70-tools/scripts/docs/validate-kotodama-manifests.py
    70-tools/scripts/docs/validate-kotodama-manifests.py --strict
        # exit 2 if jsonschema unavailable
    70-tools/scripts/docs/validate-kotodama-manifests.py --json
        # JSON output with errors per manifest
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
APPS_GLOB = REPO / "60-apps" / "*" / "kotodama.jsonld"
SCHEMA = REPO / "90-docs" / "_registry" / "schemas" / "kotodama.schema.json"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 2 if jsonschema package is unavailable (default: warn + exit 0)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output",
    )
    args = ap.parse_args()

    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:
        msg = (
            "validate-kotodama-manifests: jsonschema package not installed.\n"
            "  Install: python3 -m pip install --break-system-packages jsonschema"
        )
        if args.strict:
            print(msg, file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps({"ok": True, "skipped": True}, indent=2))
            return 0
        print(msg, file=sys.stderr)
        print("(non-strict mode; continuing without validation)", file=sys.stderr)
        return 0

    if not SCHEMA.exists():
        print(f"missing schema: {SCHEMA.relative_to(REPO)}", file=sys.stderr)
        return 2

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    manifests = sorted(glob.glob(str(APPS_GLOB)))
    if not manifests:
        msg = "validate-kotodama-manifests: no manifests found under 60-apps/*/kotodama.jsonld"
        if args.json:
            print(
                json.dumps(
                    {"ok": True, "total": 0, "clean": 0, "broken": 0, "errors": {}},
                    indent=2,
                )
            )
            return 0
        print(msg)
        return 0

    per_app_errors: dict[str, list[dict[str, Any]]] = {}
    total = 0
    clean = 0
    for f in manifests:
        total += 1
        p = Path(f)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            per_app_errors[p.parent.name] = [
                {"path": [], "message": f"JSON parse error: {e}", "validator": "json-parse"}
            ]
            continue
        errs = list(validator.iter_errors(data))
        if not errs:
            clean += 1
        else:
            per_app_errors[p.parent.name] = [
                {
                    "path": list(e.absolute_path),
                    "message": e.message,
                    "validator": e.validator,
                }
                for e in errs[:20]
            ]

    if args.json:
        print(
            json.dumps(
                {
                    "ok": len(per_app_errors) == 0,
                    "total": total,
                    "clean": clean,
                    "broken": total - clean,
                    "errors": per_app_errors,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(
            f"kotodama manifests: {clean}/{total} valid"
            + (f" ({len(per_app_errors)} broken)" if per_app_errors else "")
        )
        if per_app_errors:
            print()
            for app, errs in per_app_errors.items():
                print(f"  {app}:")
                for e in errs[:5]:
                    pth = "/".join(str(p) for p in e["path"]) or "(root)"
                    print(f"    [{pth}] {e['message'][:200]}")
                if len(errs) > 5:
                    print(f"    ... and {len(errs) - 5} more")

    return 0 if not per_app_errors else 1


if __name__ == "__main__":
    sys.exit(main())
