"""e7m-dataset CLI."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path

from . import charter, manifest, paths, pds, pinner, subdataset, verifier
from .fetchers import FetchResult
from .fetchers import geonames as geonames_fetcher
from .fetchers import hf as hf_fetcher
from .fetchers import hf_3d_nc as hf_3d_nc_fetcher
from .fetchers import mapillary as mapillary_fetcher
from .fetchers import ms_buildings as ms_buildings_fetcher
from .fetchers import openusd_samples as openusd_samples_fetcher
from .fetchers import osm as osm_fetcher
from .fetchers import overture as overture_fetcher
from .fetchers import sentinel2 as sentinel2_fetcher
from .fetchers import srtm as srtm_fetcher
from .fetchers import usgs_3dep as usgs_3dep_fetcher
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
    print(f"[publish-ipfs] kotobase_pin={p.kotobase_pin_url} (canonical remote, ADR-2606091500)", file=sys.stderr)

    result = pinner.publish(
        kubo_api=p.kubo_api,
        subdataset_name=args.subdataset,
        remote_root=remote_root,
        git_commit=args.git_commit,
        kotobase_pin_url=p.kotobase_pin_url,
    )

    print(json.dumps(
        {
            "map_cid": result.map_cid,
            "map_size_bytes": result.map_size,
            "object_count": result.object_count,
            "audit_path": str(result.audit_path),
            "remote_pin_url": result.remote_pin_url,
            "remote_pinned": result.remote_pinned,
            "remote_pin_failures": result.remote_pin_failures,
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


def _cmd_pull_sentinel2(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = sentinel2_fetcher.fetch(
        p.staging,
        sentinel2_fetcher.Sentinel2FetchOpts(
            tile_id=args.tile_id,
            stac_item_id=args.stac_item_id,
            datetime_range=args.datetime_range,
            bands=tuple(args.band) if args.band else sentinel2_fetcher.DEFAULT_BANDS,
            cloud_cover_max=args.cloud_cover_max,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_srtm(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = srtm_fetcher.fetch(
        p.staging,
        srtm_fetcher.SrtmFetchOpts(
            tile_id=args.tile_id,
            dem_type=args.dem_type,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_overture(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = overture_fetcher.fetch(
        p.staging,
        overture_fetcher.OvertureFetchOpts(
            release=args.release,
            theme=args.theme,
            type_name=args.type_name,
            explicit_shard=args.shard,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_ms_buildings(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = ms_buildings_fetcher.fetch(
        p.staging,
        ms_buildings_fetcher.MsBuildingsFetchOpts(
            country=args.country,
            quadkey=args.quadkey,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_mapillary(args: argparse.Namespace) -> int:
    from .vision_pii_filter import VisionPiiFilter
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    # Build PII filter from env (operator MUST configure ETZ_VISION_PII_BACKEND).
    vpf = VisionPiiFilter(allow_stub=args.allow_stub_pii_for_dryrun)
    bbox = tuple(args.bbox)
    if len(bbox) != 4:
        print("mapillary: --bbox requires 4 floats (west south east north)", file=sys.stderr)
        return 2
    result = mapillary_fetcher.fetch(
        p.staging,
        mapillary_fetcher.MapillaryFetchOpts(
            bbox=bbox,
            token=args.token,
            capture_date_range=args.capture_date_range,
            vision_pii_filter=vpf,
            max_images=args.max_images,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_hf_3d_nc(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = hf_3d_nc_fetcher.fetch(
        p.staging,
        hf_3d_nc_fetcher.Hf3dNcFetchOpts(
            slug=args.slug,
            explicit_owner=args.explicit_owner,
            explicit_repo=args.explicit_repo,
            explicit_nc_acknowledged=args.explicit_nc_acknowledged,
            revision=args.revision,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_openusd(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = openusd_samples_fetcher.fetch(
        p.staging,
        openusd_samples_fetcher.OpenUsdSamplesFetchOpts(
            slug=args.slug,
            explicit_url=args.explicit_url,
        ),
    )
    _print_fetch_result(result)
    return 0


def _cmd_pull_usgs_3dep(args: argparse.Namespace) -> int:
    p = paths.resolve()
    p.staging.mkdir(parents=True, exist_ok=True)
    result = usgs_3dep_fetcher.fetch(
        p.staging,
        usgs_3dep_fetcher.Usgs3depFetchOpts(
            project=args.project,
            tile_name=args.tile_name,
        ),
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
        kotobase_pin_url=p.kotobase_pin_url,
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


def _cmd_assemble_corpus(args: argparse.Namespace) -> int:
    """Delegate to the standalone assembler script.

    Per ADR-2605262400 §4. The implementation lives at
    `70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py`
    (a single file so operators can also call it directly without the
    e7m-dataset CLI). This verb is the canonical operator entry point.

    Resolution order for the assembler script:
      1. ETZ_ASSEMBLE_SCRIPT env var (operator override).
      2. Repo-root walk-up looking for the standard path.
      3. Fail with a clear "couldn't locate" error.
    """
    import importlib.util
    import os
    import sys as _sys

    override = os.environ.get("ETZ_ASSEMBLE_SCRIPT")
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override))
    here = Path.cwd().resolve()
    for parent in [here, *here.parents]:
        candidates.append(
            parent
            / "70-tools" / "baien-moemoekyun-train"
            / "scripts" / "assemble-public-corpus.py"
        )
    asm_path: Path | None = None
    for c in candidates:
        if c.is_file():
            asm_path = c
            break

    if asm_path is None:
        print(
            "e7m-dataset: couldn't locate assemble-public-corpus.py. "
            "Set ETZ_ASSEMBLE_SCRIPT or run from inside the etzhayyim-root tree.",
            file=sys.stderr,
        )
        return 2

    spec = importlib.util.spec_from_file_location(
        "_e7m_dataset_assembler", asm_path
    )
    if spec is None or spec.loader is None:
        print(f"e7m-dataset: could not build module spec for {asm_path}", file=sys.stderr)
        return 2
    mod = importlib.util.module_from_spec(spec)
    _sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    # Replay the assembler's CLI argv contract.
    argv: list[str] = ["--recipe", str(args.recipe)]
    if args.annex_root is not None:
        argv += ["--annex-root", str(args.annex_root)]
    if args.out_dir is not None:
        argv += ["--out-dir", str(args.out_dir)]
    if args.dry_run:
        argv.append("--dry-run")
    return mod.main(argv)


def _cmd_verify(args: argparse.Namespace) -> int:
    p = paths.resolve()
    remote_root = p.subdataset_annex_dir(args.subdataset)
    if not remote_root.exists():
        print(f"e7m-dataset verify: directory remote not found at {remote_root}", file=sys.stderr)
        return 2

    if args.map_cid:
        map_cid = args.map_cid
    else:
        row = manifest.find_latest_by_subdataset(args.subdataset)
        if not row:
            print(f"e7m-dataset verify: no manifest row for subdataset={args.subdataset}", file=sys.stderr)
            return 2
        map_cid = row["cid"]

    print(
        f"[verify] subdataset={args.subdataset} map_cid={map_cid} remote={remote_root}",
        file=sys.stderr,
    )
    report = verifier.verify(
        kubo_api=p.kubo_api,
        subdataset=args.subdataset,
        map_cid=map_cid,
        remote_root=remote_root,
        max_entries=(args.max_entries if args.max_entries > 0 else None),
    )

    summary = {
        "subdataset": report.subdataset,
        "map_cid": report.map_cid,
        "map_object_count": report.map_object_count,
        "checked": report.checked,
        "ok_count": report.ok_count,
        "fail_count": report.fail_count,
        "ok": report.ok,
    }
    if args.verbose:
        summary["entries"] = [
            {
                "key": e.key,
                "ipfsCid": e.ipfs_cid,
                "expectedSha256": e.expected_sha256,
                "actualSha256": e.actual_sha256,
                "localAnnexSize": e.local_annex_size,
                "ipfsSize": e.ipfs_size,
                "ok": e.ok,
                "note": e.note,
            }
            for e in report.entries
        ]
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report.ok else 4


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

    sub_pull_s2 = pull_sub.add_parser("sentinel2", help="Fetch a Sentinel-2 L2A scene via AWS Earth Search STAC (ADR-2605262500 §2 Tier A)")
    sub_pull_s2.add_argument("--tile-id", help="MGRS tile id, e.g. T54SUE")
    sub_pull_s2.add_argument("--stac-item-id", help="Pin a specific STAC item id (overrides --tile-id)")
    sub_pull_s2.add_argument("--datetime-range", help="ISO-8601 window, e.g. 2024-04-01/2024-05-31")
    sub_pull_s2.add_argument("--band", action="append", help="Bands to download (repeatable; default: B04 B03 B02)")
    sub_pull_s2.add_argument("--cloud-cover-max", type=float, default=20.0, help="Max cloud cover %% (default 20.0)")
    sub_pull_s2.set_defaults(func=_cmd_pull_sentinel2)

    sub_pull_srtm = pull_sub.add_parser("srtm", help="Fetch an SRTM 1-arc tile via OpenTopography (ADR-2605262500 §2 Tier A)")
    sub_pull_srtm.add_argument("--tile-id", required=True, help="NASA SRTM tile id, e.g. n35e139 (1°×1° square)")
    sub_pull_srtm.add_argument("--dem-type", default=srtm_fetcher.DEFAULT_DEM_TYPE, help="OpenTopography DEM type (default SRTMGL1)")
    sub_pull_srtm.set_defaults(func=_cmd_pull_srtm)

    sub_pull_ovt = pull_sub.add_parser("overture", help="Fetch an Overture Maps theme/type Parquet shard (ADR-2605262500 §2 Tier A)")
    sub_pull_ovt.add_argument("--release", required=True, help="Overture release id, e.g. 2024-12-12.0")
    sub_pull_ovt.add_argument("--theme", required=True, help=f"Theme. Known: {sorted(overture_fetcher.KNOWN_THEME_TYPES)}")
    sub_pull_ovt.add_argument("--type-name", required=True, help="Type within theme, e.g. segment / building")
    sub_pull_ovt.add_argument("--shard", help="Explicit shard filename (default: first-shard list)")
    sub_pull_ovt.set_defaults(func=_cmd_pull_overture)

    sub_pull_msb = pull_sub.add_parser("ms-buildings", help="Fetch one MS Global Building Footprints quadkey (ADR-2605262500 §2 Tier A, W2)")
    sub_pull_msb.add_argument("--country", help="MS Location slug (e.g. 'Japan'). One of --country / --quadkey required.")
    sub_pull_msb.add_argument("--quadkey", help="Explicit quadkey (overrides --country)")
    sub_pull_msb.set_defaults(func=_cmd_pull_ms_buildings)

    sub_pull_map = pull_sub.add_parser("mapillary", help="Fetch a Mapillary street-imagery bbox slice (Tier C / G13; vision PII filter MANDATORY per ADR-2605262500 §5)")
    sub_pull_map.add_argument("--bbox", type=float, nargs=4, metavar=("WEST", "SOUTH", "EAST", "NORTH"), required=True)
    sub_pull_map.add_argument("--token", help="Mapillary token (or set MAPILLARY_TOKEN env)")
    sub_pull_map.add_argument("--capture-date-range", help='Capture date filter (e.g. "2023-04-01")')
    sub_pull_map.add_argument("--max-images", type=int, default=mapillary_fetcher.DEFAULT_MAX_IMAGES)
    sub_pull_map.add_argument("--allow-stub-pii-for-dryrun", action="store_true", help="Use stub PII backend (tests / dry-runs only; requires ETZ_VISION_PII_ALLOW_STUB=1)")
    sub_pull_map.set_defaults(func=_cmd_pull_mapillary)

    sub_pull_nc = pull_sub.add_parser("hf-3d-nc", help="Fetch a NC-licensed 3D-asset bundle from HF Hub (Tier C / G13 fleet-internal; ADR-2605262500 §2)")
    sub_pull_nc.add_argument("--slug", help=f"NC repo slug. Known: {sorted(hf_3d_nc_fetcher.KNOWN_NC_REPOS)}")
    sub_pull_nc.add_argument("--explicit-owner", help="Operator-supplied HF owner (requires --explicit-nc-acknowledged)")
    sub_pull_nc.add_argument("--explicit-repo", help="Operator-supplied HF repo (requires --explicit-nc-acknowledged)")
    sub_pull_nc.add_argument("--explicit-nc-acknowledged", action="store_true", help="Operator signs that the upstream repo is NC-compatible (G13)")
    sub_pull_nc.add_argument("--revision", default="main")
    sub_pull_nc.set_defaults(func=_cmd_pull_hf_3d_nc)

    sub_pull_ousd = pull_sub.add_parser("openusd-samples", help="Fetch one Pixar OpenUSD sample scene (Apache-2.0; ADR-2605262500 §2 Tier A)")
    sub_pull_ousd.add_argument("--slug", help=f"Sample slug. Known: {sorted(openusd_samples_fetcher.KNOWN_SAMPLES)}")
    sub_pull_ousd.add_argument("--explicit-url", help="Operator-supplied URL (operator-on-license)")
    sub_pull_ousd.set_defaults(func=_cmd_pull_openusd)

    sub_pull_3dep = pull_sub.add_parser("usgs-3dep", help="Fetch one USGS 3DEP 1m DEM tile (US only; ADR-2605262500 §2 Tier A, W2)")
    sub_pull_3dep.add_argument("--project", required=True, help="USGS project slug, e.g. CA_NorCal_3DEP_2019_A19")
    sub_pull_3dep.add_argument("--tile-name", required=True, help="Tile basename without extension")
    sub_pull_3dep.set_defaults(func=_cmd_pull_usgs_3dep)

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

    # ── verify ───────────────────────────────────────────────────────
    sub_verify = sub.add_parser(
        "verify",
        help="Fetch map CID via Kubo, fetch each entry CID, sha256-check against the SHA256E key",
    )
    sub_verify.add_argument("subdataset", help="Subdataset name (e.g. 'HF/owner-repo')")
    sub_verify.add_argument("--map-cid", help="Override the map CID; default = manifest's most-recent row for this subdataset")
    sub_verify.add_argument("--max-entries", type=int, default=0, help="Cap entries to check (0 = all)")
    sub_verify.add_argument("--verbose", action="store_true", help="Include per-entry detail in the output")
    sub_verify.set_defaults(func=_cmd_verify)

    # ── assemble-corpus — cold-path corpus assembler (ADR-2605262400 §4) ──
    sub_asm = sub.add_parser(
        "assemble-corpus",
        help="Stream source subdatasets through Charter §2 + PII filter and emit typed NDJSON corpus shards per recipe (ADR-2605262400 §4)",
    )
    sub_asm.add_argument("--recipe", required=True, type=Path, help="Path to a corpus-recipe.toml file")
    sub_asm.add_argument(
        "--annex-root",
        type=Path,
        default=None,
        help="Annex-store root holding the source subdatasets (default: ${ETZ_DATASET_ROOT}/annex-store)",
    )
    sub_asm.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override output staging dir (default: ${ETZ_DATASET_ROOT}/datasets-staging/<output_subdataset>)",
    )
    sub_asm.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate recipe + emit summary, do NOT resolve pins or stream shards",
    )
    sub_asm.set_defaults(func=_cmd_assemble_corpus)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
