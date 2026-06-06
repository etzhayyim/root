#!/usr/bin/env python3
"""matsurigoto 政 — COFOG-based e-Government Service Standard loader / validator / coverage.

ADR-2606052300 (proposed). Reads data/cofog-standard.kotoba.edn (the universal,
spec-derived service standard built on the UN COFOG function backbone) and:

  1. VALIDATES the standard (structural integrity + the three charter invariants):
       G1 no-server-authority  — every service has :server-held-authority false
       G2 spec-derived-only    — every service cites a non-empty official :spec-basis
       G3 authority-separation — :live-authority false + :operated-by :adopting-government
     plus: every service's COFOG class exists in the backbone, and references a known
     kotoba-wasm module.

  2. Emits a HONEST COVERAGE report (out/coverage.md): how much of the world's
     government-function space (COFOG 10 divisions / 69 groups) and the named
     transactional domains (taxation / civil-registry / corp-registry /
     identity-credential / social-protection / interop) the standard currently
     covers — separating :standard-draft (spec + module contract defined) from
     executable (none yet — every module .solve() raises at R0).

POSTURE: matsurigoto is the EXECUTION sibling of ooyake's observation atlas. It
SUPPLIES the standard to governments; it never operates as a government (G1/G3).

stdlib only. Usage:
    python3 standard.py [standard.edn] [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import sys

from _edn import load_edn

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_STD = HERE.parent / "data" / "cofog-standard.kotoba.edn"
PROFILES_DIR = HERE.parent / "data" / "profiles"

# The named transactional domains the e-gov standard must cover (user request).
REQUIRED_DOMAINS = {
    ":taxation",
    ":civil-registry",
    ":corp-registry",
    ":identity-credential",
}

# The universal service-level invariants (G1 no-operator-master-key + G2 spec-derived).
# WHO governs (G3) is a per-deployment PROFILE concern, validated separately — etzhayyim IS
# a government (Kingdom of God), so authority is BORNE, never disclaimed; it is just never an
# operator master key.
REQUIRED_INVARIANTS = {
    ":server-held-authority": False,  # G1 — never a platform/operator master key (ADR-2605231525)
    ":spec-derived": True,            # G2 — official public specs only
}

# G3 authority-bearing: every deployment names a legitimate governing authority + mode.
ALLOWED_OPERATED_BY = {":etzhayyim-council", ":adopting-government"}
ALLOWED_AUTHORITY_MODE = {":sovereign-governance", ":supplied-to-state"}


def load_profiles(directory: pathlib.Path = PROFILES_DIR) -> list[dict]:
    """Load every per-country profile from data/profiles/*.edn (one map per file)."""
    out: list[dict] = []
    if directory.exists():
        for f in sorted(directory.glob("*.edn")):
            p = load_edn(f)
            if isinstance(p, dict):
                out.append(p)
    return out


def load_standard(path: pathlib.Path = DEFAULT_STD) -> dict:
    doc = load_edn(path)
    if not isinstance(doc, dict):
        raise ValueError("standard root must be a map")
    # merge external per-country profiles (data/profiles/*.edn) into :country-profiles,
    # deduped by iso3 (inline list wins on collision).
    inline = list(doc.get(":country-profiles", []))
    seen = {p.get(":country-profile/iso3") for p in inline}
    for p in load_profiles():
        if p.get(":country-profile/iso3") not in seen:
            inline.append(p)
            seen.add(p.get(":country-profile/iso3"))
    doc[":country-profiles"] = inline
    return doc


def cofog_index(doc: dict) -> dict:
    return {row[":cofog/code"]: row for row in doc.get(":cofog", [])}


def module_index(doc: dict) -> dict:
    return {m[":egov.module/id"]: m for m in doc.get(":modules", [])}


def validate(doc: dict) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors: list[str] = []
    cofog = cofog_index(doc)
    modules = module_index(doc)
    services = doc.get(":services", [])

    if not services:
        errors.append("no :services in standard")

    seen_ids: set[str] = set()
    for s in services:
        sid = s.get(":egov.service/id", "<no-id>")
        if sid in seen_ids:
            errors.append(f"{sid}: duplicate service id")
        seen_ids.add(sid)

        # COFOG class must exist in the backbone
        code = s.get(":egov.service/cofog")
        if code not in cofog:
            errors.append(f"{sid}: COFOG class {code!r} not in backbone")

        # module must be a known kotoba-wasm module
        mod = s.get(":egov.service/module")
        if mod not in modules:
            errors.append(f"{sid}: unknown module {mod!r}")

        # G2 spec-derived-only: non-empty official spec basis
        specs = s.get(":egov.service/spec-basis") or []
        if not specs:
            errors.append(f"{sid}: G2 violation — empty :spec-basis (spec-derived-only)")

        # G1 + G3: the three structural invariants, exact values
        inv = s.get(":egov.service/invariants") or {}
        for k, want in REQUIRED_INVARIANTS.items():
            if inv.get(k) != want:
                errors.append(f"{sid}: invariant {k} must be {want!r}, got {inv.get(k)!r}")

    # COFOG backbone sanity: 10 divisions present
    divisions = [r for r in doc.get(":cofog", []) if r.get(":cofog/level") == ":division"]
    if len(divisions) != 10:
        errors.append(f"COFOG backbone must have 10 divisions, found {len(divisions)}")

    # G3 authority-bearing: every profile (polity OR country) names a legitimate
    # governing authority + mode, and every binding targets a known service.
    for p in doc.get(":polity-profiles", []):
        errors += _validate_profile(p, "polity", ":polity-profile/", seen_ids)
    for p in doc.get(":country-profiles", []):
        errors += _validate_profile(p, "country", ":country-profile/", seen_ids)

    return errors


def _validate_profile(p: dict, kind: str, prefix: str, service_ids: set[str]) -> list[str]:
    errs: list[str] = []
    name = p.get(prefix + ("id" if kind == "polity" else "iso3"), "<no-id>")
    ob = p.get(prefix + "operated-by")
    if ob not in ALLOWED_OPERATED_BY:
        errs.append(f"{kind} {name}: :operated-by {ob!r} not in {ALLOWED_OPERATED_BY}")
    am = p.get(prefix + "authority-mode")
    if am not in ALLOWED_AUTHORITY_MODE:
        errs.append(f"{kind} {name}: :authority-mode {am!r} not in {ALLOWED_AUTHORITY_MODE}")
    # the Kingdom governs via its Council (sovereign); a nation-state runs its own (supplied).
    if kind == "polity" and (ob, am) != (":etzhayyim-council", ":sovereign-governance"):
        errs.append(f"polity {name}: must be governed by :etzhayyim-council/:sovereign-governance")
    if kind == "country" and (ob, am) != (":adopting-government", ":supplied-to-state"):
        errs.append(f"country {name}: must be :adopting-government/:supplied-to-state")
    for b in p.get(prefix + "bindings", []):
        if b.get(":bind/service") not in service_ids:
            errs.append(f"{kind} {name}: binding to unknown service {b.get(':bind/service')!r}")
    return errs


def coverage(doc: dict) -> dict:
    """Compute honest coverage figures."""
    cofog = doc.get(":cofog", [])
    divisions = [r for r in cofog if r.get(":cofog/level") == ":division"]
    groups = [r for r in cofog if r.get(":cofog/level") == ":group"]
    services = doc.get(":services", [])

    def div_of(code: str) -> str:
        return code.split(".")[0]

    covered_divs = {div_of(s[":egov.service/cofog"]) for s in services}
    covered_groups = {s[":egov.service/cofog"] for s in services}

    by_domain: dict[str, int] = {}
    by_module: dict[str, int] = {}
    by_maturity: dict[str, int] = {}
    for s in services:
        by_domain[s.get(":egov.service/domain", "?")] = by_domain.get(s.get(":egov.service/domain", "?"), 0) + 1
        by_module[s.get(":egov.service/module", "?")] = by_module.get(s.get(":egov.service/module", "?"), 0) + 1
        by_maturity[s.get(":egov.service/maturity", "?")] = by_maturity.get(s.get(":egov.service/maturity", "?"), 0) + 1

    polity_cov = []
    for p in doc.get(":polity-profiles", []):
        polity_cov.append({
            "id": p.get(":polity-profile/id"),
            "name": p.get(":polity-profile/name"),
            "operated_by": p.get(":polity-profile/operated-by"),
            "authority_mode": p.get(":polity-profile/authority-mode"),
            "bound": len(p.get(":polity-profile/bindings", [])),
        })

    profiles = doc.get(":country-profiles", [])
    profile_cov = []
    localization: dict[str, int] = {}  # service-id → number of countries that localize it
    for p in profiles:
        binds = p.get(":country-profile/bindings", [])
        for b in binds:
            sid = b.get(":bind/service")
            localization[sid] = localization.get(sid, 0) + 1
        profile_cov.append({
            "iso3": p.get(":country-profile/iso3"),
            "name": p.get(":country-profile/name"),
            "operated_by": p.get(":country-profile/operated-by"),
            "sourcing": p.get(":country-profile/sourcing"),
            "bound": len(binds),
        })

    return {
        "divisions_total": len(divisions),
        "divisions_covered": len(covered_divs),
        "groups_total": len(groups),
        "groups_covered": len(covered_groups),
        "services_total": len(services),
        "by_domain": by_domain,
        "by_module": by_module,
        "by_maturity": by_maturity,
        "required_domains_covered": sorted(REQUIRED_DOMAINS & set(by_domain)),
        "required_domains_missing": sorted(REQUIRED_DOMAINS - set(by_domain)),
        "executable_services": by_maturity.get(":executable", 0),
        "polities": polity_cov,
        "profiles": profile_cov,
        "countries": len(profile_cov),
        "localization": localization,
    }


def render_report(doc: dict, cov: dict, errors: list[str]) -> str:
    std = doc.get(":standard", {})
    L = []
    L.append(f"# {std.get(':standard/title-en', 'e-gov standard')} — coverage")
    L.append("")
    L.append(f"- standard: `{std.get(':standard/id')}` v{std.get(':standard/version')}")
    L.append(f"- backbone: {std.get(':standard/backbone')}")
    L.append(f"- validation: {'✅ PASS' if not errors else f'❌ {len(errors)} error(s)'}")
    L.append("")
    L.append("## COFOG function-space coverage (honest)")
    L.append("")
    L.append(f"- divisions covered: **{cov['divisions_covered']}/{cov['divisions_total']}**")
    L.append(f"- groups covered: **{cov['groups_covered']}/{cov['groups_total']}**")
    L.append(f"- standardized services: **{cov['services_total']}**")
    L.append(f"- executable (module .solve runs): **{cov['executable_services']}** "
             f"(R0 — all modules raise; deployment Council+operator gated)")
    L.append("")
    L.append("## Named transactional domains (user request)")
    L.append("")
    L.append(f"- covered: {', '.join(cov['required_domains_covered']) or '—'}")
    L.append(f"- missing: {', '.join(cov['required_domains_missing']) or '— (all covered)'}")
    L.append("")
    L.append("## Services by domain")
    L.append("")
    for k in sorted(cov["by_domain"]):
        L.append(f"- {k}: {cov['by_domain'][k]}")
    L.append("")
    L.append("## Services by maturity")
    L.append("")
    for k in sorted(cov["by_maturity"]):
        L.append(f"- {k}: {cov['by_maturity'][k]}")
    L.append("")
    L.append("## Polity profiles (principal A — the Kingdom's own 統治機構)")
    L.append("")
    if cov["polities"]:
        for p in cov["polities"]:
            L.append(f"- {p['name']}: {p['bound']} organs bound "
                     f"[{p['operated_by']} / {p['authority_mode']}]")
    else:
        L.append("- none yet")
    L.append("")
    L.append(f"## Country profiles (principal B — {cov['countries']} nation-state adopters)")
    L.append("")
    if cov["profiles"]:
        for p in cov["profiles"]:
            L.append(f"- {p['iso3']} ({p['name']}): {p['bound']} services bound "
                     f"[{p['operated_by']} / sourcing {p['sourcing']}]")
    else:
        L.append("- none yet")
    L.append("")
    L.append("## Per-service localization (各国調整 — how many countries localize each service)")
    L.append("")
    services = {s[":egov.service/id"]: s for s in doc.get(":services", [])}
    for sid in sorted(services, key=lambda x: (-cov["localization"].get(x, 0), x)):
        n = cov["localization"].get(sid, 0)
        ja = services[sid].get(":egov.service/ja", "")
        L.append(f"- `{sid}` ({ja}): **{n}** / {cov['countries']} countries")
    L.append("")
    if errors:
        L.append("## Validation errors")
        L.append("")
        for e in errors:
            L.append(f"- ❌ {e}")
        L.append("")
    return "\n".join(L)


def main(argv: list[str]) -> int:
    path = DEFAULT_STD
    outdir = HERE / "out"
    args = list(argv)
    if "--out" in args:
        i = args.index("--out")
        outdir = pathlib.Path(args[i + 1])
        del args[i:i + 2]
    if args:
        path = pathlib.Path(args[0])

    doc = load_standard(path)
    errors = validate(doc)
    cov = coverage(doc)
    report = render_report(doc, cov, errors)

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "coverage.md").write_text(report, encoding="utf-8")

    print(report)
    print(f"\n[written] {outdir / 'coverage.md'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
