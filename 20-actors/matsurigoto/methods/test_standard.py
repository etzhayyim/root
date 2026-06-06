#!/usr/bin/env python3
"""Tests for the COFOG-based e-gov service standard (matsurigoto 政, ADR-2606052300).

Standalone-runnable (`python3 test_standard.py`) AND pytest-compatible
(`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest`), mirroring the other actors' test style.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import standard as S  # noqa: E402

DOC = S.load_standard()


def test_standard_loads_as_map():
    assert isinstance(DOC, dict)
    assert DOC[":standard"][":standard/id"] == "egov-cofog-standard"


def test_cofog_backbone_has_10_divisions():
    divs = [r for r in DOC[":cofog"] if r.get(":cofog/level") == ":division"]
    assert len(divs) == 10
    codes = {d[":cofog/code"] for d in divs}
    assert codes == {f"{i:02d}" for i in range(1, 11)}


def test_cofog_groups_reference_existing_division():
    codes = {r[":cofog/code"] for r in DOC[":cofog"]}
    for r in DOC[":cofog"]:
        if r.get(":cofog/level") == ":group":
            assert r[":cofog/parent"] in codes, r[":cofog/code"]


def test_validate_passes_clean():
    errors = S.validate(DOC)
    assert errors == [], errors


def test_every_service_maps_to_valid_cofog_class():
    cofog = S.cofog_index(DOC)
    for s in DOC[":services"]:
        assert s[":egov.service/cofog"] in cofog, s[":egov.service/id"]


def test_every_service_has_known_module():
    mods = S.module_index(DOC)
    for s in DOC[":services"]:
        assert s[":egov.service/module"] in mods, s[":egov.service/id"]


def test_every_service_is_spec_derived_g2():
    """G2: spec-derived-only — non-empty official spec basis on every service."""
    for s in DOC[":services"]:
        specs = s.get(":egov.service/spec-basis") or []
        assert len(specs) >= 1, s[":egov.service/id"]


def test_every_service_carries_the_universal_invariants():
    """G1 no-operator-master-key + G2 spec-derived, structurally on every service."""
    for s in DOC[":services"]:
        inv = s[":egov.service/invariants"]
        assert inv[":server-held-authority"] is False, s[":egov.service/id"]   # G1
        assert inv[":spec-derived"] is True, s[":egov.service/id"]             # G2


def test_etzhayyim_is_a_government_polity_profile_present():
    """The correction: etzhayyim IS a government (Kingdom of God) with a 統治機構.

    The polity profile must exist, be governed by the Council in sovereign mode, and bind
    COFOG functions onto etzhayyim's OWN constitutional organs.
    """
    polities = DOC[":polity-profiles"]
    et = next(p for p in polities if p[":polity-profile/id"] == "etzhayyim")
    assert et[":polity-profile/operated-by"] == ":etzhayyim-council"
    assert et[":polity-profile/authority-mode"] == ":sovereign-governance"
    service_ids = {s[":egov.service/id"] for s in DOC[":services"]}
    for b in et[":polity-profile/bindings"]:
        assert b[":bind/service"] in service_ids, b[":bind/service"]
        assert b[":bind/organ"]        # a real etzhayyim constitutional organ
        assert b[":bind/legal-basis"]  # Charter / ADR basis
        assert b[":bind/spec"]


def test_both_principals_declared():
    principals = {p[":principal/id"] for p in DOC[":standard"][":standard/principals"]}
    assert principals == {":etzhayyim-sovereign", ":nation-state-adopter"}


def test_authority_is_borne_not_disclaimed():
    """G3: every profile names a legitimate authority — the Kingdom via Council, a state via itself.

    No deployment may run with an operator master key (that is what :server-held-authority false
    forbids); but governance IS exercised — authority is never 'none'.
    """
    for p in DOC[":polity-profiles"]:
        assert p[":polity-profile/operated-by"] in S.ALLOWED_OPERATED_BY
        assert p[":polity-profile/authority-mode"] in S.ALLOWED_AUTHORITY_MODE
    for p in DOC[":country-profiles"]:
        assert p[":country-profile/operated-by"] in S.ALLOWED_OPERATED_BY
        assert p[":country-profile/authority-mode"] in S.ALLOWED_AUTHORITY_MODE


def test_named_domains_all_covered():
    domains = {s[":egov.service/domain"] for s in DOC[":services"]}
    for required in S.REQUIRED_DOMAINS:
        assert required in domains, f"missing named domain {required}"


VALID_MATURITY = {":standard-draft", ":planned", ":reference-impl"}


def test_no_service_is_live_executable_at_r0():
    """Honest R0: a service is at most :reference-impl (runs in conformance tests, NOT wired to
    a live government record). :executable (live) requires Council+operator gating."""
    for s in DOC[":services"]:
        assert s[":egov.service/maturity"] in VALID_MATURITY, s[":egov.service/id"]
        assert s[":egov.service/maturity"] != ":executable", s[":egov.service/id"]


def test_tax_assess_reference_impl_is_wired_and_correct():
    """The first executable vertical slice: tax-assess reproduces the JP 速算表 exactly,
    and the three tax services it backs are marked :reference-impl."""
    sys.path.insert(0, str(HERE / "modules"))
    import tax_assess as T
    assert T.assess_income_tax(5_000_000, T.RATE_TABLES["JPN.income"]["brackets"])["liability"] == 572_500.0
    assert T.SERVER_HELD_AUTHORITY is False
    tax_services = {s[":egov.service/id"]: s for s in DOC[":services"]
                    if s[":egov.service/module"] == "tax-assess"}
    for sid in ("tax.income.file", "tax.corporate.file", "tax.vat.file"):
        assert tax_services[sid][":egov.service/maturity"] == ":reference-impl", sid


def test_jp_profile_binds_each_service_to_agency_legal_basis_and_spec():
    profiles = DOC[":country-profiles"]
    jp = next(p for p in profiles if p[":country-profile/iso3"] == "JPN")
    service_ids = {s[":egov.service/id"] for s in DOC[":services"]}
    for b in jp[":country-profile/bindings"]:
        assert b[":bind/service"] in service_ids, b[":bind/service"]
        assert b[":bind/agency"]
        assert b[":bind/legal-basis"]
        assert b[":bind/national-spec"]
        # links back to the ooyake observation atlas (read-side who/where)
        assert b[":bind/atlas-did"].startswith("did:web:etzhayyim.com:gov:")


def test_country_profiles_are_sourcing_honest():
    """No profile may claim :authoritative coverage at R0 (ooyake G5 precedent)."""
    for p in DOC[":country-profiles"]:
        assert p[":country-profile/sourcing"] == ":representative", p[":country-profile/iso3"]


def test_multiple_countries_loaded_from_profiles_dir():
    """各国ように調整 — per-country profiles load from data/profiles/*.edn and merge."""
    iso3s = {p[":country-profile/iso3"] for p in DOC[":country-profiles"]}
    # at least the major jurisdictions localized this iteration
    for expect in {"JPN", "USA", "DEU", "GBR", "KOR", "EST", "IND", "EUR"}:
        assert expect in iso3s, f"missing country profile {expect}"


def test_every_country_binding_targets_a_known_service_with_full_localization():
    service_ids = {s[":egov.service/id"] for s in DOC[":services"]}
    for p in DOC[":country-profiles"]:
        assert p[":country-profile/operated-by"] == ":adopting-government", p[":country-profile/iso3"]
        assert p[":country-profile/authority-mode"] == ":supplied-to-state", p[":country-profile/iso3"]
        assert p[":country-profile/bindings"], f"{p[':country-profile/iso3']} has no bindings"
        for b in p[":country-profile/bindings"]:
            assert b[":bind/service"] in service_ids, b[":bind/service"]
            assert b[":bind/agency"]
            assert b[":bind/legal-basis"]
            assert b[":bind/national-spec"]


def test_coverage_report_renders():
    cov = S.coverage(DOC)
    assert cov["divisions_total"] == 10
    assert cov["services_total"] >= 15
    report = S.render_report(DOC, cov, S.validate(DOC))
    assert "coverage" in report.lower()
    assert "COFOG" in report


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
