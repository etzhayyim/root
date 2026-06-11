---
id: adr-2606112400-tate-worldwide-jurisdiction-expansion-r1
title: "ADR-2606112400: tate 盾 R1 — worldwide jurisdiction expansion (日本以外にも対応)"
status: proposed
doc_type: adr
topic: tate-worldwide-jurisdictions
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "generalizes the JP-only legal-defense registries to a jurisdiction-keyed worldwide layer with coverage honesty"
authoritative_for:
  - tate-jurisdiction-registry
depends_on:
  - adr-2606112300 # tate R0 (JP-only)
related:
  - adr-2606112200 # kaiyaku
  - adr-2606021600 # ooyake world government atlas (worldwide-mirror precedent)
  - adr-2606072000 # kosatsu (multi-asserter / jurisdiction-divergence precedent)
supersedes: []
superseded_by: []
---

# ADR-2606112400: tate 盾 R1 — worldwide jurisdiction expansion

**Status**: proposed
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

tate R0 (ADR-2606112300) shipped JP-only: 消費者契約法/民訴法-anchored registries, the
特別送達 fake-guard, and 法テラス referrals. The founder's next step: **「日本以外にも
全て対応」**. "全て" cannot honestly mean encoding ~193 legal systems at once — the
roster's own precedent (inochi G5, uchiwake crosscheck, ooyake) is **coverage honesty**:
a jurisdiction-keyed architecture + a representative seed + a measurable, named gap.

# Decision

Make every tate registry **jurisdiction-keyed** and seed **5 representative legal
systems** (`:jp :us :eu :uk :de`), with a new constitutional gate:

**G10 jurisdiction-honesty** — anchors and procedures NEVER cross jurisdictions
(structural filter in `scan_doc` / `classify`); a notice from an uncovered
jurisdiction degrades to **`:unknown-jurisdiction`** (no deadlines, no options,
`declare-uncovered` + evidence + local-professional referral) — **tate never guesses
foreign law**; `coverage_report.py` reports the covered/uncovered ratio (5/193 ≈ 2.6%)
and a NAMED gap worklist.

## 1. Jurisdiction registry (`data/jurisdictions.edn`)

Per system: the DISCLOSED unauthorized-practice anchor (弁護士法72条 / state UPL /
Legal Services Act 2007 reserved activities / RDG / member-state rules), the genuine-
service note, referral + fake-help directories (法テラス · state bar + LSC + FTC ·
Citizens Advice + Action Fraud · Verbraucherzentrale + Polizei Onlinewache · ECC-Net),
and a representative refer-over line (¥600k / $10k / £10k / €5k). The **G3
representation-unrepresentable gate stays global and structural**; the registry only
carries each system's citation.

## 2. Clause patterns (8 intl shapes added, 22 total)

`:us` binding arbitration + class-action waiver (FAA — 米国では原則 enforceable, JP と
逆である事実を開示), auto-renewal negative option (FTC 16 CFR Part 425 / Cal. ARL),
early-termination fee (州 UDAP) · `:eu` 14日撤回権の排除 (CRD 2011/83/EU Art.9/16),
sole-discretion unilateral change (UCTD 93/13/EEC Annex 1(j)) · `:uk` blanket
liability exclusion (CRA 2015 s.62/65) · `:de` kurzfristige Preiserhöhung (BGB §309
Nr.1), pauschalierter Schadensersatz (§309 Nr.5). G2 (anchor-not-verdict) + G5
(consumer⊬B2B) unchanged and now jurisdiction-scoped.

## 3. Procedures (6 intl added, 11 total) + generalized fake-guard

`:us` summons+complaint (answer 21d federal FRCP 12(a) / 州 20–30d — check the
summons; referral-always like 本訴) and small claims (州差を開示) · `:eu` European
Order for Payment (opposition 30d, Reg 1896/2006 Art.16) and European Small Claims
(≤€5,000, answer 30d, Reg 861/2007 Art.5(3)) · `:uk` claim form (defence 14d / 28d
with acknowledgment, CPR 10/15.4) · `:de` Mahnbescheid (Widerspruch 2 Wochen, ZPO
§692/694/700). `:proc/genuine-channel` → **`:proc/genuine-channels` vector**: JP
特別送達 · US personal service / certified mail / sheriff · DE förmliche Zustellung ·
UK court post · EU formal service. The G6 guard generalizes unchanged: court
vocabulary (now multilingual trip-wires incl. "summons" / "Mahnbescheid" / "order for
payment") on any non-genuine channel → `:suspected-fake`, do-not-contact-sender,
jurisdiction's fake-help directory. G4 deadline-honesty unchanged (rules + anchors,
never computed dates).

## R1 scope (this ADR)

Registries jurisdiction-keyed + 5-system seed + `coverage_report.py` + intl synthetic
docs/notices + scanner/planner G10 filters; **30 tests green** (10 terms / 16 respond /
4 coverage), including: JP keywords on a US doc fire no JP anchor; the same court text
is genuine via formal service and fake via email per jurisdiction; `:br` degrades to
`:unknown-jurisdiction`. Next waves (the named gaps): EU member-state national law,
US state-level decomposition, :kr :cn :tw :in :br :au :ca :sg, civil specialty tracks.

# Consequences

- 「日本以外」が構造になった: adding a jurisdiction = one registry entry + patterns +
  procedures + tests, no code change.
- Honesty is enforced, not aspirational: uncovered law is refused, not guessed; the
  coverage report doubles as the ingest worklist.
- Statutory-accuracy maintenance multiplies per jurisdiction — every entry carries
  `:verify-current-law true`; amendments must cite current sources (suimin G1-style
  whitelist for legal sources is a natural R2 hardening).
- The EU entry covers cross-border instruments only — member-state national law is a
  named gap, not silently implied.

# Alternatives Considered

1. **Encode "all" jurisdictions now.** Rejected: un-verifiable at quality; violates
   sourcing honesty; the registry architecture makes incremental coverage cheap.
2. **LLM-generated foreign-law answers for uncovered jurisdictions.** Rejected (G10):
   hallucinated deadlines are the most dangerous failure mode this actor can have.
3. **One registry per country directory tree.** Deferred: flat jurisdiction-keyed
   files are sufficient at 5 systems; split when a registry file grows unwieldy.

# References

- `20-actors/tate/` · ADR-2606112300 (R0) · ooyake ADR-2606021600 · kosatsu
  ADR-2606072000 · inochi ADR-2606073000 (coverage honesty)
- Intl anchors referenced (all `:verify-current-law`): FAA; FTC Negative Option Rule
  16 CFR 425; Cal. Bus. & Prof. Code §17600+; FRCP 12(a); Directive 93/13/EEC;
  Directive 2011/83/EU Art.9/16; Reg (EC) 1896/2006 Art.16; Reg (EC) 861/2007
  Art.5(3); Consumer Rights Act 2015 s.62/65; CPR Parts 6/10/15; Legal Services Act
  2007; BGB §309; ZPO §§166, 692, 694, 700; RDG
