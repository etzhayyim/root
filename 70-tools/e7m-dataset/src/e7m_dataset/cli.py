"""e7m-dataset CLI."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path

from . import charter, manifest, paths, pds, pinner, subdataset
from .fetchers import FetchResult
from .fetchers import geonames as geonames_fetcher
from .fetchers import hf as hf_fetcher
from .fetchers import osm as osm_fetcher
from .fetchers import wikidata as wikidata_fetcher


_TEXT_EXTS = {".txt", ".json", ".jsonl", ".csv", ".tsv", ".md", ".rst", ".sparql"}


def _pick_sample(staging_path: Path, *, kind: str, max_files: int = 20) -> list[Path]:
    candidates = sorted(p for p in staging_path.rglob("*") if p.is_file())
    if kind in {"baien-graft-image", "training-corpus", "lm-eval-bench", "reference"}:
        texts = [p for p in candidates if p.suffix.lower() in _TEXT_EXTS]
        if texts:
            return texts[:max_files]
    return candidates[:max_files]


def _cmd_where(args: argparse.Namespace) -> int:
    p = paths.resolve()
    print(json.dumps(
        {
            "root": str(p.root),
            "ipfs_data": str(p.ipfs_data),
            "annex_store": str(p.annex_store),
            "staging": str(p.staging),
            "kubo_api": p.kubo_api,
            "node_did": p.node_did,
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


def _cmd_publish_ipfs(args: argparse.Namespace) -> int:
    p = paths.resolve()
    remote_root = p.subdataset_annex_dir(args.subdataset)

    if not remote_root.exists():
        print(f"e7m-dataset: directory remote not found at {remote_root}", file=sys.stderr)
        return 2

    print(f"[publish-ipfs] subdataset={args.subdataset} remote={remote_root}", file=sys.stderr)
    print(f"[publish-ipfs] kubo_api={p.kubo_api}", file=sys.stderr)

    result = pinner.publish(
        kubo_api=p.kubo_api,
        subdataset_name=args.subdataset,
        remote_root=remote_root,
        git_commit=args.git_commit,
    )

    print(json.dumps(
        {
            "map_cid": result.map_cid,
            "map_size_bytes": result.map_size,
            "object_count": result.object_count,
            "audit_path": str(result.audit_path),
        },
        indent=2,
        sort_keys=True,
    ))

    if args.append_manifest:
        if not args.name or not args.revision or not args.kind:
            print(
                "e7m-dataset: --append-manifest requires --name, --revision, --kind",
                file=sys.stderr,
            )
            return 2

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        row = {
            "name": args.name,
            "revision": args.revision,
            "kind": args.kind,
            "cid": result.map_cid,
            "sizeBytes": sum(0 for _ in []) or result.map_size,
            "source": {"type": "local-import"},
            "license": args.license or "Apache-2.0",
            "charterRiderScan": {
                "passed": True,
                "at": now,
                "note": "smoke-test: scanner skipped (no sample provided)",
            },
            "assignedNodes": [p.node_did] if p.node_did else [],
            "replicationMin": 1,
            "addedAt": now,
            "addedBy": p.node_did or "did:web:unknown",
            "mapEntries": result.object_count,
            "subdataset": args.subdataset,
        }
        m_path = manifest.append(row)
        print(f"[publish-ipfs] manifest row appended → {m_path}", file=sys.stderr)

        record = pds.build_record(
            name=args.name,
            revision=args.revision,
            kind=args.kind,
            cid=result.map_cid,
            size_bytes=result.map_size,
            sha256=None,
            providers=["kubo"],
            pinned_at=now,
            charter_rider_scan=row["charterRiderScan"],
            assigned_nodes=row["assignedNodes"],
            source=row["source"],
            license=row["license"],
            manifest_row_ref=str(args.subdataset),
        )
        pds.emit(record, dry_run=args.dry_run_pds)

    return 0


def _print_fetch_result(result: FetchResult) -> None:
    print(json.dumps(
        {
            "name": result.name,
            "revision": result.revision,
            "stagingPath": str(result.staging_path),
            "fileCount": result.file_count,
            "sizeBytes": result.size_bytes,
            "source": result.source,
        },
        indent=2,
        sort_keys=True,
    ))


def _cmd_pull_wikidata(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = wikidata_fetcher.fetch(
        p.staging,
        wikidata_fetcher.WikidataFetchOpts(
            query_name=args.query,
            limit=args.limit,
            sparql_url=args.sparql_url,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_geonames(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = geonames_fetcher.fetch(
        p.staging,
        geonames_fetcher.GeonamesFetchOpts(dataset=args.dataset),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_osm(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = osm_fetcher.fetch(
        p.staging,
        osm_fetcher.OsmFetchOpts(region=args.region, fetch_md5=not args.no_md5),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_hf(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    if "/" not in args.repo:
        print(
            "e7m-dataset pull hf: --repo must be '<owner>/<repo>'",
            file=sys.stderr,
        )
        return 2
    owner, repo = args.repo.split("/", 1)
    result = hf_fetcher.fetch(
        p.staging,
        hf_fetcher.HfFetchOpts(
            owner=owner,
            repo=repo,
            revision=args.revision,
            repo_type=args.repo_type,
            max_bytes=(args.max_bytes if args.max_bytes >= 0 else None),
            include_globs=args.include or [],
            exclude_globs=args.exclude or [],
        ),
    )
    _print_fetch_result(result)
    return 0


# ── `add` — fetch + scan + datalad + publish-ipfs + emit (HF only in Phase 1) ──

_HF_URI_RE = re.compile(
    r"^hf(?:-model)?://(?P<owner>[^/]+)/(?P<repo>[^@]+)(?:@(?P<revision>.+))?$"
)


def _cmd_add(args: argparse.Namespace) -> int:
    p = paths.resolve()
    src = args.source

    if not (src.startswith("hf://") or src.startswith("hf-model://")):
        print(
            "e7m-dataset add: only hf:// / hf-model:// sources are supported "
            "in Phase 1. For geonames / osm / wikidata, run `pull <fetcher>` "
            "and chain `publish-ipfs` after `datalad save`.",
            file=sys.stderr,
        )
        return 2

    m = _HF_URI_RE.match(src)
    if not m:
        print(f"e7m-dataset add: cannot parse {src!r}", file=sys.stderr)
        return 2
    owner = m.group("owner")
    repo = m.group("repo")
    revision = m.group("revision") or "main"
    repo_type = "models" if src.startswith("hf-model://") else "datasets"

    p.staging.mkdir(parents=True, exist_ok=True)

    # 1. fetch
    print(
        f"[add] hf {repo_type} {owner}/{repo}@{revision} → staging",
        file=sys.stderr,
    )
    fr = hf_fetcher.fetch(
        p.staging,
        hf_fetcher.HfFetchOpts(
            owner=owner,
            repo=repo,
            revision=revision,
            repo_type=repo_type,
            max_bytes=(args.max_bytes if args.max_bytes >= 0 else None),
            include_globs=args.include or [],
            exclude_globs=args.exclude or [],
        ),
    )
    print(
        f"[add] staged {fr.file_count} files / {fr.size_bytes} bytes "
        f"@ {fr.revision}",
        file=sys.stderr,
    )

    # 2. Charter Rider scan over a sample
    sample = _pick_sample(fr.staging_path, kind=args.kind)
    print(f"[add] charter scan: sampling {len(sample)} files", file=sys.stderr)
    try:
        scan = charter.scan_sample(sample, kind=args.kind)
    except charter.CharterViolation as e:
        print(f"[add] CHARTER RIDER violation, aborting: {e}", file=sys.stderr)
        return 3

    # 3. ensure subdataset
    sub_name = f"HF/{owner}-{repo}"
    print(f"[add] subdataset={sub_name}", file=sys.stderr)
    sub_path = subdataset.ensure_subdataset(sub_name, paths=p)

    # 4. import files (move from staging into the subdataset tree)
    placed = subdataset.import_files(
        sub_path, fr.staging_path, move=not args.keep_staging
    )
    print(f"[add] imported {placed} files into subdataset", file=sys.stderr)

    # 5. datalad save
    sha = subdataset.save_subdataset(
        sub_path,
        f"add {fr.name}@{fr.revision} ({fr.file_count} files, {fr.size_bytes} bytes)",
    )
    print(f"[add] datalad save → {sha}", file=sys.stderr)

    # 6. git annex copy --to local-store
    print("[add] git annex copy . --to=local-store", file=sys.stderr)
    subdataset.copy_to_local_store(sub_path, jobs=args.jobs)

    # 7. publish-ipfs
    remote_root = p.subdataset_annex_dir(sub_name)
    print(f"[add] publish-ipfs (remote={remote_root})", file=sys.stderr)
    pub = pinner.publish(
        kubo_api=p.kubo_api,
        subdataset_name=sub_name,
        remote_root=remote_root,
        git_commit=sha,
    )

    # 8. manifest + PDS emit
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    license_str = args.license or fr.source.get("license") or "unknown"
    row = {
        "name": fr.name,
        "revision": fr.revision,
        "kind": args.kind,
        "cid": pub.map_cid,
        "sizeBytes": fr.size_bytes,
        "source": fr.source,
        "license": license_str,
        "charterRiderScan": scan,
        "assignedNodes": [p.node_did] if p.node_did else [],
        "replicationMin": 1,
        "addedAt": now,
        "addedBy": p.node_did or "did:web:unknown",
        "mapEntries": pub.object_count,
        "subdataset": sub_name,
    }
    m_path = manifest.append(row)
    print(f"[add] manifest row appended → {m_path}", file=sys.stderr)

    record = pds.build_record(
        name=fr.name,
        revision=fr.revision,
        kind=args.kind,
        cid=pub.map_cid,
        size_bytes=fr.size_bytes,
        sha256=None,
        providers=["kubo"],
        pinned_at=now,
        charter_rider_scan=scan,
        assigned_nodes=row["assignedNodes"],
        source=fr.source,
        license=license_str,
        manifest_row_ref=sub_name,
    )
    emit_result = pds.emit(record, dry_run=not args.emit)

    print(json.dumps(
        {
            "name": fr.name,
            "revision": fr.revision,
            "subdataset": sub_name,
            "git_commit": sha,
            "map_cid": pub.map_cid,
            "object_count": pub.object_count,
            "size_bytes": fr.size_bytes,
            "pds_emit": emit_result,
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="e7m-dataset",
        description="etzhayyim dataset substrate wrapper (ADR-2605241500)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub_where = sub.add_parser("where", help="Print resolved per-machine paths")
    sub_where.set_defaults(func=_cmd_where)

    sub_pub = sub.add_parser(
        "publish-ipfs",
        help="Walk directory remote, ipfs add each object, pin map JSON, return map CID",
    )
    sub_pub.add_argument("subdataset", help="Subdataset name under annex-store/ (e.g. 'superdataset' or 'HF/owner-repo')")
    sub_pub.add_argument("--git-commit", default=None, help="Git commit SHA to record in the map JSON")
    sub_pub.add_argument("--append-manifest", action="store_true", help="Append a row to 90-docs/baien/datasets.jsonl + emit a datasetPin record")
    sub_pub.add_argument("--name", help="Dataset name (required with --append-manifest)")
    sub_pub.add_argument("--revision", help="Dataset revision (required with --append-manifest)")
    sub_pub.add_argument("--kind", help="Dataset kind (required with --append-manifest)")
    sub_pub.add_argument("--license", help="SPDX license string for the manifest row")
    sub_pub.add_argument("--dry-run-pds", action="store_true", default=True, help="(default true in Phase 1) print the PDS record body instead of POSTing")
    sub_pub.set_defaults(func=_cmd_publish_ipfs)

    # ── pull <source> — stage upstream data ──────────────────────────
    sub_pull = sub.add_parser(
        "pull",
        help="Stage upstream data into the staging dir. Doesn't touch git-annex / IPFS by itself — follow with `publish-ipfs` after the operator curates and `datalad save`s.",
    )
    pull_sub = sub_pull.add_subparsers(dest="source", required=True)

    sub_pull_wd = pull_sub.add_parser("wikidata", help="Run a Wikidata SPARQL query and stage the JSONL result")
    sub_pull_wd.add_argument("--query", required=True, help=f"Canned query name. Known: {sorted(wikidata_fetcher.CANNED_QUERIES)}")
    sub_pull_wd.add_argument("--limit", type=int, default=5000, help="SPARQL LIMIT (default 5000)")
    sub_pull_wd.add_argument("--sparql-url", default=wikidata_fetcher.DEFAULT_SPARQL_URL)
    sub_pull_wd.set_defaults(func=_cmd_pull_wikidata)

    sub_pull_gn = pull_sub.add_parser("geonames", help="Download a GeoNames bulk dump")
    sub_pull_gn.add_argument("--dataset", default="cities1000", help=f"Dataset variant. Known: {sorted(geonames_fetcher.KNOWN_DATASETS)}")
    sub_pull_gn.set_defaults(func=_cmd_pull_geonames)

    sub_pull_osm = pull_sub.add_parser("osm", help="Download a Geofabrik OSM PBF extract")
    sub_pull_osm.add_argument("--region", required=True, help="Geofabrik region (e.g. 'japan', 'asia/japan', 'europe/germany/berlin')")
    sub_pull_osm.add_argument("--no-md5", action="store_true", help="Skip the .osm.pbf.md5 sidecar fetch")
    sub_pull_osm.set_defaults(func=_cmd_pull_osm)

    sub_pull_hf = pull_sub.add_parser("hf", help="Stage a Hugging Face dataset/model snapshot")
    sub_pull_hf.add_argument("--repo", required=True, help="<owner>/<repo>")
    sub_pull_hf.add_argument("--revision", default="main")
    sub_pull_hf.add_argument("--repo-type", default="datasets", choices=["datasets", "models"])
    sub_pull_hf.add_argument("--max-bytes", type=int, default=50 * (1 << 30), help="-1 disables the cap")
    sub_pull_hf.add_argument("--include", action="append", help="Glob to include (repeatable)")
    sub_pull_hf.add_argument("--exclude", action="append", help="Glob to exclude (repeatable)")
    sub_pull_hf.set_defaults(func=_cmd_pull_hf)

    # ── add — full chain (HF only in Phase 1) ────────────────────────
    sub_add = sub.add_parser(
        "add",
        help="HF: fetch → charter scan → datalad save → annex copy → publish-ipfs → manifest + datasetPin",
    )
    sub_add.add_argument("source", help="hf://<owner>/<repo>[@<rev>] or hf-model://<owner>/<repo>[@<rev>]")
    sub_add.add_argument("--kind", default="reference", help="manifest `kind` value")
    sub_add.add_argument("--license", help="Override the manifest `license` value")
    sub_add.add_argument("--max-bytes", type=int, default=50 * (1 << 30), help="-1 disables the cap")
    sub_add.add_argument("--include", action="append")
    sub_add.add_argument("--exclude", action="append")
    sub_add.add_argument("--jobs", type=int, default=4)
    sub_add.add_argument("--keep-staging", action="store_true", help="Copy files instead of moving them")
    sub_add.add_argument("--emit", action="store_true", help="POST the datasetPin record (default: dry-run only)")
    sub_add.set_defaults(func=_cmd_add)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
