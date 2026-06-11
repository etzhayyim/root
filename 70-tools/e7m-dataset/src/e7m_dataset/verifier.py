"""`e7m-dataset verify` — fetch the map CID, fetch each entry CID,
verify sha256 against the local annex-store object."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import ipfs


@dataclass
class EntryReport:
    key: str
    ipfs_cid: str
    expected_sha256: str | None
    actual_sha256: str
    local_annex_size: int | None
    ipfs_size: int
    ok: bool
    note: str = ""


@dataclass
class VerifyReport:
    subdataset: str
    map_cid: str
    map_object_count: int
    checked: int
    ok_count: int
    fail_count: int
    entries: list[EntryReport] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.fail_count == 0 and self.checked == self.map_object_count


# SHA256E annex key embeds the sha256 of the content:
#   SHA256E-s<size>--<hex>.<ext>
_SHA256E_RE = re.compile(r"^SHA256E-s(?P<size>\d+)--(?P<sha>[0-9a-f]+)(?:\.[^/]+)?$")


def _sha256_from_key(key: str) -> str | None:
    m = _SHA256E_RE.match(key)
    return m.group("sha") if m else None


def _annex_object_path(remote_root: Path, key: str) -> Path | None:
    """Locate the actual on-disk file for a SHA256E (or MD5E etc.) key
    under the directory remote tree. The tree uses 2-level fanout."""
    for candidate in remote_root.rglob(key):
        if candidate.is_file() and candidate.parent.name == key:
            return candidate
    return None


def verify(
    *,
    kubo_api: str,
    subdataset: str,
    map_cid: str,
    remote_root: Path,
    max_entries: int | None = None,
) -> VerifyReport:
    """Fetch `map_cid`, walk its `entries[]`, fetch each via `ipfs cat`,
    sha256-check against the SHA256E key (and cross-check against the
    local annex object's size when present)."""
    map_bytes = ipfs.cat(kubo_api, map_cid)
    doc = json.loads(map_bytes.decode("utf-8"))
    entries = doc.get("entries", [])

    if max_entries is not None:
        check_set = entries[:max_entries]
    else:
        check_set = entries

    report = VerifyReport(
        subdataset=subdataset,
        map_cid=map_cid,
        map_object_count=len(entries),
        checked=len(check_set),
        ok_count=0,
        fail_count=0,
    )

    for e in check_set:
        key = e["key"]
        cid = e["ipfsCid"]
        expected = _sha256_from_key(key)
        blob = ipfs.cat(kubo_api, cid)
        actual = hashlib.sha256(blob).hexdigest()

        local_path = _annex_object_path(remote_root, key)
        local_size = local_path.stat().st_size if local_path else None

        note = ""
        ok = True
        if expected is not None and actual != expected:
            ok = False
            note = f"sha256 mismatch: ipfs={actual[:16]}… key={expected[:16]}…"
        elif local_size is not None and local_size != len(blob):
            ok = False
            note = f"size mismatch: ipfs={len(blob)} annex={local_size}"
        elif expected is None:
            note = "non-SHA256E key — falling back to size/annex cross-check only"

        report.entries.append(EntryReport(
            key=key,
            ipfs_cid=cid,
            expected_sha256=expected,
            actual_sha256=actual,
            local_annex_size=local_size,
            ipfs_size=len(blob),
            ok=ok,
            note=note,
        ))
        if ok:
            report.ok_count += 1
        else:
            report.fail_count += 1

    return report


__all__ = ["EntryReport", "VerifyReport", "verify"]
