"""IANA root zone snapshot fetcher.

Per ADR-2605262400 W1. The IANA root zone is the authoritative list of
top-level domain delegations; it is updated several times a day and is
served as a plain DNS zone file at:

  https://www.internic.net/domain/root.zone

License: public domain (the root zone is published by IANA as part of
ICANN's public-interest stewardship). Tagged Tier A.

We stage the raw zone AS-IS and emit an NDJSON sidecar with one row per
TLD delegation (NS + DS records grouped). Glue records (A / AAAA) are
preserved in a separate `glue` block per TLD.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_URL = "https://www.internic.net/domain/root.zone"


@dataclass
class IanaRootFetchOpts:
    base_url: str = DEFAULT_URL
    timeout_sec: float = 120.0
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _parse_zone(raw: str) -> list[dict]:
    """Group a root zone into per-TLD records.

    Returns a list of {tld, ns:[], ds:[], glue:[]} dicts, one per
    delegated TLD. The root itself (".") is filtered out.
    """
    by_tld: dict[str, dict] = defaultdict(
        lambda: {"ns": [], "ds": [], "glue": []}
    )
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        parts = s.split()
        if len(parts) < 5 or parts[2].upper() != "IN":
            continue
        name = parts[0].rstrip(".").lower()
        rtype = parts[3].upper()
        data = parts[4:]

        if name == "" or name == ".":
            continue
        is_tld_level = "." not in name
        is_glue_level = name.count(".") == 1
        if rtype == "NS" and is_tld_level:
            by_tld[name]["ns"].append(" ".join(data))
        elif rtype == "DS" and is_tld_level:
            by_tld[name]["ds"].append(" ".join(data))
        elif rtype in ("A", "AAAA") and is_glue_level:
            host_tld = name.split(".", 1)[1]
            by_tld[host_tld]["glue"].append({
                "host": name,
                "type": rtype,
                "addr": data[0] if data else "",
            })

    out: list[dict] = []
    for tld in sorted(by_tld):
        rec = by_tld[tld]
        out.append({
            "tld": tld,
            "ns": rec["ns"],
            "ds": rec["ds"],
            "glue": rec["glue"],
        })
    return out


def fetch(staging_dir: Path, opts: IanaRootFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"iana-root-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / "root.zone"
    ndjson_path = out_dir / "root.zone.ndjson"

    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True
    )
    try:
        resp = client.get(opts.base_url)
        resp.raise_for_status()
        raw_path.write_bytes(resp.content)
    finally:
        if owned_client:
            client.close()

    rows_decoded = 0
    if opts.write_ndjson:
        rows = _parse_zone(raw_path.read_text(encoding="utf-8", errors="replace"))
        rows_decoded = len(rows)
        with ndjson_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                f.write("\n")

    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    revision = f"sha256:{raw_sha}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
    )
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="iana-root",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": opts.base_url,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "tldCount": rows_decoded,
            "license": "public-domain",
            "tier": "A",
        },
    )


__all__ = ["DEFAULT_URL", "IanaRootFetchOpts", "fetch"]
