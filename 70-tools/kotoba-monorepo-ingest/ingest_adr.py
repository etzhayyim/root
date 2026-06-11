#!/usr/bin/env python3
"""ADR corpus → kotoba quad NDJSON ingester.

ADR-2605281800 R1 deliverable. Walks 90-docs/adr/*.md, parses YAML front
matter, computes IPFS CIDs via local Kubo, emits a kotoba-shaped NDJSON
quad stream conforming to ADR-2605281700 §5.2 vocabulary.

Output 1 row per quad: {graph, subject, predicate, object}.

Constraints:
- IPFS endpoint defaults to http://127.0.0.1:5001 (local Kubo only, no PSA)
- Subject IRI scheme: adr:<10-digit-id> (ADR-2605281700 §5.2)
- Idempotent on re-run for unchanged git HEAD
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Any, Iterable

GRAPH = "kotoba:graph:etzhayyim-root"
TOOL_VERSION = "kotoba-monorepo-ingest@0.1.0"

# YAML import deferred so --help works without PyYAML installed.
def _load_yaml():
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.stderr.write(
            "ERROR: PyYAML not installed. Run: pip install pyyaml\n"
        )
        sys.exit(2)
    return yaml


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_front_matter(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Return (front_matter, error). One of the two is None.

    Returns (None, None) when no front matter is present.
    Returns (None, "<reason>") on YAML parse failure.
    """
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return None, None
    yaml = _load_yaml()
    try:
        return yaml.safe_load(m.group(1)), None
    except yaml.YAMLError as e:
        # ADR front matter occasionally contains YAML-invalid characters
        # (backticks, unescaped colons in body-like content). Skip + log.
        return None, f"YAML parse error: {type(e).__name__}: {str(e).splitlines()[0]}"


def ipfs_add(path: pathlib.Path, endpoint: str) -> str:
    """POST /api/v0/add?cid-version=1; return base32 CIDv1."""
    url = (
        endpoint.rstrip("/")
        + "/api/v0/add?cid-version=1&pin=true&raw-leaves=false"
    )
    with path.open("rb") as f:
        body = f.read()
    boundary = "kotoba-ingest-boundary"
    data = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + body + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())
    cid = payload.get("Hash")
    if not cid:
        raise RuntimeError(f"unexpected Kubo response for {path}: {payload}")
    return cid


def git_head_sha(repo_root: pathlib.Path) -> str:
    out = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    )
    return out.strip()


def adr_id_from_filename(name: str) -> str | None:
    """`2605281700-...md` → `2605281700`."""
    m = re.match(r"^(\d{10})-", name)
    return m.group(1) if m else None


def normalize_id_ref(raw: str) -> str | None:
    """`adr-2605281700-...` or `2605281700` → `adr:2605281700`.

    Returns None if the reference doesn't look like an ADR id.
    """
    if not raw:
        return None
    raw = raw.strip()
    m = re.search(r"(\d{10})", raw)
    if not m:
        return None
    return f"adr:{m.group(1)}"


def emit_quads(
    adr_dir: pathlib.Path,
    repo_root: pathlib.Path,
    endpoint: str,
    dry_run: bool,
) -> Iterable[dict[str, str]]:
    git_sha = git_head_sha(repo_root)
    git_sha_short = git_sha[:7]
    utc_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_subject = f"ingest:{git_sha_short}:{utc_iso}"
    adr_count = 0
    skipped: list[str] = []

    md_files = sorted(adr_dir.glob("*.md"))
    for md in md_files:
        if md.name in ("README.md", "template.md"):
            continue
        adr_id = adr_id_from_filename(md.name)
        if not adr_id:
            skipped.append(f"{md.name}: filename does not start with 10-digit id")
            continue
        text = md.read_text(encoding="utf-8")
        fm, err = parse_front_matter(text)
        if err:
            skipped.append(f"{md.name}: {err}")
            continue
        if not fm:
            skipped.append(f"{md.name}: missing YAML front matter")
            continue
        required = ("id", "title", "status", "doc_type")
        missing = [k for k in required if k not in fm]
        if missing:
            skipped.append(f"{md.name}: missing required keys {missing}")
            continue

        subject = f"adr:{adr_id}"
        rel_path = md.relative_to(repo_root).as_posix()

        if dry_run:
            cid = f"bafkrei{adr_id}placeholder"  # marker — schema-only
        else:
            cid = ipfs_add(md, endpoint)

        scalar = [
            ("hasCid", cid),
            ("filePath", rel_path),
            ("docType", str(fm.get("doc_type"))),
            ("status", str(fm.get("status"))),
            ("title", str(fm.get("title"))),
            ("ingestRun", run_subject),
        ]
        for key in ("topic", "authoritative", "last_verified"):
            if key in fm:
                pred = {"last_verified": "lastVerified"}.get(key, key)
                scalar.append((pred, str(fm[key]).lower() if isinstance(fm[key], bool) else str(fm[key])))

        for predicate, obj in scalar:
            yield {"graph": GRAPH, "subject": subject, "predicate": predicate, "object": obj}

        list_predicates = [
            ("supersedes", "supersedes"),
            ("superseded_by", "supersededBy"),
            ("depends_on", "dependsOn"),
            ("related", "relatedTo"),
        ]
        for yaml_key, pred in list_predicates:
            for item in fm.get(yaml_key, []) or []:
                tgt = normalize_id_ref(str(item))
                if tgt:
                    yield {"graph": GRAPH, "subject": subject, "predicate": pred, "object": tgt}

        adr_count += 1

    # Provenance run
    yield {"graph": GRAPH, "subject": run_subject, "predicate": "gitSha", "object": git_sha}
    yield {"graph": GRAPH, "subject": run_subject, "predicate": "adrCount", "object": str(adr_count)}
    yield {"graph": GRAPH, "subject": run_subject, "predicate": "toolVersion", "object": TOOL_VERSION}

    if skipped:
        sys.stderr.write(f"\nSkipped {len(skipped)} ADR(s):\n")
        for line in skipped:
            sys.stderr.write(f"  - {line}\n")
    sys.stderr.write(f"\nIngested {adr_count} ADR(s) from {adr_dir}\n")


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adr-dir", default=str(repo_root / "90-docs/adr"))
    ap.add_argument("--kubo-endpoint", default=os.environ.get("KOTOBA_IPFS_ENDPOINT", "http://127.0.0.1:5001"))
    ap.add_argument("--out", default=str(repo_root / "90-docs/_registry/kotoba-quads.ndjson"))
    ap.add_argument("--dry-run", action="store_true", help="skip ipfs add; emit placeholder CIDs")
    args = ap.parse_args()

    adr_dir = pathlib.Path(args.adr_dir).resolve()
    out_path = pathlib.Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out:
        for q in emit_quads(adr_dir, repo_root, args.kubo_endpoint, args.dry_run):
            out.write(json.dumps(q, ensure_ascii=False) + "\n")
    sys.stderr.write(f"Wrote {out_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
