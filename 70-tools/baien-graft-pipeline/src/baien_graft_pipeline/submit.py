"""Submit N images to a baien-graft generator backend (ComfyUI or Pixal3D),
poll until all complete.

`--generator hunyuan3d` (default) goes to ComfyUI on EVO-X2.
`--generator pixal3d`  goes to a Pixal3D Gradio endpoint (locally
cloned Space or upstream HF Space — see `generators/pixal3d.py`).
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests

from .generators import GENERATOR_REGISTRY
from .generators.hunyuan3d import hunyuan3d_workflow
from .generators.pixal3d import pixal3d_request_body


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generator", choices=list(GENERATOR_REGISTRY.keys()),
                   default=os.environ.get("BGP_GENERATOR", "hunyuan3d"),
                   help="image→3D backend (default: hunyuan3d)")
    p.add_argument("--comfy-url", default=os.environ.get("BGP_COMFY_URL", "http://192.168.1.22:8188"),
                   help="ComfyUI base (for --generator hunyuan3d)")
    p.add_argument("--pixal3d-url", default=os.environ.get("BGP_PIXAL3D_URL", "http://192.168.1.22:7860"),
                   help="Pixal3D Gradio base (for --generator pixal3d; default = locally-served Space)")
    p.add_argument("--images", required=True, help="comma-separated image filenames or local paths")
    p.add_argument("--out-log", required=True, type=Path, help="JSON log of jobs + per-job elapsed_sec")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--poll-interval-sec", type=int, default=20)
    p.add_argument("--max-wait-sec", type=int, default=7200)
    args = p.parse_args()

    spec = GENERATOR_REGISTRY[args.generator]
    print(f"[bgp] generator={spec.name} ({spec.description})")
    print(f"[bgp] license={spec.license} typical_runtime={spec.typical_runtime_sec}s/sample")

    images = [s.strip() for s in args.images.split(",") if s.strip()]
    jobs: list[dict] = []

    if args.generator == "hunyuan3d":
        print(f"submitting {len(images)} jobs to {args.comfy_url}")
        for img in images:
            slug = os.path.splitext(img)[0]
            body = hunyuan3d_workflow(img, slug, seed=args.seed)
            r = requests.post(f"{args.comfy_url}/prompt", json=body, timeout=15)
            r.raise_for_status()
            pid = r.json().get("prompt_id")
            jobs.append({"image": img, "slug": slug, "prompt_id": pid, "backend": "hunyuan3d"})
            print(f"  [{img}] -> {pid}")
    elif args.generator == "pixal3d":
        # Gradio /api/predict is synchronous per call — we poll synchronously
        # rather than via ComfyUI history. Each request is one full sample.
        print(f"submitting {len(images)} jobs to {args.pixal3d_url}")
        for img in images:
            slug = os.path.splitext(img)[0]
            body = pixal3d_request_body(img, seed=args.seed)
            print(f"  [{img}] -> POST {args.pixal3d_url}/api/predict (sync)")
            t0 = time.time()
            r = requests.post(f"{args.pixal3d_url}/api/predict", json=body,
                              timeout=args.max_wait_sec)
            r.raise_for_status()
            jobs.append({
                "image": img, "slug": slug, "backend": "pixal3d",
                "elapsed_sec": round(time.time() - t0, 1),
                "result": r.json(),
            })
        # Pixal3D path is fully synchronous — skip the polling loop below.
        args.out_log.parent.mkdir(parents=True, exist_ok=True)
        args.out_log.write_text(json.dumps(jobs, indent=2, ensure_ascii=False),
                                encoding="utf-8")
        print(f"\n[bgp] wrote {len(jobs)} jobs to {args.out_log}")
        return

    print(f"\nwaiting for completion (poll every {args.poll_interval_sec}s)")
    t0 = time.time()
    done: set[str] = set()
    while len(done) < len(jobs):
        if time.time() - t0 > args.max_wait_sec:
            print(f"TIMEOUT after {args.max_wait_sec}s with {len(done)}/{len(jobs)} done")
            break
        try:
            q = requests.get(f"{args.comfy_url}/queue", timeout=10).json()
            running = len(q.get("queue_running", []))
            pending = len(q.get("queue_pending", []))
        except Exception:
            running = pending = -1
        for j in jobs:
            if j["prompt_id"] in done:
                continue
            try:
                h = requests.get(f"{args.comfy_url}/history/{j['prompt_id']}", timeout=10).json()
            except Exception:
                continue
            if h:
                st = list(h.values())[0].get("status", {}).get("status_str")
                done.add(j["prompt_id"])
                j["status"] = st
                j["elapsed_sec"] = round(time.time() - t0, 1)
                print(f"  done: {j['slug']} ({st}) @ {j['elapsed_sec']}s [{len(done)}/{len(jobs)}]")
        if len(done) < len(jobs):
            print(f"  [{time.time()-t0:.0f}s] running={running} pending={pending} done={len(done)}/{len(jobs)}")
            time.sleep(args.poll_interval_sec)

    elapsed = time.time() - t0
    print(f"\nall done in {elapsed:.1f}s")
    args.out_log.parent.mkdir(parents=True, exist_ok=True)
    args.out_log.write_text(
        json.dumps({"jobs": jobs, "total_elapsed_sec": elapsed, "started_at": t0}, indent=2)
    )
    print(f"wrote {args.out_log}")


if __name__ == "__main__":
    main()
