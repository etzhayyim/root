#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Validate 90-docs/_registry/docs.json against docs.schema.json AND
90-docs/_registry/graph.jsonld against graph.schema.json.

Fourth axis of registry enforcement (parallel to cycles 27-30 deps.toml
book-keeping, cycle 48 docs.json freshness, cycle 49 graph.jsonld
freshness): cycle 50 = registry schema validation.

The freshness workflows guarantee the artifacts regenerate idempotently
from canonical source. This validator additionally guarantees the
artifacts CONFORM to a published JSON Schema — catching structural
drift in the generators themselves or in the source .md front-matter.

Source chain (all 4 layers):
  .md → docs.json → graph.jsonld
              ↓             ↓
       docs.schema.json   graph.schema.json
       (this validator)

Requires `jsonschema` Python package. If not installed locally:
  - lefthook hook: warns + skips validation (operator non-blocking)
  - GitHub Actions:  installs via pip + runs strict

Usage:
    70-tools/scripts/docs/validate-registry-schemas.py
    70-tools/scripts/docs/validate-registry-schemas.py --strict
        # exit 2 if jsonschema unavailable (default: exit 0 with warning)
    70-tools/scripts/docs/validate-registry-schemas.py --json
        # JSON output with errors instead of human text
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO / "90-docs" / "_registry" / "schemas"
DOCS_JSON = REPO / "90-docs" / "_registry" / "docs.json"
DOCS_SCHEMA = SCHEMAS_DIR / "docs.schema.json"
GRAPH_JSONLD = REPO / "90-docs" / "_registry" / "graph.jsonld"
GRAPH_SCHEMA = SCHEMAS_DIR / "graph.schema.json"


def _load(p: Path) -> Any:
    if not p.exists():
        print(
            f"validate-registry-schemas: missing {p.relative_to(REPO)}",
            file=sys.stderr,
        )
        sys.exit(2)
    return json.loads(p.read_text(encoding="utf-8"))


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
        help="emit machine-readable JSON output (validation errors as a list)",
    )
    args = ap.parse_args()

    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:
        msg = (
            "validate-registry-schemas: jsonschema package not installed.\n"
            "  Install: python3 -m pip install --user jsonschema\n"
            "  Or:      python3 -m pip install --break-system-packages jsonschema\n"
            "  Or in a venv / uv environment."
        )
        if args.strict:
            print(msg, file=sys.stderr)
            return 2
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "skipped": True,
                        "reason": "jsonschema-not-installed",
                    },
                    indent=2,
                )
            )
            return 0
        print(msg, file=sys.stderr)
        print("(non-strict mode; continuing without validation)", file=sys.stderr)
        return 0

    docs_data = _load(DOCS_JSON)
    docs_schema = _load(DOCS_SCHEMA)
    graph_data = _load(GRAPH_JSONLD)
    graph_schema = _load(GRAPH_SCHEMA)

    docs_validator = jsonschema.Draft202012Validator(docs_schema)
    graph_validator = jsonschema.Draft202012Validator(graph_schema)

    docs_errors = list(docs_validator.iter_errors(docs_data))
    graph_errors = list(graph_validator.iter_errors(graph_data))

    if args.json:
        payload: dict[str, Any] = {
            "ok": len(docs_errors) == 0 and len(graph_errors) == 0,
            "docs": {
                "schema": str(DOCS_SCHEMA.relative_to(REPO)),
                "data": str(DOCS_JSON.relative_to(REPO)),
                "error_count": len(docs_errors),
                "errors": [
                    {
                        "path": list(e.absolute_path),
                        "message": e.message,
                        "validator": e.validator,
                    }
                    for e in docs_errors[:50]
                ],
            },
            "graph": {
                "schema": str(GRAPH_SCHEMA.relative_to(REPO)),
                "data": str(GRAPH_JSONLD.relative_to(REPO)),
                "error_count": len(graph_errors),
                "errors": [
                    {
                        "path": list(e.absolute_path),
                        "message": e.message,
                        "validator": e.validator,
                    }
                    for e in graph_errors[:50]
                ],
            },
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if docs_errors:
            print(
                f"docs.json: {len(docs_errors)} schema validation error(s)",
                file=sys.stderr,
            )
            for e in docs_errors[:10]:
                pth = "/".join(str(p) for p in e.absolute_path) or "(root)"
                print(f"  [{pth}] {e.message[:200]}", file=sys.stderr)
            if len(docs_errors) > 10:
                print(f"  ... and {len(docs_errors) - 10} more", file=sys.stderr)
        else:
            print(f"docs.json: schema-valid ({len(docs_data.get('entries', []))} entries)")

        if graph_errors:
            print(
                f"graph.jsonld: {len(graph_errors)} schema validation error(s)",
                file=sys.stderr,
            )
            for e in graph_errors[:10]:
                pth = "/".join(str(p) for p in e.absolute_path) or "(root)"
                print(f"  [{pth}] {e.message[:200]}", file=sys.stderr)
            if len(graph_errors) > 10:
                print(f"  ... and {len(graph_errors) - 10} more", file=sys.stderr)
        else:
            print(f"graph.jsonld: schema-valid ({len(graph_data.get('@graph', []))} nodes)")

    return 0 if (not docs_errors and not graph_errors) else 1


if __name__ == "__main__":
    sys.exit(main())
