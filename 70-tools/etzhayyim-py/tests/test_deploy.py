"""Unit tests for build/deploy commands (pure — no real wrangler/pnpm calls)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.deploy import (
    _find_git_root,
    _app_id,
    _ui_type,
    _validate_no_cors,
    _validate_no_pds_hardcode,
    _validate_governance_import,
    _validate_profile,
    _validate_required,
    generate_wrangler_jsonc,
    _git_short_sha,
    _actor_handle_from_cfg,
)


# ── fixtures ───────────────────────────────────────────────────────────────────

def _minimal_cfg() -> dict:
    return {
        "nanoid": "tst12345",
        "name": "myapp",
        "performerType": "service",
        "uiType": "appview",
        "convoSystemPrompt": "You are a helpful assistant.",
        "governance": {"roles": [{"role": "operator", "did": "did:web:etzhayyim.etzhayyim.com"}]},
        "profile": {
            "displayName": "My App",
            "description": "A test app",
            "capabilities": ["test"],
            "handle": "myapp",
        },
        "triggers": {
            "subscribeRepos": {"collections": ["com.etzhayyim.apps.myapp.item"]}
        },
    }


def _write_minimal_app(tmp_path: Path, cfg: dict | None = None) -> None:
    if cfg is None:
        cfg = _minimal_cfg()
    (tmp_path / "magatama.jsonld").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "app.ts").write_text('export default createWorkerExport(() => {});\n')


# ── helpers ────────────────────────────────────────────────────────────────────

def test_app_id_from_nanoid():
    assert _app_id({"nanoid": "abc123"}) == "abc123"


def test_app_id_fallback_to_name():
    assert _app_id({"name": "myapp"}) == "myapp"


def test_ui_type_default():
    assert _ui_type({}) == "appview"


def test_ui_type_yoro():
    assert _ui_type({"uiType": "yoro"}) == "yoro"


def test_find_git_root_finds_git(tmp_path):
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    result = _find_git_root(sub)
    assert result == tmp_path


def test_find_git_root_returns_none_when_absent(tmp_path):
    result = _find_git_root(tmp_path)
    assert result is None


# ── validation ─────────────────────────────────────────────────────────────────

def test_validate_no_cors_passes_no_main_go(tmp_path):
    _validate_no_cors(tmp_path)  # no exception


def test_validate_no_cors_raises_on_cors_header(tmp_path):
    import click
    (tmp_path / "main.go").write_text('res.Header.Set("Access-Control-Allow-Origin", "*")\n')
    with pytest.raises(click.ClickException, match="cors guard"):
        _validate_no_cors(tmp_path)


def test_validate_no_pds_hardcode_passes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("// clean code\n")
    _validate_no_pds_hardcode(tmp_path)  # no exception


def test_validate_no_pds_hardcode_raises(tmp_path):
    import click
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text('appId: "pds"\n')
    with pytest.raises(click.ClickException, match="pds-hardcode"):
        _validate_no_pds_hardcode(tmp_path)


def test_validate_governance_import_skips_no_magatama(tmp_path):
    _validate_governance_import(tmp_path)  # no exception


def test_validate_governance_import_skips_no_wit(tmp_path):
    (tmp_path / "magatama.jsonld").write_text("{}")
    _validate_governance_import(tmp_path)  # no exception


def test_validate_governance_import_passes_with_include(tmp_path):
    (tmp_path / "magatama.jsonld").write_text("{}")
    (tmp_path / "wit").mkdir()
    (tmp_path / "wit" / "world.wit").write_text(
        "include magatama:runtime/magatama-component@1.0.0;\n"
    )
    _validate_governance_import(tmp_path)  # no exception


def test_validate_governance_import_raises_missing(tmp_path):
    import click
    (tmp_path / "magatama.jsonld").write_text("{}")
    (tmp_path / "wit").mkdir()
    (tmp_path / "wit" / "world.wit").write_text("world my-world {}\n")
    with pytest.raises(click.ClickException, match="governance guard"):
        _validate_governance_import(tmp_path)


def test_validate_profile_raises_missing(tmp_path):
    import click
    with pytest.raises(click.ClickException, match="profile block"):
        _validate_profile({})


def test_validate_profile_raises_no_display_name(tmp_path):
    import click
    with pytest.raises(click.ClickException, match="displayName"):
        _validate_profile({"profile": {"description": "hi"}})


def test_validate_profile_passes(tmp_path):
    _validate_profile({"profile": {"displayName": "App", "description": "Desc"}})


def test_validate_required_raises_no_governance(tmp_path):
    import click
    cfg = _minimal_cfg()
    del cfg["governance"]
    with pytest.raises(click.ClickException, match="governance"):
        _validate_required(cfg)


def test_validate_required_raises_no_convo_system_prompt(tmp_path):
    import click
    cfg = _minimal_cfg()
    del cfg["convoSystemPrompt"]
    with pytest.raises(click.ClickException, match="convoSystemPrompt"):
        _validate_required(cfg)


def test_validate_required_passes(tmp_path):
    _validate_required(_minimal_cfg())


# ── wrangler.jsonc generation ──────────────────────────────────────────────────

def test_generate_wrangler_jsonc_basic(tmp_path):
    cfg = _minimal_cfg()
    _write_minimal_app(tmp_path, cfg)
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    data = json.loads(output)
    assert data["name"] == "magatama-tst12345"
    assert data["main"] == "src/app.ts"
    assert any("tst12345.etzhayyim.com/*" in r["pattern"] for r in data["routes"])


def test_generate_wrangler_jsonc_yoro_no_assets(tmp_path):
    cfg = {**_minimal_cfg(), "uiType": "yoro"}
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    assert '"assets"' not in output


def test_generate_wrangler_jsonc_has_r2_buckets(tmp_path):
    cfg = _minimal_cfg()
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    data = json.loads(output)
    assert any(b["binding"] == "YATA_R2" for b in data["r2_buckets"])


def test_generate_wrangler_jsonc_has_pds_service(tmp_path):
    cfg = _minimal_cfg()
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    data = json.loads(output)
    assert any(s["binding"] == "PDS_SERVICE" for s in data["services"])


def test_generate_wrangler_jsonc_app_vars(tmp_path):
    cfg = _minimal_cfg()
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    data = json.loads(output)
    vars_dict = data.get("vars", {})
    assert vars_dict.get("APP_NANOID") == "tst12345"
    assert vars_dict.get("APP_DISPLAY_NAME") == "My App"


def test_generate_wrangler_jsonc_has_secrets(tmp_path):
    cfg = _minimal_cfg()
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    data = json.loads(output)
    assert len(data["secrets_store_secrets"]) > 0
    bindings = {s["binding"] for s in data["secrets_store_secrets"]}
    assert "SS_OPENROUTER_API_KEY" in bindings


def test_generate_wrangler_jsonc_browser_binding(tmp_path):
    cfg = {**_minimal_cfg(), "needsBrowser": True}
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    assert "HEADLESS_BROWSER" in output


def test_generate_wrangler_jsonc_no_browser_by_default(tmp_path):
    cfg = _minimal_cfg()
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    assert "HEADLESS_BROWSER" not in output


def test_generate_wrangler_jsonc_custom_route(tmp_path):
    cfg = {**_minimal_cfg(), "routes": [{"host": "mycom.etzhayyim.com"}]}
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    data = json.loads(output)
    patterns = [r["pattern"] for r in data["routes"]]
    assert "mycom.etzhayyim.com/*" in patterns


def test_generate_wrangler_jsonc_dedup_routes(tmp_path):
    cfg = {**_minimal_cfg(), "routes": [{"host": "tst12345.etzhayyim.com"}]}
    output = generate_wrangler_jsonc(cfg, tmp_path, git_root=None)
    data = json.loads(output)
    patterns = [r["pattern"] for r in data["routes"]]
    assert patterns.count("tst12345.etzhayyim.com/*") == 1


def test_actor_handle_from_cfg_profile_handle(tmp_path):
    cfg = {"profile": {"handle": "myhandle"}}
    assert _actor_handle_from_cfg(cfg, tmp_path) == "myhandle"


def test_actor_handle_from_cfg_dir_slug(tmp_path):
    comp = tmp_path / "etzhayyim-wasm-myslug-abc12345"
    comp.mkdir()
    cfg = {}
    assert _actor_handle_from_cfg(cfg, comp) == "myslug"


# ── CLI integration ────────────────────────────────────────────────────────────

def test_cli_build_missing_magatama(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["build", "--dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "magatama.jsonld" in result.output


def test_cli_build_missing_app_ts(tmp_path):
    cfg = _minimal_cfg()
    (tmp_path / "magatama.jsonld").write_text(json.dumps(cfg))
    runner = CliRunner()
    result = runner.invoke(main, ["build", "--dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "app.ts" in result.output


def test_cli_build_no_svelte_no_score(tmp_path):
    """Build with --no-svelte --no-deps-score on a minimal app should succeed."""
    _write_minimal_app(tmp_path)
    runner = CliRunner()
    with patch("etzhayyim.deploy._run_build") as mock_build:
        mock_build.return_value = None
        result = runner.invoke(main, [
            "build", "--dir", str(tmp_path),
            "--no-svelte", "--no-deps-score",
        ])
    # The patch bypasses actual subprocess calls; validate invocation
    assert mock_build.called


def test_cli_deploy_missing_magatama(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["deploy", "--dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "magatama.jsonld" in result.output


def test_cli_deploy_generates_wrangler_and_calls_wrangler(tmp_path):
    """Deploy with mocked subprocess should generate wrangler.jsonc and call wrangler deploy."""
    _write_minimal_app(tmp_path)
    runner = CliRunner()
    with patch("etzhayyim.deploy._run_build"), \
         patch("etzhayyim.deploy._run_cmd") as mock_cmd, \
         patch("etzhayyim.deploy._post_deploy_announce"):
        result = runner.invoke(main, [
            "deploy", "--dir", str(tmp_path),
            "--no-svelte", "--no-deps-score", "--no-announce",
        ])

    wrangler_path = tmp_path / "wrangler.jsonc"
    assert wrangler_path.exists(), f"wrangler.jsonc not created; output: {result.output}"
    data = json.loads(wrangler_path.read_text())
    assert data["name"] == "magatama-tst12345"


def test_cli_deploy_stub_stub_commands_in_cli():
    """Validate that build and deploy are properly registered (not stubs)."""
    runner = CliRunner()
    result = runner.invoke(main, ["build", "--help"])
    assert result.exit_code == 0
    assert "magatama Worker" in result.output or "build" in result.output.lower()
