"""publish-ipfs sidecar.

Walks the `directory` special remote tree on disk (the canonical layout
that git-annex itself writes to), runs `ipfs add` per annex object, then
builds a key→CID map JSON, pins the map, and returns the map CID.

git-annex `directory` remote on-disk layout (with chunking enabled):

    <remote-root>/<2-letter-fanout-1>/<2-letter-fanout-2>/<SHA256E-KEY>/<SHA256E-KEY>

When chunking is on (we configure 64 MiB), the file at the leaf path is
named with the key plus a chunk suffix. For SHA256E without chunking
the leaf file's name equals the directory's name. We treat every regular
non-empty file under `<remote-root>` (excluding the `.etzhayyim/`
audit-trail prefix) as a content blob to pin.

Idempotency:
- Re-runs are safe; `ipfs add` of identical content returns the same
  CID. We track previously-published commits in
  `<remote-root>/.etzhayyim/published.json` so subsequent runs only add
  newly-arrived objects.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from . import ipfs


PUBLISHED_DIRNAME = ".etzhayyim"


@dataclass
class PublishResult:
    map_cid: str
    map_size: int
    object_count: int
    entries: list[dict]
    audit_path: Path
    remote_pin_url: str | None = None
    remote_pinned: int = 0       # CIDs successfully pinned to the canonical remote
    remote_pin_failures: int = 0


def _remote_pin(kotobase_pin_url: str | None, cid: str) -> bool:
    """Best-effort recursive pin of `cid` to the canonical remote (kotobase.net).

    Per ADR-2606091500 the local `ipfs add` is the add/self-pin tier; the durable
    canonical pin lives on kotobase.net. Fire-and-forget: any failure (endpoint
    down, auth, network) is swallowed so it never aborts the local publish —
    the dataset is still locally pinned + CID-addressable.
    """
    if not kotobase_pin_url:
        return False
    try:
        return ipfs.pin_add(kotobase_pin_url, cid)
    except Exception:  # noqa: BLE001 — remote pin is best-effort (ADR-2606091500)
        return False


def _iter_object_files(remote_root: Path) -> list[Path]:
    """Yield every regular file under `remote_root` except audit-trail files."""
    out: list[Path] = []
    for path in remote_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(remote_root)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] == PUBLISHED_DIRNAME:
            continue
        # git-annex directory remote occasionally drops housekeeping files
        # named `.git-annex-keys` or `.gitignore`; skip dotfiles defensively.
        if path.name.startswith("."):
            continue
        out.append(path)
    out.sort()
    return out


def _load_published(audit_dir: Path) -> dict:
    state_file = audit_dir / "published.json"
    if not state_file.exists():
        return {"version": 1, "last_published_keys": []}
    return json.loads(state_file.read_text("utf-8"))


def _save_published(audit_dir: Path, state: dict) -> None:
    state_file = audit_dir / "published.json"
    audit_dir.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True), "utf-8")


def _key_from_path(remote_root: Path, path: Path) -> str:
    """Derive the SHA256E key from the directory remote path.

    The git-annex `directory` remote stores objects under
    `<remote-root>/<fanout-a>/<fanout-b>/<KEY>/<KEY>` (no chunking) or
    `.../<KEY>/<KEY>.<n>` (with chunking). The penultimate path
    component is always the key.
    """
    parts = path.relative_to(remote_root).parts
    if len(parts) < 2:
        return path.stem
    return parts[-2]


def publish(
    *,
    kubo_api: str,
    subdataset_name: str,
    remote_root: Path,
    git_commit: str | None = None,
    kotobase_pin_url: str | None = None,
) -> PublishResult:
    """Run the sidecar publish-ipfs flow for one subdataset's directory remote.

    `kotobase_pin_url` (ADR-2606091500): after the local `ipfs add`, every object
    CID + the map CID is also pinned to the canonical remote pin (kotobase.net),
    best-effort. None disables the fanout (local-only publish).
    """
    if not remote_root.exists():
        raise FileNotFoundError(f"directory remote not found: {remote_root}")

    audit_dir = remote_root / PUBLISHED_DIRNAME
    state = _load_published(audit_dir)
    seen_keys = set(state.get("last_published_keys", []))

    object_files = _iter_object_files(remote_root)

    entries: list[dict] = []
    new_keys: list[str] = []
    remote_pinned = 0
    remote_failures = 0
    for path in object_files:
        key = _key_from_path(remote_root, path)
        cid = ipfs.add_file(kubo_api, path)
        pinned = _remote_pin(kotobase_pin_url, cid)
        if kotobase_pin_url:
            remote_pinned += int(pinned)
            remote_failures += int(not pinned)
        entries.append({"key": key, "ipfsCid": cid, "leafName": path.name,
                        "remotePinned": pinned})
        if key not in seen_keys:
            new_keys.append(key)

    map_doc = {
        "version": 1,
        "subdataset": subdataset_name,
        "gitCommit": git_commit,
        "annexBackend": "SHA256E",
        "publishedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": entries,
    }
    map_bytes = json.dumps(map_doc, indent=2, sort_keys=True).encode("utf-8")
    # IPFS treats `/` in filename as a path component → ipfs.add wraps in
    # a directory, breaking `ipfs cat <cid>`. Flatten the subdataset name.
    safe_name = subdataset_name.replace("/", "-").replace(" ", "_")
    map_cid = ipfs.add_bytes(kubo_api, map_bytes, filename=f"{safe_name}-map.json")
    map_remote_pinned = _remote_pin(kotobase_pin_url, map_cid)
    if kotobase_pin_url:
        remote_pinned += int(map_remote_pinned)
        remote_failures += int(not map_remote_pinned)

    audit_file = audit_dir / "published" / f"{git_commit or 'no-commit'}.json"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.write_text(
        json.dumps({**map_doc, "mapCid": map_cid}, indent=2, sort_keys=True),
        "utf-8",
    )

    state["version"] = 1
    state["last_published_keys"] = sorted({*seen_keys, *new_keys, *[e["key"] for e in entries]})
    state["last_map_cid"] = map_cid
    state["last_published_at"] = map_doc["publishedAt"]
    state["last_remote_pin_url"] = kotobase_pin_url
    _save_published(audit_dir, state)

    return PublishResult(
        map_cid=map_cid,
        map_size=len(map_bytes),
        object_count=len(entries),
        entries=entries,
        audit_path=audit_file,
        remote_pin_url=kotobase_pin_url,
        remote_pinned=remote_pinned,
        remote_pin_failures=remote_failures,
    )
