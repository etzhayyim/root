"""Materialize akashi fixture EDN artifacts for storage layers.

This does not perform a DataLad save, git commit, or kotoba-rad push. It writes
the deterministic EDN tx-data plus a storage manifest so the existing outer
tools can save the same artifact into git, DataLad/git-annex, or kotoba-rad.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from dry_run_fixtures import load_dry_run_records
from edn_export import records_to_datomic_edn, records_to_edn

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "akashi-platform-ad-library.fixture.tx.kotoba.edn"
DEFAULT_DATOMIC = ROOT / "data" / "akashi-platform-ad-library.fixture.datomic.edn"
DEFAULT_MANIFEST = ROOT / "data" / "akashi-platform-ad-library.storage-manifest.edn"


def materialize(
    out: Path = DEFAULT_OUT,
    manifest: Path = DEFAULT_MANIFEST,
    datomic: Path = DEFAULT_DATOMIC,
) -> dict[str, object]:
    records = load_dry_run_records()
    edn = records_to_edn(records)
    artifact_bytes = edn.encode()
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    cidv1 = _cidv1_raw_sha2_256(artifact_bytes)
    datomic_edn = records_to_datomic_edn(records)
    datomic_bytes = datomic_edn.encode()
    datomic_digest = hashlib.sha256(datomic_bytes).hexdigest()
    datomic_cidv1 = _cidv1_raw_sha2_256(datomic_bytes)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(edn)
    datomic.parent.mkdir(parents=True, exist_ok=True)
    datomic.write_text(datomic_edn)
    artifact_path = _display_path(out)
    datomic_path = _display_path(datomic)

    payload = {
        "akashi.storage/artifact": artifact_path,
        "akashi.storage/cidv1": cidv1,
        "akashi.storage/sha256": digest,
        "akashi.storage/format": "datomic-datascript-tx-edn",
        "akashi.storage/datomic": {
            "path": datomic_path,
            "cidv1": datomic_cidv1,
            "sha256": datomic_digest,
            "format": "datomic-schema-and-scalar-tx-edn",
        },
        "akashi.storage/records": sum(
            len(v) if isinstance(v, list) else 1 for v in records.values()
        ),
        "akashi.storage/git": {"path": artifact_path, "status": "materialized"},
        "akashi.storage/datalad": {
            "path": artifact_path,
            "next": "bb kotoba:annex save 20-actors/akashi/data",
        },
        "akashi.storage/kotoba-rad": {
            "path": artifact_path,
            "cidv1": cidv1,
            "akashi.storage/identity-journal": "80-data/kotoba-rad/akashi.identity.journal.edn",
            "next": "bb rad:add-holding akashi --apply",
        },
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(_edn(payload) + "\n")
    return payload


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _cidv1_raw_sha2_256(data: bytes) -> str:
    framed = bytes([0x01, 0x55, 0x12, 0x20]) + hashlib.sha256(data).digest()
    return "b" + base64.b32encode(framed).decode("ascii").lower().rstrip("=")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="akashi-persist-fixture-edn")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--datomic", type=Path, default=DEFAULT_DATOMIC)
    args = parser.parse_args(argv)
    payload = materialize(args.out, args.manifest, args.datomic)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


def _edn(value):
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + " ".join(_edn(v) for v in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            parts.append(":" + key)
            parts.append(_edn(value[key]))
        return "{" + " ".join(parts) + "}"
    raise TypeError(type(value))


if __name__ == "__main__":
    raise SystemExit(main())
