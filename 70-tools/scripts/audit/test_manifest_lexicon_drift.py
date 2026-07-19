"""Tests for manifest-lexicon-drift.py.

Locks in the structural invariants of the manifest-lexicon-drift
audit so future refactors don't silently break the NSID matching
or path mapping.

Iter-47 introduced the audit. Iters 48-52 closed the initial 21
findings across 5 actors. The category is currently at 0 findings.
These tests pin the audit's filter + mapping logic so it stays
useful as new actors author manifests.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "manifest-lexicon-drift.py"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("manifest_lexicon_drift", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["manifest_lexicon_drift"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── NSID regex invariants ─────────────────────────────────────────────


class TestNsidRegex:
    """The NSID matcher should accept AT-Protocol-compatible IDs."""

    def test_canonical_app_etzhayyim_three_segments(self, audit):
        # `com.etzhayyim.X.Y` — canonical form with camelCase last segment.
        assert audit.NSID_RE.match("com.etzhayyim.supply.supplierSelection") is not None
        assert audit.NSID_RE.match("com.etzhayyim.gov.permitApplication") is not None

    def test_lowercase_middle_segments(self, audit):
        # All-lowercase middle segments.
        assert audit.NSID_RE.match("com.etzhayyim.wadachi.deliveryRoute") is not None

    def test_camelcase_middle_segment(self, audit):
        # `kuniUmi` is camelCase in a middle segment — accepted because
        # the repo uses this convention. AT-Protocol strict spec would
        # reject; the audit is permissive for existence-check purposes.
        assert audit.NSID_RE.match("com.etzhayyim.kuniUmi.defineDeploymentSite") is not None

    def test_legacy_ai_etzhayyim_prefix(self, audit):
        # Legacy `com.etzhayyim.apps.etzhayyim.<actor>.X` form (pre-cutover).
        # Still matches as a valid NSID syntactically; the audit then
        # maps it to a path that — by convention — doesn't exist.
        assert audit.NSID_RE.match("com.etzhayyim.apps.etzhayyim.kuniUmi.submitSiteSurvey") is not None

    def test_rejects_too_few_segments(self, audit):
        # Need at least 3 dot-segments (a.b.c). One or two are invalid.
        assert audit.NSID_RE.match("app") is None
        assert audit.NSID_RE.match("com.etzhayyim") is None

    def test_rejects_starts_with_digit(self, audit):
        # Per AT-Protocol convention each segment starts with a letter.
        assert audit.NSID_RE.match("1bad.start.invalidNsid") is None

    def test_rejects_uppercase_first_char(self, audit):
        # Domain segments are reverse-domain, lowercase-first.
        assert audit.NSID_RE.match("App.etzhayyim.supply.foo") is None


# ─── NSID → file path mapping ──────────────────────────────────────────


class TestNsidToPath:
    """`a.b.c.d` should map to `lexicons/a/b/c/d.json`."""

    def test_canonical_three_segment(self, audit):
        path = audit.nsid_to_lexicon_path("com.etzhayyim.supply.supplierSelection")
        # Path ends with `.../com/etzhayyim/supply/supplierSelection.json`.
        suffix = "com/etzhayyim/supply/supplierSelection.json"
        assert str(path).endswith(suffix), f"{path} does not end with {suffix}"

    def test_camelcase_segment_preserved(self, audit):
        # `kuniUmi` must be preserved exactly (no lowercasing).
        path = audit.nsid_to_lexicon_path("com.etzhayyim.kuniUmi.defineDeploymentSite")
        suffix = "com/etzhayyim/kuniUmi/defineDeploymentSite.json"
        assert str(path).endswith(suffix), f"{path} does not end with {suffix}"

    def test_legacy_prefix_maps_to_legacy_path(self, audit):
        # Legacy NSIDs map to legacy paths under `com/etzhayyim/...`.
        path = audit.nsid_to_lexicon_path(
            "com.etzhayyim.apps.etzhayyim.yobel.declareRite"
        )
        suffix = "com/etzhayyim/apps/etzhayyim/yobel/declareRite.json"
        assert str(path).endswith(suffix), f"{path} does not end with {suffix}"

    def test_deep_namespace_path(self, audit):
        # 5-segment NSID → 4 dirs + 1 file.
        path = audit.nsid_to_lexicon_path("app.foo.bar.baz.qux")
        suffix = "app/foo/bar/baz/qux.json"
        assert str(path).endswith(suffix), f"{path} does not end with {suffix}"

    def test_flat_owner_contract_precedes_frozen_root(self, audit, tmp_path):
        manifest = tmp_path / "orgs/etzhayyim/com-etzhayyim-demo/manifest.edn"
        manifest.parent.mkdir(parents=True)
        local = audit.actor_lexicon_path(manifest, "com.etzhayyim.demo.record")
        local.parent.mkdir(parents=True)
        local.write_text("{}")
        assert audit.resolve_lexicon_path(manifest, "com.etzhayyim.demo.record") == local
        assert audit.lexicon_location(manifest, "com.etzhayyim.demo.record") == "owner-nsid-path"

    def test_missing_contract_is_classified(self, audit, tmp_path):
        manifest = tmp_path / "orgs/etzhayyim/com-etzhayyim-demo/manifest.edn"
        manifest.parent.mkdir(parents=True)
        assert audit.lexicon_location(manifest, "com.etzhayyim.noSuchOwner.record") == "missing"

    def test_wire_boundary_contract_is_flat_owner(self, audit, tmp_path):
        manifest = tmp_path / "orgs/etzhayyim/com-etzhayyim-demo/manifest.edn"
        manifest.parent.mkdir(parents=True)
        wire = audit.actor_wire_lexicon_path(manifest, "com.etzhayyim.demo.record")
        wire.parent.mkdir(parents=True)
        wire.write_text("{}")
        assert audit.resolve_lexicon_path(manifest, "com.etzhayyim.demo.record") == wire
        assert audit.lexicon_location(manifest, "com.etzhayyim.demo.record") == "owner-wire-lex"

    def test_plural_wire_lexicons_contract_is_flat_owner(self, audit, tmp_path):
        manifest = tmp_path / "orgs/etzhayyim/com-etzhayyim-demo/manifest.edn"
        manifest.parent.mkdir(parents=True)
        wire = audit.actor_wire_lexicons_path(manifest, "com.etzhayyim.demo.record")
        wire.parent.mkdir(parents=True)
        wire.write_text("{}")
        assert audit.resolve_lexicon_path(manifest, "com.etzhayyim.demo.record") == wire
        assert audit.lexicon_location(manifest, "com.etzhayyim.demo.record") == "owner-wire-lexicons"

    def test_contract_scoped_wire_lexicons_is_flat_owner(self, audit, tmp_path):
        manifest = tmp_path / "orgs/etzhayyim/com-etzhayyim-demo/manifest.edn"
        manifest.parent.mkdir(parents=True)
        wire = audit.actor_wire_contract_lexicons_path(
            manifest, "com.etzhayyim.demo.record"
        )
        wire.parent.mkdir(parents=True)
        wire.write_text("{}")
        assert audit.resolve_lexicon_path(manifest, "com.etzhayyim.demo.record") == wire
        assert audit.lexicon_location(manifest, "com.etzhayyim.demo.record") == (
            "owner-wire-contract-lexicons"
        )

    def test_qualified_plural_wire_lexicons_is_flat_owner(self, audit, tmp_path):
        manifest = tmp_path / "orgs/etzhayyim/com-etzhayyim-meisai/manifest.edn"
        manifest.parent.mkdir(parents=True)
        wire = audit.actor_wire_qualified_lexicons_path(
            manifest, "com.etzhayyim.meisai.statement"
        )
        wire.parent.mkdir(parents=True)
        wire.write_text("{}")
        assert wire.name == "meisai.statement.json"
        assert audit.resolve_lexicon_path(
            manifest, "com.etzhayyim.meisai.statement"
        ) == wire
        assert audit.lexicon_location(
            manifest, "com.etzhayyim.meisai.statement"
        ) == "owner-wire-qualified-lexicons"

    def test_qualified_filename_orphan_identity_comes_from_json(self, audit, tmp_path):
        wire = tmp_path / "meisai.statement.json"
        wire.write_text('{"lexicon": 1, "id": "com.etzhayyim.meisai.statement"}')
        assert audit.lexicon_file_nsid(wire, "com.etzhayyim.meisai") == (
            "com.etzhayyim.meisai.statement"
        )


# ─── End-to-end smoke tests against the live repo ──────────────────────


class TestEndToEnd:
    """Sanity-check against the actual `20-actors/` tree."""

    def test_finds_some_manifests(self, audit):
        manifests = audit.find_manifests()
        # The audit now discovers BOTH manifest.jsonld (legacy) and manifest.edn
        # (the jsonld→edn migration). As of 2026-06-25: 7 .jsonld + 143 .edn = 150
        # actors. The floor stays a generous sanity check (not a tight count).
        assert len(manifests) >= 10

    def test_post_closure_zero_drift(self, audit):
        # Iter-52 closed the last manifest-lexicon-drift finding. Re-running the
        # audit's internals — over BOTH .jsonld and .edn manifests, via the shared
        # declared_nsids() helper so this canary sees the migrated actors too —
        # should still return 0 drift.
        manifests = audit.find_manifests()
        missing_count = 0
        for mpath in manifests:
            try:
                declared = audit.declared_nsids(mpath)
            except Exception:
                continue
            for nsid in declared:
                if not isinstance(nsid, str):
                    continue
                if not audit.NSID_RE.match(nsid):
                    continue
                if not audit.nsid_to_lexicon_path(nsid).exists():
                    missing_count += 1
        # Iter-52 baseline: 0. Any non-zero indicates new drift.
        # This is the canary that catches regressions.
        assert missing_count == 0, (
            f"manifest-lexicon-drift category regressed: {missing_count} missing "
            f"lexicons (was 0 at iter-52 closure)"
        )


# ─── both-keys coverage + reverse-orphan detection (this commit) ────────


class TestBothKeysAndReverse:
    """The audit originally read only the legacy `lexicons` key, blind to the
    31 actors using `lexiconNamespaces`. It now reads both and also reports
    reverse-direction orphans (a lexicon file in an owned dir that no manifest
    declares — the iyashi/phlebotomyAttestation class of drift)."""

    @staticmethod
    def _run():
        import subprocess
        return subprocess.run(
            ["python3", str(_SCRIPT)], capture_output=True, text=True, check=False,
        )

    def test_reads_lexicon_namespaces_key(self):
        # Reading lexiconNamespaces (not just the legacy `lexicons` key) AND
        # the migrated manifest.edn corpus pushes the declared total well past
        # 100 (2026-06-25: ~193 across 150 actors). A regression to legacy-only
        # or jsonld-only would drop it far below this floor.
        out = self._run().stdout
        m = re.search(r"Lexicons declared \(total\):\s*(\d+)", out)
        assert m, f"missing declared-total line:\n{out}"
        assert int(m.group(1)) >= 100, (
            "audit appears to read only the legacy `lexicons` key; "
            "lexiconNamespaces-style manifests are invisible again"
        )

    def test_forward_rollup_is_zero_and_stable(self):
        out = self._run().stdout
        assert "missing as JSON file: 0" in out, (
            f"forward drift regressed (this would shift the aggregator baseline):\n{out}"
        )

    def test_reverse_orphan_detection_wired(self):
        out = self._run().stdout
        assert "Undeclared orphan lexicon files (tracked" in out, (
            f"reverse-orphan detection line missing:\n{out}"
        )

    def test_default_mode_exits_zero(self):
        # Orphans are tracked, not fatal (tracker mode) — default exit 0.
        assert self._run().returncode == 0

    def test_both_keys_no_forward_drift(self, audit):
        # Mirror of test_post_closure_zero_drift but reading BOTH keys — locks
        # that every lexiconNamespaces-declared lexicon also has a JSON file.
        import json
        missing = 0
        for mpath in audit.find_manifests():
            try:
                data = json.loads(mpath.read_text())
            except Exception:
                continue
            declared = []
            for key in ("lexicons", "lexiconNamespaces"):
                v = data.get(key, [])
                if not isinstance(v, list):
                    continue
                for item in v:
                    if isinstance(item, str):
                        declared.append(item)
                    elif isinstance(item, dict) and isinstance(item.get("id"), str):
                        declared.append(item["id"])
            for nsid in declared:
                if audit.NSID_RE.match(nsid):
                    if not audit.nsid_to_lexicon_path(nsid).exists():
                        missing += 1
        assert missing == 0, f"{missing} declared lexicon(s) (incl. lexiconNamespaces) have no JSON file"


# ─── minimal EDN reader robustness ─────────────────────────────────────


class TestEdnReader:
    """The dependency-free EDN reader replaced a regex that truncated arrays at
    the first `]` (inside nested `{id … "refs" [...]}` entries) and was blind to
    `;` comments / string escapes. Lock in the cases the regex got wrong."""

    def test_flat_string_array(self, audit):
        edn = '{:actor/manifest {"lexiconNamespaces" ["com.etzhayyim.a.foo" "com.etzhayyim.b.bar"]}}'
        assert audit.edn_lexicons(edn) == ["com.etzhayyim.a.foo", "com.etzhayyim.b.bar"]

    def test_canonical_top_level_actor_lexicons(self, audit):
        edn = ('{:actor/id "kosatsu" '
               ':actor/lexicons ["com.etzhayyim.kosatsu.query" '
               '"com.etzhayyim.kosatsu.result"]}')
        assert audit.edn_lexicons(edn) == [
            "com.etzhayyim.kosatsu.query",
            "com.etzhayyim.kosatsu.result",
        ]

    def test_keyword_legacy_and_namespaced_forms(self, audit):
        edn = ('{:lexicons ["com.etzhayyim.a.one"] '
               ':lexiconNamespaces ["com.etzhayyim.b.two"] '
               ':actor/lexiconNamespaces ["com.etzhayyim.c.three"]}')
        assert audit.edn_lexicons(edn) == [
            "com.etzhayyim.a.one",
            "com.etzhayyim.b.two",
            "com.etzhayyim.c.three",
        ]

    def test_rich_object_entry_uses_id(self, audit):
        # {id, status} entry → only the id is a lexicon; status is ignored.
        edn = '{"lexicons" [{"id" "com.etzhayyim.c.baz" "status" "active"}]}'
        assert audit.edn_lexicons(edn) == ["com.etzhayyim.c.baz"]

    def test_nested_brackets_not_truncated(self, audit):
        # The regex stopped at the first `]` here, dropping `d.two`.
        edn = ('{"lexiconNamespaces" '
               '[{"id" "com.etzhayyim.d.one" "refs" ["x" "y"]} "com.etzhayyim.d.two"]}')
        assert audit.edn_lexicons(edn) == ["com.etzhayyim.d.one", "com.etzhayyim.d.two"]

    def test_ignores_comments_and_other_keys(self, audit):
        edn = ('{:actor/manifest\n'
               '  {"name" "x"  ; a comment with ] and "quotes"\n'
               '   "lexiconNamespaces" ["com.etzhayyim.e.foo"]\n'
               '   "other" ["not.a.lexicon.but.dotted"]}}')
        assert audit.edn_lexicons(edn) == ["com.etzhayyim.e.foo"]

    def test_no_lexicons_is_empty(self, audit):
        assert audit.edn_lexicons('{:actor/id "x" :actor/glyph "兜"}') == []

    def test_root_owned_registry_is_edn_canonical(self, audit, tmp_path):
        registry = tmp_path / "root-owned.edn"
        registry.write_text(
            '{:registry/lexicons ["com.etzhayyim.apps.etzhayyim.'
            'priorityConformanceAttestation"]}'
        )
        assert audit.root_owned_nsids(registry) == {
            "com.etzhayyim.apps.etzhayyim.priorityConformanceAttestation"
        }
