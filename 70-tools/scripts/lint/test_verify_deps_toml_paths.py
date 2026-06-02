"""Tests for verify_deps_toml_paths.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "verify_deps_toml_paths.py"


@pytest.fixture(scope="module")
def verifier():
    spec = importlib.util.spec_from_file_location("verify_deps_toml_paths", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["verify_deps_toml_paths"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_deps_toml(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_all_paths_valid(verifier, tmp_path):
    """Every [[adrs]] + [[modules]] path exists → empty missing list."""
    (tmp_path / "real-adr.md").write_text("# adr")
    (tmp_path / "real-module.py").write_text("# code")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[adrs]]
id = "test-1"
path = "real-adr.md"

[[modules]]
path = "real-module.py"
adr = "ADR-test-1"
""")
    results = verifier.check_paths(deps, tmp_path)
    assert len(results) == 2
    assert all(r.exists for r in results)


def test_missing_paths_reported(verifier, tmp_path):
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[adrs]]
id = "test-missing"
path = "does-not-exist.md"

[[modules]]
path = "also-missing.py"
adr = "ADR-test-missing"
""")
    results = verifier.check_paths(deps, tmp_path)
    assert len(results) == 2
    assert all(not r.exists for r in results)
    # Section labels preserved.
    sections = {r.section for r in results}
    assert sections == {"adrs", "modules"}


def test_mixed_valid_and_missing(verifier, tmp_path):
    (tmp_path / "exists.py").write_text("x")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "exists.py"
adr = "ADR-1"

[[modules]]
path = "ghost.py"
adr = "ADR-2"
""")
    results = verifier.check_paths(deps, tmp_path)
    assert len(results) == 2
    ok = [r for r in results if r.exists]
    missing = [r for r in results if not r.exists]
    assert len(ok) == 1
    assert ok[0].path == "exists.py"
    assert len(missing) == 1
    assert missing[0].path == "ghost.py"


def test_filter_by_token(verifier, tmp_path):
    """--filter limits the audit scope to entries matching the token."""
    (tmp_path / "keep.py").write_text("x")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "keep.py"
adr = "ADR-2605262500"

[[modules]]
path = "different.py"
adr = "ADR-2605262400"
""")
    results = verifier.check_paths(deps, tmp_path, filter_token="2605262500")
    assert len(results) == 1
    assert results[0].path == "keep.py"


def test_directory_path_accepted(verifier, tmp_path):
    """Directory paths (e.g., scenes/foo/) resolve when the dir exists."""
    (tmp_path / "scenes").mkdir()
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "scenes/"
adr = "ADR-x"
""")
    results = verifier.check_paths(deps, tmp_path)
    assert len(results) == 1
    assert results[0].exists


def test_main_cli_exit_0_when_all_resolve(verifier, tmp_path, capsys):
    """The CLI main() returns 0 when all paths resolve."""
    (tmp_path / "ok.py").write_text("x")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "ok.py"
adr = "ADR-x"
""")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
    ])
    assert rc == 0


def test_main_cli_exit_1_when_missing(verifier, tmp_path):
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "missing.py"
adr = "ADR-x"
""")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
    ])
    assert rc == 1


def test_main_json_output(verifier, tmp_path, capsys):
    (tmp_path / "real.py").write_text("x")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "real.py"
adr = "ADR-x"

[[modules]]
path = "fake.py"
adr = "ADR-x"
""")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
        "--json",
    ])
    assert rc == 1
    captured = capsys.readouterr()
    import json
    payload = json.loads(captured.out)
    assert payload["total"] == 2
    assert payload["ok"] == 1
    assert payload["drift_count"] == 1
    assert payload["drift"][0]["path"] == "fake.py"


def test_main_cli_parse_error(verifier, tmp_path):
    """Malformed deps.toml → exit 2."""
    deps = tmp_path / "deps.toml"
    deps.write_text("this is [[ not [[ valid toml")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
    ])
    assert rc == 2


def test_main_cli_missing_deps_toml(verifier, tmp_path):
    """deps.toml missing → exit 2."""
    rc = verifier.main([
        "--deps-toml", str(tmp_path / "does-not-exist.toml"),
        "--repo-root", str(tmp_path),
    ])
    assert rc == 2


def test_strip_reserved_marker_helper(verifier):
    """_strip_reserved_marker recognizes (reserved) and (deferred-rename) suffixes."""
    fn = verifier._strip_reserved_marker

    # No marker → returns path unchanged + None
    assert fn("90-docs/adr/2605262500-foo.md") == ("90-docs/adr/2605262500-foo.md", None)

    # (reserved) marker
    clean, marker = fn("90-docs/adr/foo.md (reserved)")
    assert clean == "90-docs/adr/foo.md"
    assert marker == "reserved"

    # (deferred-rename) marker
    clean, marker = fn("00-contracts/lexicons/com/etzhayyim/apps/unispsc (deferred-rename)")
    assert clean == "00-contracts/lexicons/com/etzhayyim/apps/unispsc"
    assert marker == "deferred-rename"

    # Unknown marker token is NOT stripped (regex is exact-match)
    assert fn("foo.md (placeholder)") == ("foo.md (placeholder)", None)

    # Trailing whitespace after marker is tolerated
    clean, marker = fn("foo.md (reserved)  ")
    assert clean == "foo.md"
    assert marker == "reserved"


def test_reserved_marker_counted_as_accepted(verifier, tmp_path):
    """Missing path with (reserved) suffix → is_accepted_missing, not drift."""
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[adrs]]
id = "2605250730"
path = "90-docs/adr/2605250730-tatekata-r1.md (reserved)"
""")
    results = verifier.check_paths(deps, tmp_path)
    assert len(results) == 1
    r = results[0]
    assert not r.exists           # underlying file is missing
    assert r.reserved_marker == "reserved"
    assert r.is_accepted_missing
    assert not r.is_drift
    assert not r.is_stale_marker


def test_reserved_marker_stale_when_path_exists(verifier, tmp_path):
    """Path exists but still carries (reserved) marker → stale, not drift."""
    (tmp_path / "real.md").write_text("# adr")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[adrs]]
id = "test-stale"
path = "real.md (reserved)"
""")
    results = verifier.check_paths(deps, tmp_path)
    assert len(results) == 1
    r = results[0]
    assert r.exists
    assert r.reserved_marker == "reserved"
    assert r.is_stale_marker
    assert not r.is_drift
    assert not r.is_accepted_missing


def test_reserved_marker_exits_0_not_1(verifier, tmp_path):
    """Audit with only accepted-reserved entries exits 0 (no real drift)."""
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[adrs]]
id = "test-reserved-only"
path = "future.md (reserved)"
""")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
    ])
    assert rc == 0  # accepted-reserved are NOT drift


def test_stale_marker_exits_0_not_1(verifier, tmp_path):
    """Audit with stale-marker entries exits 0 (warning, not drift)."""
    (tmp_path / "real.md").write_text("x")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[adrs]]
id = "test-stale"
path = "real.md (reserved)"
""")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
    ])
    assert rc == 0  # stale markers warn but don't fail


def test_drift_still_exits_1(verifier, tmp_path):
    """Bare missing entry (no marker) still exits 1."""
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "missing-no-marker.py"
adr = "ADR-x"
""")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
    ])
    assert rc == 1


def test_find_duplicates_detects_module_path_dupes(verifier, tmp_path):
    """find_duplicates returns 2+ entries when same path registered twice."""
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "shared.py"
adr = "ADR-1"
status = "stale"

[[modules]]
path = "shared.py"
adr = "ADR-1"
status = "current"

[[modules]]
path = "unique.py"
adr = "ADR-2"
""")
    dups = verifier.find_duplicates(deps)
    assert "modules:shared.py" in dups
    assert len(dups["modules:shared.py"]) == 2
    # The unique one is NOT in duplicates
    assert "modules:unique.py" not in dups


def test_find_duplicates_detects_adr_id_dupes(verifier, tmp_path):
    """ADR id duplicates are detected separately from module paths."""
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[adrs]]
id = "2605270000"
title = "First entry"
path = "first.md"

[[adrs]]
id = "2605270000"
title = "Second entry (dupe)"
path = "second.md"
""")
    dups = verifier.find_duplicates(deps)
    assert "adrs:2605270000" in dups
    assert len(dups["adrs:2605270000"]) == 2


def test_find_duplicates_strips_reserved_marker(verifier, tmp_path):
    """Same path with/without (reserved) marker counts as duplicate."""
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "future.py (reserved)"
adr = "ADR-1"

[[modules]]
path = "future.py"
adr = "ADR-1"
""")
    dups = verifier.find_duplicates(deps)
    assert "modules:future.py" in dups
    assert len(dups["modules:future.py"]) == 2


def test_main_exits_1_on_duplicates(verifier, tmp_path):
    """Duplicates trigger exit 1 (real drift)."""
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "dup.py"
adr = "ADR-1"

[[modules]]
path = "dup.py"
adr = "ADR-1"
""")
    # Ensure the file exists so non-dup tests don't false-positive
    (tmp_path / "dup.py").write_text("x")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
    ])
    # Duplicates fail even when paths resolve
    assert rc == 1


def test_json_output_separates_categories(verifier, tmp_path, capsys):
    """JSON payload exposes drift / accepted_missing / stale_markers separately."""
    (tmp_path / "real-stale.md").write_text("x")
    deps = tmp_path / "deps.toml"
    _write_deps_toml(deps, """
[[modules]]
path = "real-stale.md (reserved)"
adr = "ADR-stale"

[[modules]]
path = "missing-reserved.py (reserved)"
adr = "ADR-accepted"

[[modules]]
path = "missing-drift.py"
adr = "ADR-drift"
""")
    rc = verifier.main([
        "--deps-toml", str(deps),
        "--repo-root", str(tmp_path),
        "--json",
    ])
    assert rc == 1  # drift entry forces exit 1
    captured = capsys.readouterr()
    import json
    payload = json.loads(captured.out)
    assert payload["total"] == 3
    assert payload["drift_count"] == 1
    assert payload["accepted_missing_count"] == 1
    assert payload["stale_marker_count"] == 1
    assert payload["drift"][0]["path"] == "missing-drift.py"
    assert payload["accepted_missing"][0]["path"] == "missing-reserved.py (reserved)"
    assert payload["stale_markers"][0]["path"] == "real-stale.md (reserved)"
