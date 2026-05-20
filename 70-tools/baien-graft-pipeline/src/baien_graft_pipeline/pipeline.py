"""End-to-end batch pipeline: pull GLB, render 4-view, caption, assemble sample.json."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from .caption import FlorenceCaptioner
from .gate import primary_gate, sanity_gate
from .render import render_4view


def _sha1(p: Path) -> str:
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _scp(remote_path: str, local_path: Path, ssh_alias: str) -> bool:
    rc = subprocess.run(["scp", "-q", f"{ssh_alias}:{remote_path}", str(local_path)]).returncode
    return rc == 0


def process_one(
    job: dict,
    out_root: Path,
    *,
    captioner: FlorenceCaptioner,
    ssh_alias: str,
    remote_input_dir: str,
    remote_output_dir: str,
) -> dict | None:
    if job.get("status") != "success":
        print(f"SKIP {job['slug']} ({job.get('status')})")
        return None

    sample_dir = out_root / job["slug"]
    (sample_dir / "source").mkdir(parents=True, exist_ok=True)
    (sample_dir / "mesh").mkdir(parents=True, exist_ok=True)
    (sample_dir / "renders").mkdir(parents=True, exist_ok=True)

    glb_local = sample_dir / "mesh" / "hunyuan3d.glb"
    img_local = sample_dir / "source" / job["image"]
    if not _scp(f"{remote_output_dir}/baien-graft/batch/{job['slug']}_00001_.glb", glb_local, ssh_alias):
        return {"slug": job["slug"], "scp_error": "glb"}
    if not _scp(f"{remote_input_dir}/{job['image']}", img_local, ssh_alias):
        return {"slug": job["slug"], "scp_error": "image"}

    t_r0 = time.time()
    paths, stats = render_4view(glb_local, sample_dir / "renders", "hunyuan3d")
    t_render = time.time() - t_r0

    t_c0 = time.time()
    src_cap = captioner.caption(img_local)
    view_caps = {k: captioner.caption(v) for k, v in paths.items() if k != "tile"}
    tile_cap = captioner.caption(paths["tile"])
    t_cap = time.time() - t_c0

    matches, gate_details = primary_gate(src_cap, view_caps)
    sanity_ok = sanity_gate(stats)
    accepted = (matches == 4) and sanity_ok

    sample = {
        "schema": {
            "id": "dataset.baien-graft.3d-augmented",
            "version": "v0",
            "task": "image-grounded-text",
            "variant": "3d-augmented",
            "ref_adr": "2605202115",
        },
        "sample_id": job["slug"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": {
            "image_path": f"source/{job['image']}",
            "image_sha1": _sha1(img_local),
            "image_caption_2d_only": src_cap,
            "captioner": "microsoft/Florence-2-large-ft @ <MORE_DETAILED_CAPTION>",
        },
        "candidate": {
            "tool": "Tencent/Hunyuan3D-2 via kijai/ComfyUI-Hunyuan3DWrapper",
            "params": {"guidance_scale": 5.5, "steps": 30, "seed": 42, "octree_resolution": 384, "mc_algo": "mc"},
            "wall_clock_sec_gen": job.get("elapsed_sec"),
            "wall_clock_sec_render": round(t_render, 1),
            "wall_clock_sec_caption": round(t_cap, 1),
            "mesh_path": "mesh/hunyuan3d.glb",
            "mesh_sha1": _sha1(glb_local),
            "mesh_stats": stats,
            "renders": {
                k: f"renders/hunyuan3d_{k}.png" if k != "tile" else "renders/hunyuan3d_4view_tile.png"
                for k in paths
            },
            "captions": {"tile": tile_cap, **{f"view_{k}": v for k, v in view_caps.items()}},
        },
        "acceptance_gate": {
            "primary_4view_noun_matches": matches,
            "primary_pass": matches == 4,
            "sanity_pass": sanity_ok,
            "accepted": accepted,
            "details_per_view": gate_details,
        },
        "baien_supervision_pair_v0": {
            "x_image_2d_path": f"source/{job['image']}",
            "y_caption_3d_augmented": (
                src_cap
                + " [3D-augmented from Hunyuan3D-2 mesh, viewed from 4 cardinal angles]"
                + " Front: "
                + view_caps["front"]
                + " Right: "
                + view_caps["right"]
                + " Back: "
                + view_caps["back"]
                + " Left: "
                + view_caps["left"]
            ),
            "preferred_candidate": "hunyuan3d_2",
            "accepted": accepted,
        },
    }
    (sample_dir / "sample.json").write_text(json.dumps(sample, indent=2, ensure_ascii=False))
    return {
        "slug": job["slug"],
        "image": job["image"],
        "gen_sec": job.get("elapsed_sec"),
        "render_sec": round(t_render, 1),
        "caption_sec": round(t_cap, 1),
        "4view_matches": matches,
        "sanity_pass": sanity_ok,
        "accepted": accepted,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jobs-log", required=True, type=Path, help="output of `bgp-submit --out-log`")
    p.add_argument("--out-root", required=True, type=Path, help="root of per-sample dirs")
    p.add_argument("--ssh-alias", default=os.environ.get("BGP_SSH_ALIAS", "evo"))
    p.add_argument(
        "--remote-input-dir",
        default="/c:/Users/gad/ComfyUI/ComfyUI_windows_portable/ComfyUI/input",
    )
    p.add_argument(
        "--remote-output-dir",
        default="/c:/Users/gad/ComfyUI/ComfyUI_windows_portable/ComfyUI/output",
    )
    args = p.parse_args()

    jobs_log = json.loads(args.jobs_log.read_text())
    args.out_root.mkdir(parents=True, exist_ok=True)

    print("Loading Florence-2...")
    captioner = FlorenceCaptioner()

    t0 = time.time()
    summary = []
    for j in jobs_log["jobs"]:
        print(f"\n=== {j['slug']} ===")
        res = process_one(
            j,
            args.out_root,
            captioner=captioner,
            ssh_alias=args.ssh_alias,
            remote_input_dir=args.remote_input_dir,
            remote_output_dir=args.remote_output_dir,
        )
        if res:
            summary.append(res)
            print(
                f"  gen={res.get('gen_sec')}s render={res.get('render_sec')}s "
                f"caption={res.get('caption_sec')}s gate={res.get('4view_matches')}/4 acc={res.get('accepted')}"
            )

    elapsed_total = time.time() - t0
    batch_summary = {
        "batch_id": args.out_root.name,
        "n_input": len(jobs_log["jobs"]),
        "n_completed": len(summary),
        "n_accepted": sum(1 for s in summary if s.get("accepted")),
        "n_rejected": sum(1 for s in summary if not s.get("accepted")),
        "total_elapsed_sec_render_caption_assemble": round(elapsed_total, 1),
        "comfyui_gen_total_sec": round(jobs_log.get("total_elapsed_sec", 0), 1),
        "samples": summary,
    }
    (args.out_root / "batch_summary.json").write_text(
        json.dumps(batch_summary, indent=2, ensure_ascii=False)
    )
    print(f"\n=== BATCH SUMMARY ===")
    print(f"input:     {batch_summary['n_input']}")
    print(f"completed: {batch_summary['n_completed']}")
    print(f"accepted:  {batch_summary['n_accepted']}")
    print(f"rejected:  {batch_summary['n_rejected']}")
    print(f"gen total (ComfyUI sequential):   {batch_summary['comfyui_gen_total_sec']}s")
    print(f"render+caption+assemble total:    {batch_summary['total_elapsed_sec_render_caption_assemble']}s")
    print(f"summary at {args.out_root/'batch_summary.json'}")


if __name__ == "__main__":
    main()
