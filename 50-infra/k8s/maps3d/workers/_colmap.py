"""COLMAP CPU pipeline driver.

Wraps the seven-step COLMAP subprocess chain (feature_extractor →
exhaustive_matcher → mapper → image_undistorter → patch_match_stereo →
stereo_fusion → delaunay_mesher) with strict per-step timeouts, output
capture, and a classifier that maps COLMAP stderr / exit codes to the
errorCode taxonomy declared in `colmapTile.json`.

Pure subprocess + filesystem — no broker, no B2, no GPU. Can be unit-
tested by passing a fake `runner` that returns canned results.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Sequence

log = logging.getLogger("maps3d.colmap")

# Error code taxonomy — must match colmapTile.json `errorCode` enum.
ERR_TOO_FEW_MATCHES = "TOO_FEW_MATCHES"
ERR_BUNDLE_DIVERGED = "BUNDLE_DIVERGED"
ERR_DENSE_OOM = "DENSE_OOM"
ERR_TIMEOUT = "TIMEOUT"
ERR_UNKNOWN = "UNKNOWN"


@dataclass
class StepResult:
    name: str
    returncode: int
    duration_ms: int
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class PipelineResult:
    ok: bool
    raw_mesh: Path | None = None
    image_count: int = 0  # cameras COLMAP successfully registered
    vertex_count: int = 0
    triangle_count: int = 0
    duration_ms: int = 0
    error_code: str | None = None
    error_message: str = ""
    steps: list[StepResult] = field(default_factory=list)


# Public type for dependency injection — tests pass a fake runner.
SubprocessRunner = Callable[
    [Sequence[str], float],
    Awaitable[StepResult],
]


# ─── Stderr / exit-code classifier ──────────────────────────────────


# COLMAP stderr fingerprints. These are pattern-matched in priority
# order — earlier rules win. Keep narrow (full-line tokens) so we don't
# misclassify on substrings of unrelated logs.
_FAILURE_RULES: list[tuple[str, re.Pattern[str]]] = [
    (ERR_TOO_FEW_MATCHES, re.compile(
        r"(no good initial image pair found"
        r"|less than \d+ images registered"
        r"|registered \d+ images, expected at least"
        r"|no two-view geometries|insufficient inliers)",
        re.IGNORECASE,
    )),
    (ERR_BUNDLE_DIVERGED, re.compile(
        r"(bundle adjustment did not converge"
        r"|reconstruction failed"
        r"|sparse reconstruction failed"
        r"|degenerate configuration)",
        re.IGNORECASE,
    )),
    (ERR_DENSE_OOM, re.compile(
        r"(out of memory|cannot allocate|bad_alloc|killed: 9)",
        re.IGNORECASE,
    )),
]


def classify_failure(stderr: str, returncode: int) -> tuple[str, str]:
    """Return (error_code, short_message) from COLMAP stderr + exit code.

    Used both inline by `run_pipeline` and by the unit tests in this file.
    """
    if not stderr and returncode == 0:
        return ERR_UNKNOWN, "unknown failure (returncode=0, empty stderr)"
    for code, pat in _FAILURE_RULES:
        m = pat.search(stderr)
        if m:
            return code, _short_msg(stderr, m.start())
    if returncode == 137 or returncode == -9:  # SIGKILL — usually OOMKill on k8s
        return ERR_DENSE_OOM, f"process killed (rc={returncode})"
    if returncode == 124:  # GNU timeout(1) sentinel — we use Python asyncio though
        return ERR_TIMEOUT, "step exceeded budget"
    return ERR_UNKNOWN, _short_msg(stderr or "(no stderr)", 0)


def _short_msg(s: str, anchor: int, span: int = 200) -> str:
    """Pick a `span`-byte window around `anchor` for the error message."""
    if not s:
        return "(no stderr)"
    start = max(0, anchor - span // 2)
    end = min(len(s), start + span)
    return s[start:end].strip().replace("\n", " | ")


# ─── Subprocess runner ──────────────────────────────────────────────


async def default_runner(cmd: Sequence[str], timeout_s: float) -> StepResult:
    """asyncio.create_subprocess_exec wrapper that enforces a hard
    timeout via process-group SIGKILL on the child + descendants.

    `cmd` is a list of args. stdout / stderr are captured (last 4 KiB
    each, so we don't blow up on a chatty COLMAP run). On timeout we
    SIGTERM, wait 5s, then SIGKILL the whole process group — the
    COLMAP subprocess tree often spawns OpenMP threads that ignore
    SIGTERM on the main pid alone.
    """
    t0 = time.perf_counter()
    log.info("$ %s (budget %.0fs)", " ".join(cmd), timeout_s)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        # Put the child in its own process group so SIGKILL via
        # killpg() catches every descendant (COLMAP spawns OpenMP
        # workers that survive a plain proc.kill on Linux).
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
        rc = proc.returncode if proc.returncode is not None else -1
    except asyncio.TimeoutError:
        log.warning("step %s timed out at %.0fs — SIGTERM → SIGKILL", cmd[1] if len(cmd) > 1 else cmd[0], timeout_s)
        _kill_process_tree(proc)
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        except asyncio.TimeoutError:
            stdout_b, stderr_b = b"", b"timeout, killed"
        rc = -1  # sentinel: timed out
    dur_ms = int((time.perf_counter() - t0) * 1000)
    name = cmd[1] if len(cmd) > 1 else cmd[0]
    return StepResult(
        name=name,
        returncode=rc,
        duration_ms=dur_ms,
        stdout_tail=(stdout_b[-4096:] or b"").decode("utf-8", errors="replace"),
        stderr_tail=(stderr_b[-4096:] or b"").decode("utf-8", errors="replace"),
    )


def _kill_process_tree(proc: asyncio.subprocess.Process) -> None:
    """Send SIGTERM, wait briefly, escalate to SIGKILL on the whole
    process group. No-op on platforms without setsid (e.g. macOS in
    some test environments)."""
    if proc.pid is None:
        return
    if not hasattr(os, "killpg"):
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    # Async sleep would require an event loop here; we're already
    # inside one but don't block too long. The wait_for above gives
    # the child a 5s grace, and then we hard-kill.
    time.sleep(0.2)
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


# ─── Output parsers ─────────────────────────────────────────────────


_RE_REGISTERED = re.compile(r"Registered (\d+) images", re.IGNORECASE)


def parse_registered_images(text: str) -> int:
    """COLMAP `mapper` prints e.g. 'Registered 23 images.' on success."""
    last = 0
    for m in _RE_REGISTERED.finditer(text):
        try:
            last = int(m.group(1))
        except ValueError:
            pass
    return last


def parse_ply_counts(ply_path: Path) -> tuple[int, int]:
    """Return (vertex_count, triangle_count) from a PLY header. Cheap —
    we only read the ASCII header before the first `end_header` line."""
    if not ply_path.exists():
        return 0, 0
    verts = 0
    tris = 0
    try:
        with ply_path.open("rb") as f:
            for raw in f:
                line = raw.decode("ascii", errors="replace").strip()
                if line == "end_header":
                    break
                if line.startswith("element vertex "):
                    verts = int(line.split()[-1])
                elif line.startswith("element face "):
                    tris = int(line.split()[-1])
    except (OSError, ValueError):
        return verts, tris
    return verts, tris


# ─── Pipeline driver ────────────────────────────────────────────────


async def run_pipeline(
    *,
    image_dir: Path,
    work_dir: Path,
    colmap_bin: str,
    total_budget_s: float,
    dense_enabled: bool = True,
    matcher: str = "exhaustive",
    runner: SubprocessRunner | None = None,
    threads: int | None = None,
) -> PipelineResult:
    """Drive the seven-step COLMAP CPU pipeline.

    `runner` is injectable for tests. `total_budget_s` is the
    end-to-end ceiling — each step gets a fraction of the remaining
    budget (denser steps get more).
    """
    runner = runner or default_runner
    threads = threads or max(1, (os.cpu_count() or 2) - 1)

    work_dir.mkdir(parents=True, exist_ok=True)
    db_path = work_dir / "database.db"
    sparse_dir = work_dir / "sparse"
    sparse_dir.mkdir(exist_ok=True)
    dense_dir = work_dir / "dense"
    fused_path = dense_dir / "fused.ply"
    meshed_path = dense_dir / "meshed.ply" if dense_enabled else sparse_dir / "0" / "meshed.ply"

    result = PipelineResult(ok=False)
    t_start = time.perf_counter()

    def remaining_budget(min_floor: float = 5.0) -> float:
        spent = time.perf_counter() - t_start
        return max(min_floor, total_budget_s - spent)

    # Per-step share of remaining budget. Numbers tuned for CPU COLMAP
    # at 1080p × ~30 images: matching is the second-heaviest step,
    # patch_match_stereo dominates wall-clock.
    step_share = {
        "feature_extractor": 0.10,
        "matcher": 0.20,
        "mapper": 0.20,
        "image_undistorter": 0.05,
        "patch_match_stereo": 0.40,
        "stereo_fusion": 0.10,
        "delaunay_mesher": 0.10,
    }

    async def step(name: str, cmd: list[str]) -> StepResult:
        budget = remaining_budget() * step_share.get(name, 0.10)
        sr = await runner(cmd, budget)
        result.steps.append(sr)
        return sr

    # 1. feature_extractor
    sr = await step("feature_extractor", [
        colmap_bin, "feature_extractor",
        "--database_path", str(db_path),
        "--image_path", str(image_dir),
        "--SiftExtraction.use_gpu", "0",
        "--SiftExtraction.num_threads", str(threads),
    ])
    if sr.returncode == -1:
        result.error_code = ERR_TIMEOUT
        result.error_message = "feature_extractor timed out"
        return _finalize(result, t_start)
    if sr.returncode != 0:
        result.error_code, result.error_message = classify_failure(sr.stderr_tail, sr.returncode)
        return _finalize(result, t_start)

    # 2. matcher
    matcher_cmd = {
        "exhaustive": "exhaustive_matcher",
        "sequential": "sequential_matcher",
        "spatial": "spatial_matcher",
    }.get(matcher, "exhaustive_matcher")
    sr = await step("matcher", [
        colmap_bin, matcher_cmd,
        "--database_path", str(db_path),
        "--SiftMatching.use_gpu", "0",
        "--SiftMatching.num_threads", str(threads),
    ])
    if sr.returncode == -1:
        result.error_code = ERR_TIMEOUT
        result.error_message = f"{matcher_cmd} timed out"
        return _finalize(result, t_start)
    if sr.returncode != 0:
        result.error_code, result.error_message = classify_failure(sr.stderr_tail, sr.returncode)
        return _finalize(result, t_start)

    # 3. mapper — incremental SfM
    sr = await step("mapper", [
        colmap_bin, "mapper",
        "--database_path", str(db_path),
        "--image_path", str(image_dir),
        "--output_path", str(sparse_dir),
        "--Mapper.num_threads", str(threads),
    ])
    if sr.returncode == -1:
        result.error_code = ERR_TIMEOUT
        result.error_message = "mapper timed out"
        return _finalize(result, t_start)
    result.image_count = parse_registered_images(sr.stdout_tail + "\n" + sr.stderr_tail)
    if sr.returncode != 0 or result.image_count < 3:
        # mapper sometimes exits 0 even when it produced no model;
        # treat <3 cameras as a reconstruction failure.
        if sr.returncode != 0:
            result.error_code, result.error_message = classify_failure(sr.stderr_tail, sr.returncode)
        else:
            result.error_code = ERR_TOO_FEW_MATCHES
            result.error_message = f"mapper registered only {result.image_count} cameras"
        return _finalize(result, t_start)

    if not dense_enabled:
        # Sparse-only fallback — skip MVS, mesh from the sparse cloud.
        sparse_zero = sparse_dir / "0"
        if sparse_zero.is_dir():
            # Use poisson_mesher input from sparse points3D — actually
            # delaunay_mesher needs dense; sparse-only path emits the
            # sparse points as-is (no mesh). We mark ok with empty
            # raw mesh so the BPMN can downgrade to OSM.
            result.ok = True
            result.error_code = ERR_TOO_FEW_MATCHES
            result.error_message = "sparse-only fallback: no dense mesh"
        else:
            result.error_code = ERR_BUNDLE_DIVERGED
            result.error_message = "no sparse model produced"
        return _finalize(result, t_start)

    # 4. image_undistorter
    dense_dir.mkdir(exist_ok=True)
    sr = await step("image_undistorter", [
        colmap_bin, "image_undistorter",
        "--image_path", str(image_dir),
        "--input_path", str(sparse_dir / "0"),
        "--output_path", str(dense_dir),
        "--output_type", "COLMAP",
    ])
    if sr.returncode == -1:
        result.error_code = ERR_TIMEOUT
        result.error_message = "image_undistorter timed out"
        return _finalize(result, t_start)
    if sr.returncode != 0:
        result.error_code, result.error_message = classify_failure(sr.stderr_tail, sr.returncode)
        return _finalize(result, t_start)

    # 5. patch_match_stereo (the heaviest step)
    sr = await step("patch_match_stereo", [
        colmap_bin, "patch_match_stereo",
        "--workspace_path", str(dense_dir),
        "--PatchMatchStereo.gpu_index", "-1",
        "--PatchMatchStereo.num_iterations", "5",
    ])
    if sr.returncode == -1:
        result.error_code = ERR_TIMEOUT
        result.error_message = "patch_match_stereo timed out"
        return _finalize(result, t_start)
    if sr.returncode != 0:
        result.error_code, result.error_message = classify_failure(sr.stderr_tail, sr.returncode)
        return _finalize(result, t_start)

    # 6. stereo_fusion → fused.ply
    sr = await step("stereo_fusion", [
        colmap_bin, "stereo_fusion",
        "--workspace_path", str(dense_dir),
        "--output_path", str(fused_path),
    ])
    if sr.returncode == -1:
        result.error_code = ERR_TIMEOUT
        result.error_message = "stereo_fusion timed out"
        return _finalize(result, t_start)
    if sr.returncode != 0:
        result.error_code, result.error_message = classify_failure(sr.stderr_tail, sr.returncode)
        return _finalize(result, t_start)

    # 7. delaunay_mesher → meshed.ply
    sr = await step("delaunay_mesher", [
        colmap_bin, "delaunay_mesher",
        "--input_path", str(dense_dir),
        "--output_path", str(meshed_path),
    ])
    if sr.returncode == -1:
        result.error_code = ERR_TIMEOUT
        result.error_message = "delaunay_mesher timed out"
        return _finalize(result, t_start)
    if sr.returncode != 0:
        result.error_code, result.error_message = classify_failure(sr.stderr_tail, sr.returncode)
        return _finalize(result, t_start)

    if not meshed_path.exists():
        result.error_code = ERR_UNKNOWN
        result.error_message = "delaunay_mesher returned 0 but produced no PLY"
        return _finalize(result, t_start)

    verts, tris = parse_ply_counts(meshed_path)
    result.vertex_count = verts
    result.triangle_count = tris
    result.raw_mesh = meshed_path
    result.ok = True
    return _finalize(result, t_start)


def _finalize(result: PipelineResult, t_start: float) -> PipelineResult:
    result.duration_ms = int((time.perf_counter() - t_start) * 1000)
    return result


# ─── Filesystem helpers ─────────────────────────────────────────────


def cleanup_workdir(work_dir: Path) -> None:
    """Best-effort scratch cleanup. Called between tiles so /scratch
    doesn't accumulate. Safe to call on a missing directory."""
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
