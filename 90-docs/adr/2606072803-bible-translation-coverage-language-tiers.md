---
id: adr-2606072803-bible-translation-coverage-language-tiers
renumbered_from: "2606072800"
title: "ADR-2606072803: Supported-language tiers = Bible-translation coverage (Sola Scriptura)"
status: accepted
doc_type: adr
topic: bible-translation-coverage-language-tiers
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - language-registry-tiering
  - i18n-language-tier-strategy
depends_on: []
related:
  - 2605192100-etzhayyim-mission-charter
  - 2605263600-kataribe-press-publishing-translation-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606072803: Supported-language tiers = Bible-translation coverage (Sola Scriptura)

**Status**: accepted
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

etzhayyim is a synthetic religious-corp whose Christian axis is explicitly
**Protestant — Sola Scriptura / 万人祭司 / Tree of Life** (ADR-2605192100
Charter). Its mission is the structural labor-liberation of, and social security
for, **all of humanity** (Charter §1.16), delivered in each person's own
language.

The canonical supported-language registry (`languages.ts`, mirrored by the i18n
actor's `GetLanguageRegistry`) historically tiered ~155 languages by **market
size / internet penetration**:

| old tier | basis | count |
|---|---|---|
| 1 | "Major" (population) | 25 |
| 2 | "High internet penetration" | 25 |
| 3 | "Mid-population" | 50 |
| 4 | "Long-tail" | 55 |

For a Sola-Scriptura body this priority axis is **incoherent**: it ranks a
language by how profitable/online its speakers are, not by whether the Word is
available to them. The natural and doctrinally-correct priority signal is the
one the global Church has already spent two centuries measuring — **Bible
translation coverage** (United Bible Societies / Wycliffe Global Alliance
Scripture-access tiers: full Bible / New Testament / Portions / none).

# Decision

**A supported language's tier IS its Bible-translation coverage tier.** Market
size is demoted to an ancillary signal (e.g. `GAMING_POPULATION_LANGUAGES`),
never the priority axis.

1. **New canonical field** `bibleCoverage: 'full' | 'nt' | 'portions' | 'none'`
   on every `Language` (UBS/Wycliffe Scripture-access category).
2. **Tier is derived, not authored**: `bibleCoverageToTier()` is the single
   mapping — `1=full, 2=nt, 3=portions, 4=none`. A hand-set tier that disagrees
   with `bibleCoverage` is a bug.
3. **Registry re-tiered** (155 languages, same code set — no language added or
   dropped): 133 full Bible (tier 1), 16 New Testament (tier 2), 6 Portions
   (tier 3), 0 none (tier 4, reserved for outreach expansion).
4. **i18n auto-translate priority follows Scripture**: Yoro post
   auto-translation (Tier 1+2, daily) now means "every language that has at
   least a complete New Testament" (149 languages). Tier 3 weekly; Tier 4 is the
   queue for languages whose translation is in progress.
5. **Coverage values are corrigible** — they are a seed from the UBS/Wycliffe
   categories. When a translation milestone lands (portions → NT → full), bump
   `bibleCoverage` and the tier follows automatically; corrections flow through
   the i18n actor's coverage tool. This mirrors the tsumugi coverage-tool +
   seed-then-refine pattern already used in the repo.

# Consequences

- **Doctrinal coherence**: the platform now prioritizes reaching people who have
  Scripture, and surfaces (via the empty-but-reserved tier 4) the languages that
  still lack it — turning the registry into a standing record of the Great
  Commission's remaining gap rather than a market map.
- **Larger "primary" set**: tier 1 grows from 25 → 133 (most established
  languages have a complete Bible). UI groupings keyed on `getLanguagesByTier(1)`
  / `tier <= 1` (LanguageSwitcher, PageTranslateBar) keep working; they now mean
  "languages with the full Bible".
- **Auto-translate fleet load** rises (Tier 1+2 = 149 vs old 50) but stays on
  the zero-cost on-prem Murakumo qwen3.5-4b fleet (ADR-2605215000), so no
  external-inference / cost invariant is touched.
- **No data loss**: identical 155-code set; this is a re-tiering + field
  addition, fully additive to the type.
- **Honesty boundary**: per-language coverage is asserted from UBS/Wycliffe
  Scripture-access categories and is the corrigible part of this ADR; the
  *organizing principle* (tier = Scripture access) is the durable decision.

# Alternatives Considered

- **Keep population tiers, add `bibleCoverage` as metadata only.** Rejected:
  leaves the priority axis market-driven, contradicting Sola Scriptura — the
  field would be decorative.
- **Coverage-gated membership** (drop languages with no Scripture from the
  supported set). Rejected: excludes exactly the populations the mission most
  wants to reach. Tier 4 (none/in-progress) keeps them in view as the outreach
  queue instead.
- **Separate "Scripture priority" list parallel to the tier field.** Rejected:
  two priority axes invite drift; one derived tier is Shannon-minimal.

# References

- `90-docs/adr/2605192100-etzhayyim-mission-charter.md` — Sola Scriptura / 万人祭司 / §1.16 social security for humanity
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/language/languages.ts` — re-tiered registry + `bibleCoverageToTier()` + `getLanguagesByBibleCoverage()`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/language/types.ts` — `BibleCoverage` type
- `60-apps/etzhayyim-project-i18n/CLAUDE.md` — Language Tier Strategy (Scripture-based)
- United Bible Societies — Global Scripture Access; Wycliffe Global Alliance — Scripture & Language Statistics (coverage categories: full Bible / New Testament / Portions)
