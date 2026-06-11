#!/usr/bin/env python3
"""Normalize real-estate JSONL records and submit them to the BPMN dispatcher.

Input rows are JSON objects with a `kind` field:
  source | property | listing | transaction

The worker deliberately stays thin: crawling/source-specific extraction should
land source artifacts first, then feed normalized rows here for graph writes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import Any


NSIDS = {
    "source": "com.etzhayyim.apps.realEstate.registerSource",
    "property": "com.etzhayyim.apps.realEstate.registerProperty",
    "listing": "com.etzhayyim.apps.realEstate.publishListing",
    "transaction": "com.etzhayyim.apps.realEstate.recordTransaction",
}


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body else {"ok": True}


def normalize(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    kind = str(row.pop("kind", "")).strip()
    if kind not in NSIDS:
        raise ValueError(f"unsupported kind: {kind!r}")
    return NSIDS[kind], {k: v for k, v in row.items() if v is not None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", help="normalized JSONL file, or '-' for stdin")
    parser.add_argument("--dispatcher-url", default=os.environ.get("DISPATCHER_URL", "https://dispatcher.etzhayyim.com"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    stream = sys.stdin if args.jsonl == "-" else open(args.jsonl, "r", encoding="utf-8")
    ok = 0
    failed = 0
    with stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                nsid, payload = normalize(json.loads(line))
                url = f"{args.dispatcher_url.rstrip('/')}/xrpc/{nsid}"
                result = {"dryRun": True, "nsid": nsid, "payload": payload} if args.dry_run else post_json(url, payload)
                print(json.dumps({"line": line_no, "nsid": nsid, "result": result}, ensure_ascii=False))
                ok += 1
            except Exception as exc:
                print(json.dumps({"line": line_no, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
                failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
