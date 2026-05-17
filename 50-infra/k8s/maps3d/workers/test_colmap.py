"""Unit tests for `_colmap` — error classification + output parsing.

Pure unit tests; no subprocess, no COLMAP binary, no Open3D, no B2.
Run with `python -m pytest 50-infra/k8s/maps3d/workers/test_colmap.py`
or `python -m unittest 50-infra/k8s/maps3d/workers/test_colmap.py`.
"""

from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from . import _colmap
from ._colmap import (
    ERR_BUNDLE_DIVERGED,
    ERR_DENSE_OOM,
    ERR_TIMEOUT,
    ERR_TOO_FEW_MATCHES,
    ERR_UNKNOWN,
    PipelineResult,
    StepResult,
    classify_failure,
    parse_ply_counts,
    parse_registered_images,
    run_pipeline,
)


class ClassifyFailureTests(unittest.TestCase):
    def test_too_few_matches(self) -> None:
        for txt in [
            "ERROR: No good initial image pair found",
            "Less than 3 images registered",
            "Registered 1 images, expected at least 3",
        ]:
            code, _ = classify_failure(txt, returncode=1)
            self.assertEqual(code, ERR_TOO_FEW_MATCHES, txt)

    def test_bundle_diverged(self) -> None:
        code, _ = classify_failure("Bundle adjustment did not converge", 1)
        self.assertEqual(code, ERR_BUNDLE_DIVERGED)

        code, _ = classify_failure("Sparse reconstruction failed", 1)
        self.assertEqual(code, ERR_BUNDLE_DIVERGED)

    def test_dense_oom(self) -> None:
        code, _ = classify_failure("std::bad_alloc: Out of memory", 1)
        self.assertEqual(code, ERR_DENSE_OOM)

        # Linux OOMKill via SIGKILL → returncode 137 (or -9 in Python).
        code, _ = classify_failure("", returncode=137)
        self.assertEqual(code, ERR_DENSE_OOM)
        code, _ = classify_failure("", returncode=-9)
        self.assertEqual(code, ERR_DENSE_OOM)

    def test_timeout_returncode(self) -> None:
        code, _ = classify_failure("", returncode=124)
        self.assertEqual(code, ERR_TIMEOUT)

    def test_unknown_falls_through(self) -> None:
        code, _ = classify_failure("some random colmap warning", 1)
        self.assertEqual(code, ERR_UNKNOWN)

    def test_empty_stderr_zero_rc(self) -> None:
        code, msg = classify_failure("", 0)
        self.assertEqual(code, ERR_UNKNOWN)
        self.assertIn("returncode=0", msg)


class ParseRegisteredImagesTests(unittest.TestCase):
    def test_basic(self) -> None:
        text = "==== Registered 23 images.\nfinishing up..."
        self.assertEqual(parse_registered_images(text), 23)

    def test_returns_last_count(self) -> None:
        # mapper logs progress; last "Registered N" wins.
        text = "Registered 5 images.\nRegistered 12 images.\nRegistered 27 images."
        self.assertEqual(parse_registered_images(text), 27)

    def test_no_match(self) -> None:
        self.assertEqual(parse_registered_images("nothing useful here"), 0)


class ParsePlyCountsTests(unittest.TestCase):
    def test_ascii_header(self) -> None:
        ply = (
            b"ply\n"
            b"format ascii 1.0\n"
            b"element vertex 12345\n"
            b"property float x\n"
            b"element face 24690\n"
            b"property list uchar int vertex_indices\n"
            b"end_header\n"
            b"... vertex data omitted ...\n"
        )
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.ply"
            p.write_bytes(ply)
            v, t = parse_ply_counts(p)
            self.assertEqual(v, 12345)
            self.assertEqual(t, 24690)

    def test_missing_file(self) -> None:
        v, t = parse_ply_counts(Path("/nonexistent/foo.ply"))
        self.assertEqual((v, t), (0, 0))


# ─── Pipeline driver — fake runner so we don't need COLMAP binary ────


def _runner_factory(plan: list[StepResult]) -> _colmap.SubprocessRunner:
    """Return a runner that pops StepResults off `plan` in order."""
    queue = list(plan)

    async def _runner(cmd: list[str], timeout_s: float) -> StepResult:
        if not queue:
            return StepResult(name=cmd[1] if len(cmd) > 1 else "?", returncode=1, duration_ms=0,
                              stderr_tail="ran past plan")
        return queue.pop(0)

    return _runner


class RunPipelineTests(unittest.TestCase):
    def test_too_few_matches_at_mapper_short_circuits(self) -> None:
        # feature_extractor + matcher succeed, mapper returns rc=0 but
        # only registers 1 camera ⇒ TOO_FEW_MATCHES synthesized.
        plan = [
            StepResult("feature_extractor", 0, 1000),
            StepResult("matcher", 0, 1000),
            StepResult("mapper", 0, 1000, stdout_tail="Registered 1 images.\n"),
        ]
        with TemporaryDirectory() as tmp:
            res: PipelineResult = asyncio.run(run_pipeline(
                image_dir=Path(tmp), work_dir=Path(tmp) / "w",
                colmap_bin="/dev/null", total_budget_s=120.0,
                runner=_runner_factory(plan),
            ))
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, ERR_TOO_FEW_MATCHES)
        self.assertEqual(res.image_count, 1)
        self.assertEqual(len(res.steps), 3)

    def test_timeout_on_first_step(self) -> None:
        plan = [
            StepResult("feature_extractor", -1, 60_000, stderr_tail="timeout, killed"),
        ]
        with TemporaryDirectory() as tmp:
            res = asyncio.run(run_pipeline(
                image_dir=Path(tmp), work_dir=Path(tmp) / "w",
                colmap_bin="/dev/null", total_budget_s=60.0,
                runner=_runner_factory(plan),
            ))
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, ERR_TIMEOUT)
        self.assertEqual(len(res.steps), 1)

    def test_sparse_only_path_skips_dense(self) -> None:
        # dense_enabled=False ⇒ pipeline stops after mapper. Mark
        # ok=True with empty raw_mesh + downgrade hint so caller can
        # choose how to react.
        plan = [
            StepResult("feature_extractor", 0, 100),
            StepResult("matcher", 0, 100),
            StepResult("mapper", 0, 100, stdout_tail="Registered 12 images.\n"),
        ]
        with TemporaryDirectory() as tmp:
            sparse_zero = Path(tmp) / "w" / "sparse" / "0"
            sparse_zero.mkdir(parents=True)
            res = asyncio.run(run_pipeline(
                image_dir=Path(tmp), work_dir=Path(tmp) / "w",
                colmap_bin="/dev/null", total_budget_s=60.0,
                runner=_runner_factory(plan),
                dense_enabled=False,
            ))
        self.assertTrue(res.ok)
        self.assertEqual(res.image_count, 12)
        self.assertIsNone(res.raw_mesh)
        # Sparse-only carries an advisory error_code.
        self.assertEqual(res.error_code, ERR_TOO_FEW_MATCHES)


if __name__ == "__main__":
    unittest.main()
