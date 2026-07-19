"""Regression tests for west-flat absolute path handling in substrate-boundary."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
SCANNER = ROOT / "70-tools/scripts/lint/substrate-boundary.mjs"


def run_scanner(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(SCANNER), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_absolute_flat_actor_path_is_scanned(tmp_path: Path) -> None:
    source = tmp_path / "orgs/etzhayyim/com-etzhayyim-demo/src/direct.ts"
    source.parent.mkdir(parents=True)
    source.write_text('import { AtpAgent } from "@atproto/' + 'api";\n')
    result = run_scanner(source)
    assert result.returncode == 1
    assert "substrate client seam" in result.stderr


def test_absolute_flat_sdk_path_is_allowed(tmp_path: Path) -> None:
    source = tmp_path / "orgs/etzhayyim/com-etzhayyim-sdk/src/direct.ts"
    source.parent.mkdir(parents=True)
    source.write_text('import { AtpAgent } from "@atproto/' + 'api";\n')
    result = run_scanner(source)
    assert result.returncode == 0
