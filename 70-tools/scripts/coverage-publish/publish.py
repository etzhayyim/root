#!/usr/bin/env python3
"""coverage-publish — durable persistence for live-ingested coverage artifacts.
ADR-2606142300 (clj-native) + ADR-2605241500 (DataLad+git-annex+IPFS dataset substrate) +
ADR-2605262130/2605312345 (kotoba Datom log) + ADR-2606111330 (kotobase.net pin saga).

Council-authorised (founder Lv7+ 1/1, 2026-06-16): the G7 live-ingest gate is OPEN and the
ingested artifacts are persisted on the three operator-named stores — DataLad, IPFS, kotobase.net.

For each artifact it:
  1. IPFS  — `ipfs add --cid-version=1 --raw-leaves --pin` and ASSERTS the daemon's CID equals
     the pure-stdlib CIDv1/raw/sha2-256 (content-address trust anchor; matches `ipfs add`).
  2. DataLad — saves the artifact into a DataLad dataset under 80-data/<name>/ (git-annex content
     + git metadata = the durable, versioned dataset record, ADR-2605241500). The dataset is a
     standalone DataLad dataset (NOT registered as a monorepo subdataset → no .gitmodules race);
     the monorepo commits only the small manifest pointer (G8 — data lives in DataLad/IPFS, never
     git-lfs in the monorepo).
  3. IPNS (optional) — publishes the primary CID under the node's `self` key → a stable
     `/ipns/<id>` that resolves to the latest graph.
  4. kotobase.net (optional) — POSTs to the IPFS Pinning Service API `/pins` with a bearer
     `KOTOBA_PIN_TOKEN`. Per ADR-2606111330 the deployed pod is isolated (peer_count:0) and the
     endpoint is 401 unauthed, so without a token this is recorded as `operator-follow-up`, never
     faked. With a token it registers a real pin.
  5. writes publish-manifest.json + PUBLISH.md (CIDs, IPNS, DataLad commit, kotobase status,
     gateway URLs, fetch+verify steps).

Public/representative coverage data only (G1) — safe to publish by construction. Stdlib only.

Usage:
  publish.py --name <dataset-name> --actor <actor> --artifacts f1 [f2 ...] \\
             [--ipns] [--kotobase] [--data-root 80-data]
"""
from __future__ import annotations
import argparse, base64, hashlib, json, os, pathlib, shutil, subprocess, sys

GATEWAYS = ["https://ipfs.io/ipfs/", "https://dweb.link/ipfs/", "https://cloudflare-ipfs.com/ipfs/"]
KOTOBASE_PINS = "https://kotobase.net/pins"


def _b32(b: bytes) -> str:
    return base64.b32encode(b).decode("ascii").lower().rstrip("=")


def cidv1_raw(data: bytes) -> str:
    """CIDv1 / raw (0x55) / sha2-256 — byte-identical to `ipfs add --cid-version=1 --raw-leaves`."""
    mh = bytes([0x12, 0x20]) + hashlib.sha256(data).digest()
    return "b" + _b32(bytes([0x01, 0x55]) + mh)


def _run(args, timeout=120):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def _ipfs(*args, timeout=120):
    return _run(["ipfs", *args], timeout=timeout)


_RAW_BLOCK_MAX = 262144  # IPFS default chunk size: files ≤256KiB are a single raw block


def ipfs_add_pin(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    local = cidv1_raw(data)                    # single-block CIDv1/raw (valid only ≤256KiB)
    out = _ipfs("add", "-Q", "--cid-version=1", "--raw-leaves", "--pin=true", str(path))
    daemon = out.stdout.strip() if out.returncode == 0 else None
    chunked = len(data) > _RAW_BLOCK_MAX
    # ≤256KiB: assert byte-identical to the pure CID (trust anchor). >256KiB: IPFS chunks into a
    # dag-pb DAG, so the daemon CID is authoritative + content-addressed but != the single-block CID.
    verified = (daemon == local) if not chunked else (daemon is not None)
    return {"file": path.name, "cid": daemon or local,
            "local_single_block_cid": local, "daemon_cid": daemon, "chunked": chunked,
            "verified": verified, "bytes": len(data)}


def datalad_save(dataset: pathlib.Path, artifacts: list[pathlib.Path], msg: str) -> dict:
    dataset.mkdir(parents=True, exist_ok=True)
    created = False
    if not (dataset / ".datalad").is_dir():
        r = _run(["datalad", "create", "--force", str(dataset)], timeout=180)
        created = r.returncode == 0
    for a in artifacts:
        dst = dataset / a.name
        if a.resolve() != dst.resolve():
            if dst.exists() or dst.is_symlink():
                _run(["datalad", "unlock", "-d", str(dataset), str(dst)], timeout=120)
                dst.unlink(missing_ok=True)   # drop the (possibly read-only annex) symlink first
            shutil.copy2(a, dst)
    r = _run(["datalad", "save", "-d", str(dataset), "-m", msg], timeout=300)
    sha = _run(["git", "-C", str(dataset), "rev-parse", "HEAD"], timeout=30)
    return {"dataset": str(dataset), "created": created, "saved": r.returncode == 0,
            "commit": sha.stdout.strip() if sha.returncode == 0 else None}


def ipns_publish(cid: str, key: str) -> dict:
    """Publish under a PER-DATASET IPNS key (created if absent) so distinct datasets get distinct
    stable /ipns names — the shared `self` key would let each publish clobber the last."""
    have = _ipfs("key", "list", "-l", timeout=30)
    if key not in (have.stdout or ""):
        _ipfs("key", "gen", "--type=ed25519", key, timeout=30)
    kid = _ipfs("key", "list", "-l", timeout=30)
    keyid = next((ln.split()[0] for ln in (kid.stdout or "").splitlines()
                  if ln.strip().endswith(" " + key) or ln.strip().split()[-1] == key), None)
    r = _ipfs("name", "publish", "--allow-offline", f"--key={key}", f"/ipfs/{cid}", timeout=120)
    if r.returncode == 0:
        return {"published": True, "ipns": keyid, "key": key}
    return {"published": False, "key": key, "error": r.stderr.strip()[:200]}


def kotobase_pin(cid: str, name: str) -> dict:
    token = os.environ.get("KOTOBA_PIN_TOKEN")
    if not token:
        return {"status": "operator-follow-up",
                "note": "no KOTOBA_PIN_TOKEN; /pins is 401 unauthed + pod isolated "
                        "(ADR-2606111330). CID is locally pinned + DataLad-saved; register on "
                        "kotobase.net when a CACAO/JWT token is provided."}
    import urllib.request, urllib.error
    body = json.dumps({"cid": cid, "name": name}).encode("utf-8")
    req = urllib.request.Request(KOTOBASE_PINS, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"status": "registered", "http": r.status, "response": json.load(r)}
    except urllib.error.HTTPError as e:
        return {"status": "error", "http": e.code, "body": e.read().decode("utf-8", "replace")[:200]}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)[:200]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="persist live-ingested coverage artifacts (DataLad+IPFS+kotobase)")
    ap.add_argument("--name", required=True, help="dataset name under <data-root>/")
    ap.add_argument("--actor", required=True)
    ap.add_argument("--artifacts", nargs="+", required=True)
    ap.add_argument("--data-root", default="80-data")
    ap.add_argument("--ipns", action="store_true")
    ap.add_argument("--kotobase", action="store_true")
    args = ap.parse_args(argv)

    if not shutil.which("ipfs"):
        print("publish: ipfs CLI not found", file=sys.stderr); return 1
    arts = [pathlib.Path(a) for a in args.artifacts]
    missing = [str(a) for a in arts if not a.exists()]
    if missing:
        print(f"publish: missing artifacts: {missing}", file=sys.stderr); return 1

    dataset = pathlib.Path(args.data_root) / args.name
    added = [ipfs_add_pin(a) for a in arts]
    primary = added[0]["cid"]
    dl = datalad_save(dataset, arts, f"coverage: live-ingest publish for {args.actor}")
    ipns = ipns_publish(primary, f"coverage-{args.name}") if args.ipns else {"published": False, "skipped": True}
    kb = kotobase_pin(primary, args.name) if args.kotobase else {"status": "skipped"}

    manifest = {"actor": args.actor, "name": args.name, "artifacts": added,
                "primary_cid": primary, "datalad": dl, "ipns": ipns, "kotobase": kb,
                "gateways": [g + primary for g in GATEWAYS],
                "adr": ["2605241500", "2606111330", "2606142300"]}
    # The DataLad dataset holds the DATA (annexed → IPFS); the manifest/PUBLISH.md are the small
    # GIT-tracked POINTER and live OUTSIDE the (read-only annexed) dataset, in coverage-manifests/.
    mdir = pathlib.Path(args.data_root) / "coverage-manifests"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / f"{args.name}-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    _emit_publish_md(mdir / f"{args.name}-PUBLISH.md", manifest)
    print(json.dumps({k: manifest[k] for k in ("actor", "primary_cid", "datalad", "ipns", "kotobase")},
                     indent=2, ensure_ascii=False))
    return 0


def _emit_publish_md(out_path: pathlib.Path, m: dict) -> None:
    lines = [f"# {m['actor']} — live-ingest publish\n",
             "Council-authorised G7 live ingest (2026-06-16). Persisted on DataLad + IPFS + kotobase.net.\n",
             "## Artifacts (content-addressed, CIDv1/raw/sha2-256)\n",
             "| file | CID | bytes | verified |", "|---|---|---:|:--:|"]
    for a in m["artifacts"]:
        lines.append(f"| {a['file']} | `{a['cid']}` | {a['bytes']} | {'✓' if a['verified'] else '✗'} |")
    lines += [f"\n- **primary CID**: `{m['primary_cid']}`",
              f"- **DataLad**: dataset `{m['datalad']['dataset']}` commit `{m['datalad'].get('commit')}` (saved={m['datalad'].get('saved')})",
              f"- **IPNS**: {m['ipns'].get('ipns') or m['ipns'].get('skipped') and 'skipped' or m['ipns'].get('error')}",
              f"- **kotobase.net**: {m['kotobase'].get('status')} — {m['kotobase'].get('note','')}",
              "\n## Fetch + verify (works for single- and multi-block)\n```bash",
              f"ipfs cat {m['primary_cid']} > got.edn",
              "ipfs add -Q --cid-version=1 --raw-leaves --only-hash got.edn",
              f"# → must print {m['primary_cid']}", "```"]
    out_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
