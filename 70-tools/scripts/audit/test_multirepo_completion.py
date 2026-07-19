"""Completion guards for the root-to-west multirepo extraction."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_60_apps_has_no_implementation_directories():
    assert [path for path in (ROOT / "60-apps").iterdir() if path.is_dir()] == []


def test_60_apps_has_no_go_or_tinygo_sources():
    assert list((ROOT / "60-apps").rglob("*.go")) == []


def test_20_actors_directories_are_marker_only():
    canonical_markers = {"MOVED.edn", "README.edn", "migration.edn"}
    offenders = [
        path.relative_to(ROOT)
        for actor_dir in (ROOT / "20-actors").iterdir()
        if actor_dir.is_dir()
        for path in actor_dir.rglob("*")
        if path.is_file() and path.name not in canonical_markers
    ]
    assert offenders == []


def test_active_root_configs_do_not_reference_extracted_60_apps_paths():
    active_files = (
        ROOT / "pnpm-workspace.yaml",
        ROOT / ".github" / "dependabot.yml",
        ROOT / "70-tools" / "scripts" / "open-ot" / "validate-cell-abi.py",
        ROOT / "70-tools" / "scripts" / "guard" / "check-auth-worker-config.mjs",
    )
    offenders = [path.relative_to(ROOT) for path in active_files if "60-apps/" in path.read_text()]
    assert offenders == []
