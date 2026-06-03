"""Unit tests for etzhayyim.dns_sync — ADR-0013 Phase 3 DNS sync.

No real Cloudflare API calls are made. All CF API interactions are mocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from etzhayyim.dns_sync import (
    _IdActor,
    _IdLegacy,
    _parse_identifier_tables,
    _build_desired_records,
    _diff_records,
    _emit_routing_map_ts,
    _emit_yoro_mirror_ts,
    _find_services_range,
    _patch_wrangler_bindings,
    dns_sync,
)
from etzhayyim.cli import main


# ─── _parse_identifier_tables ────────────────────────────────────────────────

class TestParseIdentifierTables:
    def _write_deps(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "deps.toml"
        p.write_text(content)
        return p

    def test_empty_file(self, tmp_path):
        p = self._write_deps(tmp_path, "")
        actors, legacies = _parse_identifier_tables(p)
        assert actors == []
        assert legacies == []

    def test_parses_mitama_actors(self, tmp_path):
        p = self._write_deps(tmp_path, """
[[mitama_actors]]
name = "adr"
domain = "adr.etzhayyim.com"
did = "did:web:adr.etzhayyim.com"
nanoid = "abc123"
""")
        actors, _ = _parse_identifier_tables(p)
        assert len(actors) == 1
        assert actors[0].name == "adr"
        assert actors[0].domain == "adr.etzhayyim.com"
        assert actors[0].did == "did:web:adr.etzhayyim.com"
        assert actors[0].nanoid == "abc123"

    def test_parses_handles_array(self, tmp_path):
        p = self._write_deps(tmp_path, """
[[mitama_actors]]
name = "multi"
handles = ["a.etzhayyim.com", "b.etzhayyim.com"]
""")
        actors, _ = _parse_identifier_tables(p)
        assert actors[0].handles == ["a.etzhayyim.com", "b.etzhayyim.com"]

    def test_parses_legacy_nanoids(self, tmp_path):
        p = self._write_deps(tmp_path, """
[[legacy_nanoids]]
actor = "adr"
nanoid = "xyzlegacy"
handle = "adr.etzhayyim.com"
""")
        _, legacies = _parse_identifier_tables(p)
        assert len(legacies) == 1
        assert legacies[0].actor == "adr"
        assert legacies[0].nanoid == "xyzlegacy"
        assert legacies[0].handle == "adr.etzhayyim.com"

    def test_multiple_actors(self, tmp_path):
        p = self._write_deps(tmp_path, """
[[mitama_actors]]
name = "alpha"
domain = "alpha.etzhayyim.com"

[[mitama_actors]]
name = "beta"
domain = "beta.etzhayyim.com"
""")
        actors, _ = _parse_identifier_tables(p)
        assert len(actors) == 2
        assert {a.name for a in actors} == {"alpha", "beta"}

    def test_missing_file(self, tmp_path):
        actors, legacies = _parse_identifier_tables(tmp_path / "missing.toml")
        assert actors == []
        assert legacies == []

    def test_actor_without_name_skipped(self, tmp_path):
        p = self._write_deps(tmp_path, """
[[mitama_actors]]
domain = "noname.etzhayyim.com"
""")
        actors, _ = _parse_identifier_tables(p)
        assert actors == []


# ─── _build_desired_records ───────────────────────────────────────────────────

class TestBuildDesiredRecords:
    def _actor(self, name="test", domain="test.etzhayyim.com", did="did:web:test.etzhayyim.com") -> _IdActor:
        return _IdActor(name=name, domain=domain, did=did, nanoid="", handles=[])

    def _legacy(self, actor="test", nanoid="legacynanoid", handle="test.etzhayyim.com") -> _IdLegacy:
        return _IdLegacy(actor=actor, nanoid=nanoid, handle=handle)

    def test_empty(self):
        recs = _build_desired_records([], [], True, True, "etzhayyim.com")
        assert recs == []

    def test_txt_record_created(self):
        actors = [self._actor()]
        recs = _build_desired_records(actors, [], True, False, "etzhayyim.com")
        assert len(recs) == 1
        assert recs[0]["type"] == "TXT"
        assert recs[0]["name"] == "_atproto.test.etzhayyim.com"
        assert recs[0]["content"] == '"did=did:web:test.etzhayyim.com"'

    def test_txt_skipped_when_include_txt_false(self):
        actors = [self._actor()]
        recs = _build_desired_records(actors, [], False, False, "etzhayyim.com")
        assert recs == []

    def test_txt_skipped_when_no_did(self):
        actor = _IdActor(name="nodid", domain="nodid.etzhayyim.com", did="", nanoid="", handles=[])
        recs = _build_desired_records([actor], [], True, False, "etzhayyim.com")
        assert recs == []

    def test_cname_record_created(self):
        legacies = [self._legacy()]
        recs = _build_desired_records([], legacies, False, True, "etzhayyim.com")
        assert len(recs) == 1
        assert recs[0]["type"] == "CNAME"
        assert recs[0]["name"] == "legacynanoid.etzhayyim.com"
        assert recs[0]["content"] == "test.etzhayyim.com"
        assert recs[0]["proxied"] is True

    def test_cname_skipped_when_include_nanoid_false(self):
        legacies = [self._legacy()]
        recs = _build_desired_records([], legacies, False, False, "etzhayyim.com")
        assert recs == []

    def test_cross_zone_actor_excluded(self):
        actor = _IdActor(name="ext", domain="ext.example.com", did="did:web:ext.example.com", nanoid="", handles=[])
        recs = _build_desired_records([actor], [], True, False, "etzhayyim.com")
        assert recs == []

    def test_handles_fallback_used(self):
        actor = _IdActor(name="h", domain="", did="did:web:h.etzhayyim.com", nanoid="", handles=["h.etzhayyim.com"])
        recs = _build_desired_records([actor], [], True, False, "etzhayyim.com")
        assert len(recs) == 1
        assert recs[0]["name"] == "_atproto.h.etzhayyim.com"

    def test_records_sorted(self):
        actors = [
            _IdActor(name="z", domain="z.etzhayyim.com", did="did:web:z.etzhayyim.com", nanoid="", handles=[]),
            _IdActor(name="a", domain="a.etzhayyim.com", did="did:web:a.etzhayyim.com", nanoid="", handles=[]),
        ]
        recs = _build_desired_records(actors, [], True, False, "etzhayyim.com")
        assert recs[0]["name"] < recs[1]["name"]

    def test_comment_prefix_set(self):
        actors = [self._actor()]
        recs = _build_desired_records(actors, [], True, False, "etzhayyim.com")
        assert recs[0]["comment"].startswith("etzhayyim:adr-0013:")


# ─── _diff_records ────────────────────────────────────────────────────────────

class TestDiffRecords:
    def _rec(self, name: str, rtype: str, content: str, comment: str = "etzhayyim:adr-0013:atproto-verify", rid: str = "") -> dict:
        r: dict = {"name": name, "type": rtype, "content": content, "comment": comment}
        if rid:
            r["id"] = rid
        return r

    def test_empty_both(self):
        plan = _diff_records([], [])
        assert plan == []

    def test_create_when_no_existing(self):
        desired = [self._rec("_atproto.x.etzhayyim.com", "TXT", '"did=did:web:x.etzhayyim.com"')]
        plan = _diff_records(desired, [])
        assert len(plan) == 1
        assert plan[0]["action"] == "create"

    def test_keep_when_identical(self):
        desired = [self._rec("_atproto.x.etzhayyim.com", "TXT", '"did=did:web:x.etzhayyim.com"')]
        existing = [self._rec("_atproto.x.etzhayyim.com", "TXT", '"did=did:web:x.etzhayyim.com"', rid="rec123")]
        plan = _diff_records(desired, existing)
        assert plan[0]["action"] == "keep"

    def test_update_when_content_differs(self):
        desired = [self._rec("_atproto.x.etzhayyim.com", "TXT", '"did=did:plc:new"')]
        existing = [self._rec("_atproto.x.etzhayyim.com", "TXT", '"did=did:web:old"', rid="rec123")]
        plan = _diff_records(desired, existing)
        assert plan[0]["action"] == "update"
        assert "new" in plan[0]["reason"]

    def test_delete_orphan(self):
        desired: list[dict] = []
        existing = [self._rec("_atproto.gone.etzhayyim.com", "TXT", '"did=did:web:gone.etzhayyim.com"', rid="old")]
        plan = _diff_records(desired, existing)
        assert plan[0]["action"] == "delete"
        assert "orphan" in plan[0]["reason"]

    def test_mixed_plan(self):
        desired = [
            self._rec("_atproto.a.etzhayyim.com", "TXT", '"did=did:web:a.etzhayyim.com"'),
            self._rec("_atproto.b.etzhayyim.com", "TXT", '"did=did:web:b.etzhayyim.com"'),
        ]
        existing = [
            self._rec("_atproto.a.etzhayyim.com", "TXT", '"did=did:web:a.etzhayyim.com"', rid="r1"),  # keep
            self._rec("_atproto.c.etzhayyim.com", "TXT", '"did=did:web:c.etzhayyim.com"', rid="r2"),  # delete
        ]
        plan = _diff_records(desired, existing)
        actions = {p["action"] for p in plan}
        assert "keep" in actions
        assert "create" in actions
        assert "delete" in actions


# ─── _emit_routing_map_ts ─────────────────────────────────────────────────────

class TestEmitRoutingMapTs:
    def test_empty_legacies(self):
        ts = _emit_routing_map_ts([])
        assert "LEGACY_NANOID_MAP" in ts
        assert "PHASE4_DEPRECATE_AT" in ts
        assert "DO NOT EDIT BY HAND" in ts

    def test_sorted_by_nanoid(self):
        legacies = [
            _IdLegacy(actor="z", nanoid="zzz", handle="z.etzhayyim.com"),
            _IdLegacy(actor="a", nanoid="aaa", handle="a.etzhayyim.com"),
        ]
        ts = _emit_routing_map_ts(legacies)
        aaa_pos = ts.index('"aaa"')
        zzz_pos = ts.index('"zzz"')
        assert aaa_pos < zzz_pos

    def test_entry_format(self):
        legacies = [_IdLegacy(actor="x", nanoid="mynanoid", handle="x.etzhayyim.com")]
        ts = _emit_routing_map_ts(legacies)
        assert '"mynanoid": "x.etzhayyim.com",' in ts

    def test_phase4_date(self):
        ts = _emit_routing_map_ts([])
        assert "2026-10-01" in ts


# ─── _emit_yoro_mirror_ts ─────────────────────────────────────────────────────

class TestEmitYoroMirrorTs:
    def test_has_resolve_function(self):
        ts = _emit_yoro_mirror_ts([])
        assert "resolveLegacyHandle" in ts
        assert "LEGACY_NANOID_MAP" in ts

    def test_sorted_by_nanoid(self):
        legacies = [
            _IdLegacy(actor="z", nanoid="zzz", handle="z.etzhayyim.com"),
            _IdLegacy(actor="a", nanoid="aaa", handle="a.etzhayyim.com"),
        ]
        ts = _emit_yoro_mirror_ts(legacies)
        assert ts.index('"aaa"') < ts.index('"zzz"')

    def test_mirror_comment(self):
        ts = _emit_yoro_mirror_ts([])
        assert "MIRROR OF" in ts


# ─── _find_services_range / _patch_wrangler_bindings ─────────────────────────

class TestFindServicesRange:
    def test_no_services(self):
        assert _find_services_range('{"name": "test"}') is None

    def test_simple_services(self):
        src = '{ "services": [{"binding": "FOO", "service": "bar"}] }'
        rng = _find_services_range(src)
        assert rng is not None
        start, end = rng
        assert src[start:end].startswith('"services"')
        assert src[end - 1] == "]"

    def test_nested_brackets(self):
        src = '{ "services": [{"a": [1,2]}, {"b": 3}] }'
        rng = _find_services_range(src)
        assert rng is not None
        _, end = rng
        assert src[end - 1] == "]"


class TestPatchWranglerBindings:
    def _minimal_jsonc(self) -> str:
        return '{\n  "name": "routing-gateway",\n  "services": []\n}'

    def test_replaces_services(self, tmp_path):
        p = tmp_path / "wrangler.jsonc"
        p.write_text(self._minimal_jsonc())
        actors = [_IdActor(name="adr", domain="adr.etzhayyim.com", nanoid="", did="", handles=[])]
        patched, count = _patch_wrangler_bindings(p, actors)
        assert "PDS_WORKER" in patched
        assert "PLC_DIRECTORY" in patched
        assert "WORKER_ADR" in patched
        assert count == 3

    def test_count_includes_fixed_entries(self, tmp_path):
        p = tmp_path / "wrangler.jsonc"
        p.write_text(self._minimal_jsonc())
        actors: list[_IdActor] = []
        _, count = _patch_wrangler_bindings(p, actors)
        assert count == 2  # PDS_WORKER + PLC_DIRECTORY only

    def test_actors_sorted_alphabetically(self, tmp_path):
        p = tmp_path / "wrangler.jsonc"
        p.write_text(self._minimal_jsonc())
        actors = [
            _IdActor(name="zzz", domain="zzz.etzhayyim.com", nanoid="", did="", handles=[]),
            _IdActor(name="aaa", domain="aaa.etzhayyim.com", nanoid="", did="", handles=[]),
        ]
        patched, _ = _patch_wrangler_bindings(p, actors)
        assert patched.index("WORKER_AAA") < patched.index("WORKER_ZZZ")

    def test_hyphen_converted_to_underscore(self, tmp_path):
        p = tmp_path / "wrangler.jsonc"
        p.write_text(self._minimal_jsonc())
        actors = [_IdActor(name="my-actor", domain="my-actor.etzhayyim.com", nanoid="", did="", handles=[])]
        patched, _ = _patch_wrangler_bindings(p, actors)
        assert "WORKER_MY_ACTOR" in patched

    def test_inserts_when_no_services_key(self, tmp_path):
        p = tmp_path / "wrangler.jsonc"
        p.write_text('{\n  "name": "test"\n}')
        actors: list[_IdActor] = []
        patched, count = _patch_wrangler_bindings(p, actors)
        assert "PDS_WORKER" in patched
        assert count == 2


# ─── CLI integration tests ────────────────────────────────────────────────────

class TestDnsSyncCLI:
    def _write_deps(self, tmp_path: Path) -> None:
        (tmp_path / "deps.toml").write_text("""
[[mitama_actors]]
name = "adr"
domain = "adr.etzhayyim.com"
did = "did:web:adr.etzhayyim.com"
nanoid = "adr1"

[[legacy_nanoids]]
actor = "adr"
nanoid = "adr1"
handle = "adr.etzhayyim.com"
""")

    def test_help(self):
        result = CliRunner().invoke(main, ["dns-sync", "--help"])
        assert result.exit_code == 0

    def test_no_cf_offline_text(self, tmp_path):
        self._write_deps(tmp_path)
        result = CliRunner().invoke(main, ["dns-sync", "--no-cf", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "offline" in result.output
        assert "_atproto" in result.output

    def test_no_cf_offline_json(self, tmp_path):
        self._write_deps(tmp_path)
        result = CliRunner().invoke(main, ["dns-sync", "--no-cf", "--json", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["mode"] == "offline"
        assert data["desired_count"] > 0

    def test_no_cf_with_no_include_nanoid(self, tmp_path):
        self._write_deps(tmp_path)
        result = CliRunner().invoke(main, [
            "dns-sync", "--no-cf", "--no-include-nanoid", "--json",
            "--workspace-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        for rec in data["desired"]:
            assert rec["type"] != "CNAME"

    def test_no_cf_with_no_include_txt(self, tmp_path):
        self._write_deps(tmp_path)
        result = CliRunner().invoke(main, [
            "dns-sync", "--no-cf", "--no-include-txt", "--json",
            "--workspace-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        for rec in data["desired"]:
            assert rec["type"] != "TXT"

    def test_emit_routing_map(self, tmp_path):
        self._write_deps(tmp_path)
        out = tmp_path / "legacy-nanoid-map.ts"
        result = CliRunner().invoke(main, [
            "dns-sync",
            f"--emit-routing-map={out}",
            "--no-yoro-mirror",
            "--workspace-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert "LEGACY_NANOID_MAP" in content
        assert "adr1" in content

    def test_emit_routing_map_with_yoro_mirror(self, tmp_path):
        self._write_deps(tmp_path)
        out = tmp_path / "map.ts"
        yoro = tmp_path / "yoro-map.ts"
        result = CliRunner().invoke(main, [
            "dns-sync",
            f"--emit-routing-map={out}",
            f"--yoro-mirror-path={yoro}",
            "--workspace-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert yoro.exists()
        assert "resolveLegacyHandle" in yoro.read_text()

    def test_populate_bindings(self, tmp_path):
        self._write_deps(tmp_path)
        wrangler = tmp_path / "wrangler.jsonc"
        wrangler.write_text('{\n  "name": "routing",\n  "services": []\n}')
        result = CliRunner().invoke(main, [
            "dns-sync",
            f"--populate-bindings={wrangler}",
            "--workspace-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "WORKER_ADR" in wrangler.read_text()

    def test_no_token_fails(self, tmp_path):
        self._write_deps(tmp_path)
        with patch("etzhayyim.dns_sync._resolve_cf_token", return_value=("", "")):
            result = CliRunner().invoke(main, ["dns-sync", "--workspace-dir", str(tmp_path)])
        assert result.exit_code != 0

    def test_with_cf_token_dry_run(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "test-token")
        self._write_deps(tmp_path)

        mock_zone_resp = MagicMock()
        mock_zone_resp.raise_for_status.return_value = None
        mock_zone_resp.json.return_value = {
            "success": True,
            "result": [{"id": "zone123", "name": "etzhayyim.com"}],
        }
        mock_list_resp = MagicMock()
        mock_list_resp.raise_for_status.return_value = None
        mock_list_resp.json.return_value = {
            "success": True,
            "result": [],
            "result_info": {"page": 1, "total_pages": 1},
        }

        with patch("httpx.get", side_effect=[mock_zone_resp, mock_list_resp]):
            result = CliRunner().invoke(main, ["dns-sync", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "dry-run" in result.output

    def test_with_cf_token_apply(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "test-token")
        self._write_deps(tmp_path)

        mock_zone_resp = MagicMock()
        mock_zone_resp.raise_for_status.return_value = None
        mock_zone_resp.json.return_value = {
            "success": True,
            "result": [{"id": "zone123", "name": "etzhayyim.com"}],
        }
        mock_list_resp = MagicMock()
        mock_list_resp.raise_for_status.return_value = None
        mock_list_resp.json.return_value = {
            "success": True,
            "result": [],
            "result_info": {"page": 1, "total_pages": 1},
        }
        mock_create_resp = MagicMock()
        mock_create_resp.status_code = 200

        with (
            patch("httpx.get", side_effect=[mock_zone_resp, mock_list_resp]),
            patch("httpx.post", return_value=mock_create_resp),
        ):
            result = CliRunner().invoke(main, ["dns-sync", "--apply", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "applied=" in result.output
