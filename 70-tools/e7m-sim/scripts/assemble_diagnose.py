#!/usr/bin/env python3
"""assemble_diagnose.py — operator-side diagnostic CLI for assemble-usd-scene.py.

Third in the diagnostic CLI triad (alongside vision_pii_diagnose +
pds_diagnose). Mirrors the same shape: `check` for env/deps,
`inspect <scene.yaml>` for plan introspection, `dry-run <scene.yaml>`
for full assemble without writing output.

Usage:

  # 1. Validate env / deps / schema presence:
  python3 70-tools/e7m-sim/scripts/assemble_diagnose.py check
  # → reports yaml / jsonschema / pyarrow / Pillow / scipy availability
  # → reports schema file location + scenes/ dir count

  # 2. Inspect a scene.yaml's plan structure:
  python3 70-tools/e7m-sim/scripts/assemble_diagnose.py inspect <scene.yaml>
  # → prints scene name, ADR, bbox, sim_consumer, layer + prop summary,
  #   resolved CIDs, max_tier, charter scan status

  # 3. Dry-run assembly (no output written):
  python3 70-tools/e7m-sim/scripts/assemble_diagnose.py dry-run <scene.yaml>
  # → runs build_plan + build_usda; reports USDA SHA + layer/prop counts
  # → does NOT write scene.usda or manifest.json

Reduces operator-side debugging — before running full assemble against
a new scene.yaml (especially one that references real `local_*_path`
artifacts), use `inspect` to confirm layer composition and `dry-run`
to confirm USDA emission would succeed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_ASSEMBLE_SCRIPT = _SCRIPT_DIR / "assemble-usd-scene.py"


def _load_assemble_module():
    """Load assemble-usd-scene.py via importlib (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location("assemble_usd_scene", _ASSEMBLE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {_ASSEMBLE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["assemble_usd_scene"] = mod
    spec.loader.exec_module(mod)
    return mod


def _check_dep(name: str) -> tuple[bool, str]:
    try:
        mod = __import__(name)
    except ImportError as exc:
        return False, str(exc)
    return True, str(getattr(mod, "__version__", "unknown"))


def _cmd_check(args: argparse.Namespace) -> int:
    """Validate assemble env: yaml + optional jsonschema/pyarrow/Pillow/scipy."""
    report: dict = {
        "required": {},
        "recommended": {},
        "scene_schema": {},
        "scenes_dir": {},
    }
    critical_missing = False

    for dep in ("yaml",):
        ok, info = _check_dep(dep)
        report["required"][dep] = {"available": ok, "version": info if ok else None,
                                    "error": None if ok else info}
        if not ok:
            critical_missing = True

    for dep in ("jsonschema", "pyarrow", "PIL", "scipy", "numpy"):
        ok, info = _check_dep(dep)
        report["recommended"][dep] = {"available": ok, "version": info if ok else None,
                                       "error": None if ok else info}

    e7m_sim_root = _SCRIPT_DIR.parent
    schema_path = e7m_sim_root / "scenes" / "_schema" / "scene.schema.json"
    report["scene_schema"]["path"] = str(schema_path)
    report["scene_schema"]["exists"] = schema_path.exists()

    scenes_dir = e7m_sim_root / "scenes"
    if scenes_dir.exists():
        scenes = sorted([
            p.name for p in scenes_dir.iterdir()
            if p.is_dir() and (p / "scene.yaml").exists()
        ])
        report["scenes_dir"]["count"] = len(scenes)
        report["scenes_dir"]["scenes"] = scenes

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_check(report)

    return 2 if critical_missing else 0


def _print_check(report: dict) -> None:
    print("assemble-usd-scene setup check\n")
    print("Required deps:")
    for dep, info in report["required"].items():
        mark = "✓" if info["available"] else "✘"
        ver = info["version"] or info["error"]
        print(f"  {mark} {dep}: {ver}")
    print("Recommended deps:")
    for dep, info in report["recommended"].items():
        mark = "✓" if info["available"] else "?"
        ver = info["version"] or info["error"]
        print(f"  {mark} {dep}: {ver}")
    sc = report["scene_schema"]
    mark = "✓" if sc["exists"] else "✘"
    print(f"\nScene schema: {mark} {sc['path']}")
    sd = report["scenes_dir"]
    if "count" in sd:
        print(f"Scenes registered: {sd['count']}")
        for name in sd["scenes"]:
            print(f"  - {name}")


def _cmd_inspect(args: argparse.Namespace) -> int:
    """Print scene plan summary without emitting USDA."""
    mod = _load_assemble_module()
    scene_path = Path(args.scene_yaml)
    if not scene_path.exists():
        print(f"inspect: scene.yaml not found: {scene_path}", file=sys.stderr)
        return 2
    try:
        plan = mod.build_plan(scene_path)
    except Exception as exc:   # noqa: BLE001
        print(f"inspect: build_plan failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "scene_name": plan.scene_name,
            "adr": plan.adr,
            "sim_consumer": plan.sim_consumer,
            "crs": plan.crs,
            "bbox": plan.bbox,
            "output_subdataset": plan.output_subdataset,
            "max_tier": plan.max_tier,
            "must_carry_nc_infix": plan.must_carry_nc_infix,
            "layers": [
                {
                    "index": l.index, "kind": l.kind, "tier": l.tier,
                    "source_subdataset": l.source_subdataset,
                    "datasetPin_at": l.datasetPin_at,
                    "resolved_cid": l.resolved_cid,
                    "dispatch_handler": l.dispatch_handler,
                    "local_path": l.extra.get("local_geotiff_path")
                                  or l.extra.get("local_parquet_path"),
                }
                for l in plan.layers
            ],
            "props": [
                {
                    "index": p.index, "kind": p.kind, "tier": p.tier,
                    "source_subdataset": p.source_subdataset,
                    "resolved_cid": p.resolved_cid,
                    "count": p.extra.get("count"),
                }
                for p in plan.props
            ],
            "charter_scan_status": plan.charter_attestations.get("scan_status"),
            "charter_scan_scope": plan.charter_attestations.get("scope"),
        }
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(f"Scene: {plan.scene_name}")
        print(f"  ADR        : {plan.adr}")
        print(f"  Consumer   : {plan.sim_consumer}")
        print(f"  CRS        : {plan.crs}")
        print(f"  bbox       : {plan.bbox}")
        print(f"  Max tier   : {plan.max_tier}  (nc_required={plan.must_carry_nc_infix})")
        print(f"\nLayers ({len(plan.layers)}):")
        for l in plan.layers:
            local = (l.extra.get("local_geotiff_path")
                     or l.extra.get("local_parquet_path"))
            local_tag = f"  [local: {local}]" if local else ""
            print(f"  [{l.index}] {l.kind:18s} tier={l.tier}  "
                  f"→ {l.dispatch_handler}{local_tag}")
            print(f"      cid    : {l.resolved_cid}")
        print(f"\nProps ({len(plan.props)}):")
        for p in plan.props:
            print(f"  [{p.index}] {p.kind:25s} tier={p.tier}  "
                  f"count={p.extra.get('count', '-')}")
        print(f"\nCharter scan: "
              f"{plan.charter_attestations.get('scan_status')}  "
              f"(scope: {plan.charter_attestations.get('scope', '-')})")
    return 0


def _cmd_dry_run(args: argparse.Namespace) -> int:
    """Run build_plan + build_usda but DO NOT write any output."""
    mod = _load_assemble_module()
    scene_path = Path(args.scene_yaml)
    if not scene_path.exists():
        print(f"dry-run: scene.yaml not found: {scene_path}", file=sys.stderr)
        return 2
    try:
        plan = mod.build_plan(scene_path)
        usda = mod.build_usda(plan)
    except Exception as exc:   # noqa: BLE001
        print(f"dry-run: failed: {exc}", file=sys.stderr)
        return 1

    import hashlib
    sha = hashlib.sha256(usda.encode("utf-8")).hexdigest()
    payload = {
        "scene_name": plan.scene_name,
        "adr": plan.adr,
        "max_tier": plan.max_tier,
        "layers": len(plan.layers),
        "props": len(plan.props),
        "usda_bytes": len(usda),
        "usda_sha256": sha,
        "usda_sha256_prefix": sha[:12],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"dry-run: scene_name={plan.scene_name}")
        print(f"  layers={len(plan.layers)} props={len(plan.props)} max_tier={plan.max_tier}")
        print(f"  usda_bytes={len(usda)} sha256={sha[:12]}…")
        print(f"  (no files written)")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="assemble-usd-scene operator-side diagnostic CLI."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Validate env / deps / schema / scene-dir count")
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=_cmd_check)

    p_inspect = sub.add_parser("inspect",
                                help="Print scene plan structure without writing")
    p_inspect.add_argument("scene_yaml")
    p_inspect.add_argument("--json", action="store_true")
    p_inspect.set_defaults(func=_cmd_inspect)

    p_dry = sub.add_parser("dry-run",
                            help="Build plan + build_usda; report usda_sha256 but write nothing")
    p_dry.add_argument("scene_yaml")
    p_dry.add_argument("--json", action="store_true")
    p_dry.set_defaults(func=_cmd_dry_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
