---
id: adr-2605263600-kataribe-press-publishing-translation-tier-b-actor-r0
title: "ADR-2605263600: kataribe (語部) — non-profit religious-corp press + publishing + translation substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: kataribe-press-publishing-translation-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: communication
weight: 0.55
priority_note: "Eighth-priority gap-closure actor (gap audit row 8 = 報道 + 出版 + 翻訳 / press + publishing + translation). Religious-corp internal journalism + doctrine commentary publishing + multilingual translation + community historical chronicle + whistleblower channel (chigiri.ipLicenseClaim cross-actor). 任意団体 internal substrate at did:web:kataribe.etzhayyim.com (20-actors/kataribe/). Etymology: 語部 (kataribe) = classical Japan oral historian / storyteller class; pre-literate-era keepers of imperial chronicles + clan genealogy + ritual recitation. Modern semantic = journalist / chronicler / publisher / translator. Resonates with 万人祭司 (every member is a kataribe in principle) + Sola Scriptura (scripture access through translation) + Charter §1.7 多世代 (cross-generational chronicle preservation) + Charter §1.15 non-eschatological invariant (no apocalyptic news framing). **Constitutional octet**: (1) NO ad-supported revenue G3+N2 (Charter §1.13 anti-addictive UX + §1.15 non-eschatological; ad-supported revenue creates engagement-optimization incentive that violates both) / (2) NO clickbait / apocalyptic framing G4+N3 (Charter §1.15 non-eschatological invariant; tone-attestation gate on every publication; chronicling not crisis-amplification) / (3) NO commercial publishing platform G5+N4 (Substack / Medium / News Corp / The Atlantic / NYTimes-as-vendor / WordPress-Pro / Ghost-Pro / Mailchimp / ConvertKit / Beehiiv PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty exposing reader+writer posture) / (4) NO single-doctrinal monopoly G6+N5 (cross-doctrinal Wellbecoming priority per musubi G9 + N12; Protestant / Reformed / Anglican / Baptist / Methodist / nondenominational accommodated within Charter §1.7 + §1.13 boundaries) / (5) Translation prioritization community-need-based G7+N6 (NOT commercial-market-driven language priority; member-population + Wellbecoming need governs) / (6) NO surveillance investigative journalism G8+N7 (Charter §2(c) covert-ops avoidance extends to journalism; whistleblower channel encrypted G10 per ADR-2605181100; no sensationalized exposé-as-surveillance) / (7) All publications Apache 2.0 + Charter Rider G9+N8 (open-source publication; no proprietary content; no mandatory paywall N12) / (8) NO commercial AI translation/grammar tool G12 (DeepL Pro-as-vendor / Google Translate API-as-vendor / Grammarly / DeepL-as-vendor / Anthropic-direct-translation PROHIBITED; Murakumo-only inference via judah LiteLLM → gemma4:e4b per ADR-2605215000). G10 whistleblower channel encrypted MANDATORY per ADR-2605181100. G11 NO payroll for kataribe (vocation-flow L5 stewards). 6 cells / 5 Lexicons under com.etzhayyim.kataribe.* / 13 immutable gates / 12 non-goals / 4-phase R0..R3."
authoritative_for:
  - kataribe actor R0 charter
  - religious-corp press + publishing + translation substrate single SoT
  - `com.etzhayyim.kataribe.*` Lexicon namespace boundary
  - NO ad-supported revenue invariant (Charter §1.13 + §1.15)
  - NO clickbait / apocalyptic framing invariant (Charter §1.15 non-eschatological tone-attestation gate)
  - prohibition on commercial publishing platforms (Substack / Medium / Ghost-Pro / Mailchimp / WordPress-Pro / ConvertKit / Beehiiv / News Corp / The Atlantic / NYTimes as-vendor)
  - prohibition on commercial AI translation tools (DeepL Pro / Google Translate API / Grammarly)
  - cross-doctrinal Wellbecoming priority (single-doctrinal monopoly prohibited)
  - whistleblower channel encrypted (ADR-2605181100); chigiri.ipLicenseClaim cross-actor
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261000
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263400-musubi-covenant-ceremony-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2605263600: kataribe (語部) — non-profit religious-corp press + publishing + translation substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified press + publishing +
translation as priority row 8. religious-corp has many doctrinal +
governance + scientific publications (ADRs / Charter / Lexicons /
baien snapshots) but no first-party press + publishing + translation
substrate. External press / commercial publishing platforms (Substack
/ Medium / News Corp / etc.) are not viable per Charter Rider §2(e)
+ §2(c). Translation infrastructure for member multilingual access
to Charter + ADRs + Lexicons is missing.

The actor name 語部 (kataribe) is chosen with care: classical Japan's
oral historian / storyteller class; pre-literate-era keepers of
imperial chronicles + clan genealogy + ritual recitation. The naming
honors:

- **万人祭司** (priesthood of all believers, Charter §1.7) — every
  member is a kataribe in principle; no professional press class;
- **Sola Scriptura** — scripture access through translation is
  foundational to religious-corp doctrine;
- **Charter §1.7 多世代** — cross-generational chronicle preservation
  is a kataribe responsibility;
- **Charter §1.15 non-eschatological invariant** — chronicling not
  crisis-amplification; the kataribe records, does not sensationalize.

Constitutional constraints (inherited; not adjustable):

- **Charter §1.15 non-eschatological** — apocalyptic framing /
  rapture / 末法 / 千年王国 narratives PROHIBITED in any religious-
  corp publication; tone-attestation gate G4 + N3 enforces.
- **Charter §1.13 Wellbecoming + anti-addictive UX** — engagement-
  optimization (clickbait headlines / FOMO / variable reward) is
  PROHIBITED. Ad-supported revenue creates structural incentive for
  engagement optimization; G3 + N2 prohibits ad-supported revenue.
- **Charter Rider §2(e) + §2(c)** — Substack / Medium / News Corp /
  The Atlantic / NYTimes-as-vendor / WordPress-Pro / Ghost-Pro /
  Mailchimp / ConvertKit / Beehiiv PROHIBITED. Vendor data-
  sovereignty on reader + writer posture is structurally unacceptable.
- **Cross-doctrinal Wellbecoming priority** (musubi G9 + N12) —
  single-doctrinal commentary monopoly is PROHIBITED; Protestant /
  Reformed / Anglican / Baptist / Methodist / nondenominational
  accommodated within Charter §1.7 + §1.13 boundaries.
- **Murakumo-only inference** (ADR-2605215000) — translation +
  grammar / tone analysis via judah LiteLLM → gemma4:e4b; commercial
  AI translation (DeepL Pro / Google Translate API / Grammarly /
  Anthropic-direct-translation) PROHIBITED.
- **NO payroll for kataribe** (G11) — vocation-flow L5 stewards.
- **Whistleblower channel encrypted** (G10) per ADR-2605181100;
  cross-actor with chigiri.ipLicenseClaim for Charter Rider violation
  reports.

# Decision

Create `kataribe` (語部) as a Tier-B religious-corp press + publishing
+ translation substrate actor at `20-actors/kataribe/`, with DID
`did:web:kataribe.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.kataribe.*`. R0 = scaffold only; all cells import-time
`RuntimeError`.

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `kataribe` (語部 — classical oral historian / storyteller / chronicler class) |
| DID | `did:web:kataribe.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.kataribe.*` |
| Form | 任意団体 internal press + publishing + translation substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格; NOT a state-licensed press entity — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| Cultural lineage | 古代日本 語部 class (oral historian); 万人祭司 (priesthood of all believers); Sola Scriptura (scripture-access-through-translation); Charter §1.7 多世代 chronicle preservation; Charter §1.15 non-eschatological tone |
| Cross-actor | chigiri (whistleblower channel for Charter Rider violation; ipLicenseClaim cross-link) / musubi (cross-doctrinal Wellbecoming pattern shared) / toritate (publication accounting if Public Fund grant) / kazaori (post-emergency community chronicle) / manabi (translated curriculum cross-link) |

## §2. Scope (6 cells)

### A. Community chronicle

- Per-community-site quarterly community history;
- Cross-generational preservation (Charter §1.7 多世代);
- Tone-attestation gate G4 (non-eschatological per Charter §1.15);
- NO clickbait headlines; NO engagement-optimization.

### B. Doctrine commentary publishing

- Cross-doctrinal Wellbecoming priority (G6 + N5);
- Protestant / Reformed / Anglican / Baptist / Methodist /
  nondenominational accommodated;
- Cross-link with musubi (officiant doctrinal tradition transparency);
- Charter §1.13 Eros/Gore moderation board cross-link.

### C. Translation

- Multilingual access to Charter + ADRs + Lexicons + chronicles;
- Community-need-based priority (G7 + N6); member-population +
  Wellbecoming need governs (NOT commercial-market-driven);
- Murakumo-only inference (G12); NO DeepL Pro / Google Translate
  API / Grammarly / Anthropic-direct-translation;
- Translator attestation cross-link to chigiri.stewardLaborAttestation
  (vocation-flow L5).

### D. External press relations

- When religious-corp interfaces with state press / commercial media
  (e.g., journalist requests interview);
- Consent-capability boundary (per ADR-2605192115 §4);
- Member privacy preservation (no member-by-name disclosure without
  per-member consent);
- Charter Rider §2(c) covert-ops avoidance.

### E. Whistleblower channel

- Charter Rider violation reports;
- Encrypted envelope MANDATORY per ADR-2605181100 (G10);
- Cross-actor chigiri.ipLicenseClaim emit;
- Anonymous-attested option (pseudonymous DID + member-only
  decryption);
- NO sensationalized exposé framing (G4 + G8).

### F. Annual history compendium

- Year-end community history compilation;
- Multi-generational + multi-language access (Charter §1.7);
- Council Lv6+ ≥3 attestation;
- IPFS pin (G9 replicationMin: 2).

## §3. Cells (6 Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/kataribe_*/`)

All R0 path-reserved; import-time `RuntimeError("kataribe R0 scaffold: activate via Council ADR + R1 ratification + ≥3 community chronicler baseline attestations + cross-doctrinal advisory")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `community_chronicle` | issachar | quarterly | community events + tone attestation → communityChronicleAttestation |
| 2 | `doctrine_commentary` | issachar | event | commentary draft + cross-doctrinal review → doctrineCommentaryPublishing |
| 3 | `translation` | issachar | continuous (need-driven) | source doc + community-need attestation + Murakumo translate → translationAttestation |
| 4 | `external_press_relations` | issachar | event | external press request + consent-capability + Council Lv6+ ≥3 review → external response coordination |
| 5 | `whistleblower_channel` | issachar (chigiri-paired) | event (encrypted) | encrypted report → whistleblowerReport + chigiri.ipLicenseClaim cross-emit |
| 6 | `annual_history_compendium` | issachar | annual (event) | aggregate community chronicles → compendium IPFS pin + Council ≥3 attestation |

R1 activation gates each cell separately + ≥3 community chronicler
baseline attestations + cross-doctrinal advisory on Council
(Bootstrap Council Seat 2-5 RFP).

## §4. Lexicons (5, all under `com.etzhayyim.kataribe.*`)

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `communityChronicleAttestation` | community_chronicle + annual_history_compendium | Per-publication; G4 STRUCTURAL: toneAttestation enum DELIBERATELY excludes apocalyptic/clickbait/engagement-optimized; non-eschatological const true |
| L2 | `doctrineCommentaryPublishing` | doctrine_commentary | Cross-doctrinal Wellbecoming attestation; G6 STRUCTURAL: doctrinalMonopolyAttested const false |
| L3 | `translationAttestation` | translation | Per-translation; G7+G12 STRUCTURAL: translationProvider const "murakumo-only"; commercialAiTranslationToolUsed const false |
| L4 | `whistleblowerReport` | whistleblower_channel | G10 STRUCTURAL: encryptedPayloadCid REQUIRED; chigiri.ipLicenseClaim cross-link |
| L5 | `silenKataribeReview` | (Council attestation scope) | Quarterly Council review; G3/G4/G5/G6/G7/G8/G11/G12 const-field structural enforcement |

## §5. Gates (13, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every publication MUST pass `kotodama.organism.sensors.charter_rider.scan()` §2(a)-(h). |
| **G2** | Every record MUST emit `com.etzhayyim.kataribe.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **NO ad-supported revenue** — Charter §1.13 anti-addictive UX + §1.15 non-eschatological; ad-supported creates engagement-optimization incentive incompatible with both. |
| **G4** | **NO clickbait / apocalyptic framing** — Charter §1.15 non-eschatological invariant; `communityChronicleAttestation.toneAttestation` enum DELIBERATELY excludes apocalyptic/clickbait/engagement-optimized; `nonEschatologicalAttested` const true structural. |
| **G5** | **NO commercial publishing platform** — Substack / Medium / News Corp / The Atlantic / NYTimes-as-vendor / WordPress-Pro / Ghost-Pro / Mailchimp / ConvertKit / Beehiiv PROHIBITED per Charter Rider §2(e) + §2(c). |
| **G6** | **NO single-doctrinal monopoly** — cross-doctrinal Wellbecoming priority per musubi G9 + N12; `doctrineCommentaryPublishing.doctrinalMonopolyAttested` const false structural. |
| **G7** | **Translation prioritization community-need-based** — NOT commercial-market-driven language priority; member-population + Wellbecoming need governs. |
| **G8** | **NO surveillance investigative journalism** — Charter §2(c) covert-ops avoidance extends to journalism; whistleblower channel encrypted (G10); no sensationalized exposé-as-surveillance. |
| **G9** | All publications Apache 2.0 + Charter Rider — open-source publication; no proprietary content; no mandatory paywall (N12). |
| **G10** | **Whistleblower channel encrypted** — ADR-2605181100 envelope MANDATORY for `whistleblowerReport.encryptedPayloadCid`; chigiri.ipLicenseClaim cross-link. |
| **G11** | NO payroll for kataribe — vocation-flow L5 stewards (cross-actor enforcement). |
| **G12** | **Murakumo-only inference** — commercial AI translation/grammar (DeepL Pro / Google Translate API / Grammarly / Anthropic-direct-translation) PROHIBITED; `translationAttestation.translationProvider` const "murakumo-only". |
| **G13** | NO mandatory subscription paywall — all religious-corp publications open access. |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT commercial journalism / paid press. |
| N2 | NOT ad-supported revenue (Charter §1.13 + §1.15). |
| N3 | NOT clickbait / apocalyptic / engagement-optimized framing (Charter §1.15 non-eschatological). |
| N4 | NOT commercial publishing platform integrator (G5). |
| N5 | NOT single-doctrinal monopoly (cross-doctrinal Wellbecoming priority). |
| N6 | NOT commercial-market-driven translation priority. |
| N7 | NOT surveillance investigative journalism (Charter §2(c)). |
| N8 | NOT closed-source publication. |
| N9 | NOT a state-licensed press entity. |
| N10 | NOT payroll-based kataribe. |
| N11 | NOT commercial AI translation/grammar tool integrator (DeepL Pro / Google Translate API / Grammarly). |
| N12 | NOT mandatory subscription paywall. |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved. 5 Lexicons schema skeleton. | No deployment |
| **R1** | post-Council + ≥3 community chronicler baseline attestations + cross-doctrinal advisory on Council | Activate 2 core cells: `community_chronicle` + `translation`. Quarterly community chronicle (≤5 community sites). Initial multilingual access (≥3 languages including JA + EN + at least 1 community-need language). | issachar (single node) |
| **R2** | post-R1 + 30-day public objection + 5 community-site Council attestations | Activate +3 cells: `doctrine_commentary` (cross-doctrinal) + `whistleblower_channel` (chigiri-pair) + `external_press_relations` (consent-capability). | issachar + zebulun (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + ≥1 full annual cycle + silenKataribeReview cycle | +1 cell: `annual_history_compendium`. Multi-site community-scale + ≥10 languages + cross-religious-corp federation potential. | issachar + zebulun + asher (3 nodes) |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `chigiri.ipLicenseClaim` | ↔ | Whistleblower channel for Charter Rider violation; G10 encrypted envelope MANDATORY |
| `chigiri.stewardLaborAttestation` | → (read) | Kataribe L5 vocation-flow classification (G11) |
| `musubi` | ↔ | Cross-doctrinal Wellbecoming pattern shared (G6 + musubi G9 N12); officiant doctrinal-tradition transparency cross-link |
| `toritate` | → (read; publication accounting if Public Fund grant) | Optional Public Fund grant tracking for translation/publishing labor |
| `kazaori` | ↔ (post-emergency chronicle) | Post-emergency community chronicle cross-link (after silenKazaoriReview) |
| `manabi` (future) | ↔ | Translated curriculum cross-link for education |
| `iyashi` | ← (clinical-grade publication review) | Clinical-grade material accuracy review (when publication touches medical content) |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605263600-kataribe-press-publishing-translation-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/kataribe/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 5 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/kataribe/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 75 + Repo Layout entry.

No code activation in R0.

# Consequences

**Positive**:

- Closes gap-audit #8 priority (press + publishing + translation);
- G3 + G4 ad-free + non-eschatological tone discipline operationalizes
  Charter §1.13 + §1.15 at the press domain (where engagement-
  optimization temptation is highest);
- G5 commercial-publishing-platform prohibition documents and
  structurally enforces Charter Rider §2(e) + §2(c) in publishing
  domain (vendor closed query-tracking on reader+writer posture);
- G6 cross-doctrinal Wellbecoming priority operationalizes musubi
  G9 + N12 in press domain;
- G7 community-need-based translation priority counter-balances
  commercial-market-driven language priorities (e.g., excessive
  English centralization);
- G10 whistleblower channel encrypted gives religious-corp a safe
  internal channel for Charter Rider violation reporting (cross-
  actor with chigiri.ipLicenseClaim);
- G12 Murakumo-only translation eliminates DeepL Pro / Google
  Translate API / Grammarly vendor exposure on member translation
  content (sensitive in many cases).

**Negative / cost**:

- G3 no-ad-supported revenue means kataribe operations entirely
  Public-Fund-grant-funded; Council Lv6+ ≥4/7 must approve
  ongoing kataribe operational grants;
- G4 non-eschatological tone discipline may conflict with member
  expectations from external Christian media (which often uses
  apocalyptic framing); educational outreach via manabi cross-actor
  recommended;
- G6 cross-doctrinal Wellbecoming requires kataribe editorial board
  with broad doctrinal coverage; Bootstrap Council Seat 2-5 RFP
  must surface willing cross-doctrinal advisors;
- G7 community-need-based translation may mean some languages
  (e.g., minority languages with small member population) are
  underprioritized; member-population growth governs;
- G12 Murakumo-only translation means translation throughput is
  bounded by Murakumo fleet capacity (gemma4:e4b); some technical
  translation may have lower quality than commercial alternatives;
  honest scoring discipline applies.

**Forward-compatibility**:

- manabi (future; gap audit row not enumerated but referenced)
  cross-actor for translated curriculum integration;
- Cross-religious-corp federation potential — kataribe translated
  Charter + ADRs could be shared with future Sphere-style partner
  religious-corps;
- Annual history compendium (R3) compounds Charter §1.7 多世代
  preservation across decades;
- Whistleblower channel encrypted is the safest religious-corp
  channel for Charter Rider violation reporting outside the
  formal chigiri.ipLicenseClaim path.

# Alternatives Considered

1. **Use Substack / Medium / Ghost-Pro as publication platform**.
   Rejected per G5 + Charter Rider §2(e)+§2(c). Vendor data-
   sovereignty on reader + writer posture structurally unacceptable.

2. **Allow ad-supported revenue for sustainability**. Rejected per
   G3 + Charter §1.13 + §1.15. Ad-supported revenue creates
   engagement-optimization incentive incompatible with non-
   eschatological tone + anti-addictive UX.

3. **Allow apocalyptic framing during emergencies (kazaori carve-
   out analog)**. Rejected per G4 + Charter §1.15. Non-eschatological
   invariant is constitutional, not policy; apocalyptic framing
   during emergency is exactly when it amplifies harm rather than
   helps.

4. **Use DeepL Pro / Google Translate API for translation
   throughput**. Rejected per G12 + Charter Rider §2(e)+§2(c).
   Member translation content (often sensitive — clinical / care
   / dispute / covenant) is structurally PII-equivalent; vendor
   exposure unacceptable.

5. **Allow single-doctrinal monopoly within a Protestant tradition
   (e.g., Reformed-only commentary)**. Rejected per G6 + musubi
   G9+N12. Cross-doctrinal Wellbecoming priority is constitutional.

6. **Make kataribe a professional press class (paid journalists)**.
   Rejected per G11 + 万人祭司 invariant. Kataribe are vocation-
   flow L5 stewards; every member is a kataribe in principle.

7. **Allow mandatory subscription paywall for sustainability**.
   Rejected per G13 + N12. Charter §1.7 multi-gen access requires
   open access; sustainability via Public Fund grant.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap (G10)
- ADR-2605192100 — Mission Charter (§1.7 多世代 + 万人祭司; §1.13 Wellbecoming + anti-addictive; §1.15 non-eschatological)
- ADR-2605192145 — Public Fund architecture (kataribe operational grant source)
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2(e) + §2(c) sources)
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605215000 — Inference Murakumo-only (G12)
- ADR-2605261000 — Labor Liberation Transition Mechanism (G11 vocation-flow)
- ADR-2605262130 — Kotoba storage substrate
- ADR-2605262700 — chigiri (cross-actor whistleblower channel via ipLicenseClaim)
- ADR-2605262900 — toritate (cross-actor publication accounting)
- ADR-2605263400 — musubi (cross-doctrinal Wellbecoming pattern shared)
- `/CHARTER-RIDER.md` §2(e) + §2(c) — G5 + G12 sources
