#!/usr/bin/env python3
"""Verify okaimono UNSPSC integration contracts.

This is a repository-local, DB-free gate for the okaimono side of the
openUnispsc integration. It checks that catalog/order API contracts, component
manifest, and docs all expose the same UNSPSC import/search/purchase surface.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SHOPPING_ROOT = REPO / "60-apps/etzhayyim-project-shopping"


REQUIRED_PROTO_PATTERNS = [
    "string unispsc_code = 13;",
    "string unispsc_segment = 14;",
    "string unispsc_family = 15;",
    "string unispsc_class = 16;",
    "string commodity_did = 17;",
    "rpc ImportUnispscSegment(ImportUnispscSegmentRequest) returns (ImportUnispscSegmentPlan);",
    "message ImportUnispscSegmentRequest",
    "message ImportUnispscSegmentPlan",
    "bool validate_unispsc_classification = 4;",
]

REQUIRED_DOC_PATTERNS = [
    "catalog-search-unispsc",
    "import-unispsc-segment",
    "procurement-find-offers-unispsc",
    "com.etzhayyim.apps.openUnispsc.syncCatalogItem",
    "com.etzhayyim.apps.openUnispsc.planCatalogPurchase",
]

REQUIRED_MANIFEST_CAPABILITIES = {
    "e-commerce",
    "product-catalog",
    "unispsc-classification",
    "unispsc-catalog-import",
}

REQUIRED_MANIFEST_COLLECTIONS = {
    "com.etzhayyim.apps.okaimono.catalogItem",
    "com.etzhayyim.apps.okaimono.order",
    "com.etzhayyim.apps.unispsc.commodity",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _missing_patterns(path: Path, patterns: list[str]) -> list[str]:
    text = _read(path)
    return [pattern for pattern in patterns if pattern not in text]


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    }


def verify() -> dict[str, Any]:
    proto_okaimono = ROOT / "proto/v1/shopping.proto"
    proto_shopping = SHOPPING_ROOT / "proto/v1/shopping.proto"
    manifest_path = ROOT / "appview/okaimono-shopping-mcp-component/kotodama.jsonld"
    readme_path = ROOT / "appview/okaimono-shopping-mcp-component/README.md"
    claude_path = ROOT / "CLAUDE.md"
    spec_path = ROOT / "okaimono-etzhayyim-ai-ec-operating-spec.md"

    missing: list[str] = []
    checks: dict[str, bool] = {}

    for label, path in {
        "proto:okaimono": proto_okaimono,
        "proto:shopping": proto_shopping,
        "manifest": manifest_path,
        "readme": readme_path,
        "claude": claude_path,
        "spec": spec_path,
    }.items():
        exists = path.exists()
        checks[f"{label}:exists"] = exists
        if not exists:
            missing.append(label)

    proto_missing = {
        "okaimono": _missing_patterns(proto_okaimono, REQUIRED_PROTO_PATTERNS) if proto_okaimono.exists() else REQUIRED_PROTO_PATTERNS,
        "shopping": _missing_patterns(proto_shopping, REQUIRED_PROTO_PATTERNS) if proto_shopping.exists() else REQUIRED_PROTO_PATTERNS,
    }
    for label, gaps in proto_missing.items():
        checks[f"proto:{label}:patterns"] = not gaps
        missing.extend(f"proto:{label}:{gap}" for gap in gaps)

    docs = {
        "readme": readme_path,
        "claude": claude_path,
        "spec": spec_path,
    }
    doc_missing: dict[str, list[str]] = {}
    for label, path in docs.items():
        patterns = REQUIRED_DOC_PATTERNS if label != "spec" else REQUIRED_DOC_PATTERNS[:3]
        gaps = _missing_patterns(path, patterns) if path.exists() else patterns
        doc_missing[label] = gaps
        checks[f"doc:{label}:patterns"] = not gaps
        missing.extend(f"doc:{label}:{gap}" for gap in gaps)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    capabilities = set(manifest.get("profile", {}).get("capabilities", []))
    collections = set(manifest.get("triggers", {}).get("subscribeRepos", {}).get("collections", []))
    missing_capabilities = sorted(REQUIRED_MANIFEST_CAPABILITIES - capabilities)
    missing_collections = sorted(REQUIRED_MANIFEST_COLLECTIONS - collections)
    checks["manifest:capabilities"] = not missing_capabilities
    checks["manifest:collections"] = not missing_collections
    missing.extend(f"manifest:capability:{capability}" for capability in missing_capabilities)
    missing.extend(f"manifest:collection:{collection}" for collection in missing_collections)

    tool_checks: dict[str, dict[str, Any]] = {}
    protoc = shutil.which("protoc")
    if protoc:
        tool_checks["protoc:okaimono"] = _run([
            protoc,
            "--proto_path=proto/v1",
            "--descriptor_set_out=/tmp/okaimono-unispsc-contract.pb",
            "proto/v1/shopping.proto",
        ], ROOT)
        tool_checks["protoc:shopping"] = _run([
            protoc,
            "--proto_path=proto/v1",
            "--descriptor_set_out=/tmp/shopping-unispsc-contract.pb",
            "proto/v1/shopping.proto",
        ], SHOPPING_ROOT)
    else:
        tool_checks["protoc"] = {"ok": None, "skipped": True, "reason": "protoc not found"}

    for label, result in tool_checks.items():
        if result.get("ok") is False:
            missing.append(f"tool:{label}")
            checks[f"tool:{label}"] = False
        elif result.get("ok") is True:
            checks[f"tool:{label}"] = True

    return {
        "ok": not missing,
        "checks": checks,
        "missing": sorted(set(missing)),
        "proto": {"missing": proto_missing},
        "docs": {"missing": doc_missing},
        "manifest": {
            "missingCapabilities": missing_capabilities,
            "missingCollections": missing_collections,
        },
        "toolChecks": tool_checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--report-path", help="Optional path to write the JSON verifier report.")
    args = parser.parse_args()

    result = verify()
    payload = json.dumps(result, indent=2 if args.pretty else None, sort_keys=True)
    if args.report_path:
        path = Path(args.report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
