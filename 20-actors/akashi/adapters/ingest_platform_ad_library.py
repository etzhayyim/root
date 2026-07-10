"""Ingest reviewed local platform ad-library exports.

This is the operator-facing file boundary for Meta/Instagram/X-style public
ad-library records. It does not fetch the network, log in, scrape, or bypass
platform controls. Operators provide already-reviewed JSON exports/snapshots;
the adapter validates them against akashi lexicons and can emit records,
DataScript/kotoba tx EDN, or Datomic schema+scalar tx EDN.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from edn_export import records_to_datomic_edn, records_to_edn
from lexicon_shape_validator import validate_record, validate_records
from platform_ad_library_fixture_parser import parse_platform_ad_library_fixture

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
LEX = REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "akashi"

ATTESTING_DID = "did:web:akashi.etzhayyim.com"
DEFAULT_SOURCE_POLICY_CID = "cid:akashi:source-policy:reviewed-platform-export"
DEFAULT_METHOD_NOTE_CID = "cid:akashi:method-note:platform-export-ingest"


def ingest_files(
    paths: list[Path],
    *,
    attesting_did: str = ATTESTING_DID,
    source_policy_cid: str = DEFAULT_SOURCE_POLICY_CID,
    method_note_cid: str = DEFAULT_METHOD_NOTE_CID,
) -> dict[str, Any]:
    if not paths:
        raise ValueError("at least one reviewed platform export path is required")
    outputs = [
        parse_platform_ad_library_fixture(
            _load(path),
            attesting_did=attesting_did,
            source_policy_cid=source_policy_cid,
            method_note_cid=method_note_cid,
        )
        for path in paths
    ]
    merged = _merge_outputs(*outputs)
    _validate_output(merged)
    return merged


def summarize(records: dict[str, Any], paths: list[Path]) -> dict[str, Any]:
    counts = {
        name: len(value) if isinstance(value, list) else 1
        for name, value in sorted(records.items())
    }
    platforms = sorted(
        {
            r.get("platform")
            for r in records.get("adDisclosureSnapshot", [])
            if isinstance(r, dict) and r.get("platform")
        }
    )
    return {
        "actor": "akashi",
        "mode": "reviewed-platform-export-ingest",
        "networkAccess": False,
        "writes": False,
        "inputFiles": [str(path) for path in paths],
        "platforms": platforms,
        "recordCounts": counts,
        "totalRecords": sum(counts.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="akashi-ingest-platform-ad-library")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--source-policy-cid", default=DEFAULT_SOURCE_POLICY_CID)
    parser.add_argument("--method-note-cid", default=DEFAULT_METHOD_NOTE_CID)
    parser.add_argument("--attesting-did", default=ATTESTING_DID)
    parser.add_argument("--emit-records", action="store_true")
    parser.add_argument("--emit-edn", action="store_true")
    parser.add_argument("--emit-datomic", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    records = ingest_files(
        args.paths,
        attesting_did=args.attesting_did,
        source_policy_cid=args.source_policy_cid,
        method_note_cid=args.method_note_cid,
    )
    if args.emit_datomic:
        payload = records_to_datomic_edn(records)
    elif args.emit_edn:
        payload = records_to_edn(records)
    else:
        value = records if args.emit_records else summarize(records, args.paths)
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _merge_outputs(*outputs: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for output in outputs:
        for name, value in output.items():
            if isinstance(value, list):
                merged.setdefault(name, []).extend(value)
            else:
                merged.setdefault(name, value)
    return merged


def _validate_output(output: dict[str, Any]) -> None:
    for name, value in output.items():
        lexicon = _load(LEX / f"{name}.json")
        if isinstance(value, list):
            validate_records(value, lexicon)
        else:
            validate_record(value, lexicon)


if __name__ == "__main__":
    raise SystemExit(main())
