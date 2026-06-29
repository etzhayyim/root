---
id: adr-2606290830-cultural-auspicious-number-donation-and-root-design
title: "ADR-2606290830: Cultural auspicious-number defaults for donation and root surfaces"
status: proposed
doc_type: adr
topic: cultural-auspicious-number-donation-and-root-design
authoritative: true
last_verified: 2026-06-29
priority: 5.5
axis: experience
weight: 0.55
priority_note: "Donation and apex/root surfaces should feel naturally auspicious without creating donor tiers, pressure, numerology-as-law, or cross-cultural mistakes. Amount presets, display order, route defaults, and seed examples may use culturally local auspicious numbers when the locale is known; otherwise use neutral dozen-family / 18 / 36 / 72 / 108 style defaults. This is presentation and defaulting only; any amount remains valid."
authoritative_for:
  - donation amount preset generation by locale/culture
  - root/apex public-surface numeric defaults and display ordering
  - culturally scoped auspicious-number registry shape
  - anti-coercion and anti-ranking rules for lucky-number UX
depends_on:
  - 2605192115
  - 2605192130
  - 2606012100
  - 2606111700
  - 2606111800
  - 2606112200
related:
  - 2605170900
  - 2606231808
  - 2606261114
supersedes: []
superseded_by: []
companion_profiles:
  - 90-docs/rules/ui/auspicious-number-profiles.md
---

# ADR-2606290830: Cultural auspicious-number defaults for donation and root surfaces

**Status**: proposed
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki; Council Lv6+ for production rollout

# Context

The founder asked that etzhayyim's donation and root surfaces be designed so
they are "縁起が良い" by default, and that the design adapt by country and culture.
This belongs in the ADR layer because donation UX touches constitutional
funding doctrine: etzhayyim is donation-only, ad-free, anti-class, no donor
leaderboard, no paid priority, and no pressure mechanics.

Numbers are culturally meaningful, but they are not universal. A number that
feels auspicious in one locale can be neutral or unlucky in another. The design
therefore must be:

- local when locale/culture is known,
- neutral when it is not,
- optional for the donor,
- never a status tier,
- never a gate to benefits,
- never presented as religious obligation or prediction.

# Decision

## 1. Auspicious numbers are presentation defaults, not doctrine

Donation presets, route examples, rkeys, example IDs, and visible root/apex
ordering MAY use auspicious numbers. They MUST remain defaults only.

- A donor may give any amount, including non-auspicious amounts.
- No preset may create a "better donor" class.
- No receipt, profile, rank, governance weight, or member benefit may depend on
  choosing an auspicious preset.
- No UI may imply that the number causes merit, protection, prosperity, or
  priority.

This preserves ADR-2605192115 donation-only / no-ads and ADR-2606112200
no-score-of-soul.

## 2. Locale-scoped preset registry

Donation UI and machine-readable policy SHOULD expose a small registry. The
maintained cultural profile table lives outside this ADR at
`90-docs/rules/ui/auspicious-number-profiles.md`, so country/culture tuning can
evolve without re-opening the doctrine. A compact projection looks like:

```edn
{:auspicious-number/v 1
 :scope :donation-defaults
 :profile-source "90-docs/rules/ui/auspicious-number-profiles.md"
 :fallback {:numbers [12 18 36 72 108]
            :avoid []
            :rationale "neutral complete-count + etzhayyim cycle/life defaults"}
 :locales
 {:JP {:numbers [5 8 88 108 888]
       :avoid [4 9]
       :notes ["5 yen / go-en association" "8 opens outward" "108 as wholeness/cleansing"]}
  :ZH {:numbers [8 88 168 888]
       :avoid [4]
       :notes ["8 prosperity association" "168 as smooth-going/prosperity sequence"]}
  :KR {:numbers [7 8 88 108]
       :avoid [4]
       :notes ["7/8 common lucky associations" "4 avoided in Sino-Korean contexts"]}
  :IN {:numbers [11 21 51 101 108]
       :avoid []
       :notes ["odd-plus-one gift convention" "108 sacred-count association"]}
  :IL-JEWISH {:numbers [18 36 72 108]
              :avoid []
              :notes ["18 chai/life" "36 double-chai / lamed-vav association"]}
  :US {:numbers [7 12 18 24 36 72 108 144]
       :avoid [13]
       :avoid-strength :soft
       :notes ["7 common lucky association" "12 dozen" "24 two-dozen" "144 gross"]}
  :WEST-GENERAL {:numbers [7 12 24 36 52 72 108 144]
                 :avoid [13]
                 :avoid-strength :soft
                 :notes ["dozen-family" "calendar/card cycles" "gross"]}}}
```

The registry is not a theological truth table. It is an operator-maintained
presentation registry, versioned, cited, and reviewable. If a locale is
unknown, use `:fallback`, not the operator's home culture.

## 3. Currency-aware amount shaping

The UI MUST convert number choice into reasonable local-currency amounts rather
than blindly copying the same nominal value everywhere.

Rules:

1. Choose 3 to 5 presets per locale.
2. Preserve the auspicious suffix or structure where possible.
3. Keep at least one low-friction small gift.
4. Never hide a custom amount field.
5. For crypto, show both human amount and approximate fiat value; do not
   encourage dust or unsafe transfers.

Examples:

| Locale | Example fiat presets | Notes |
|---|---:|---|
| JP | JPY 500, 800, 1,080, 8,888 | `5`, `8`, `108`, `8888`; avoid defaulting to `4` or `9` endings |
| ZH | CNY 88, 168, 888 | `8` and `168`; avoid `4` endings |
| US | USD 12, 18, 36, 72, 144 | dozen / three-dozen / six-dozen / gross, plus etzhayyim fallback |
| IN | INR 108, 501, 1,008 | `108`, `...1` gift convention |
| IL-JEWISH | ILS 18, 36, 72, 108 | chai/double-chai sequence |

These are examples, not hard-coded requirements. Production amounts should be
bounded by fee economics, local purchasing power, and donor accessibility.

## 4. Root/apex numeric defaults

The root/apex surface (`etzhayyim.com`, `/donate`, `/.well-known/donation.json`,
`/sos`, and future root pages) SHOULD use auspicious numbers for low-stakes
presentation defaults:

- card counts, sample rows, default page sizes, and example limits SHOULD prefer
  `7`, `8`, `18`, `36`, `72`, or `108` over arbitrary `10`/`20` when no
  technical constraint decides otherwise;
- Japanese-facing root surfaces SHOULD prefer `8`, `88`, `108` and avoid `4` or
  `9` as decorative counts;
- Chinese-facing surfaces SHOULD prefer `8`, `88`, `168`, `888` and avoid `4`;
- US and broader Western surfaces SHOULD prefer complete-count units such as
  `12`, `24`, `36`, `72`, and `144` (dozen, two-dozen, three-dozen, six-dozen,
  gross), with `7` only as a light lucky-number accent;
- Jewish-facing surfaces SHOULD prefer `18`, `36`, `72`;
- Indian-facing surfaces SHOULD prefer `11`, `21`, `51`, `101`, `108`;
- protocol constants, security thresholds, quorum rules, tithe rate, BPS math,
  pagination safety caps, gas limits, and storage limits MUST NOT be changed for
  auspiciousness.

This ADR is about human-facing defaults. Engineering constraints remain
engineering constraints.

## 5. Selection algorithm

When rendering donation or root defaults:

1. Resolve `locale` from explicit user setting first.
2. If absent, use browser/app locale only for presentation; do not store it as
   donor identity.
3. Select the nearest supported cultural profile.
4. Filter out numbers listed in `:avoid`.
5. Produce 3 to 5 presets within the allowed min/max for the rail.
6. Always include custom amount / custom view controls.
7. Log only aggregate usage; no per-donor numerology profile.

## 6. Invariants

| Gate | Rule |
|---|---|
| G1 optional | Auspicious presets are selectable defaults only; custom input is always available. |
| G2 anti-class | No donor tier, leaderboard, badge, or priority may be derived from a number choice. |
| G3 anti-coercion | Text must not imply spiritual penalty, obligation, or destiny. |
| G4 locale humility | Unknown locale uses neutral fallback; never assume Japanese defaults globally. |
| G5 privacy | Locale/culture preference is presentation state, not donor identity. |
| G6 engineering supremacy | Security, quorum, tithe, and protocol constants are never altered for numerology. |
| G7 cultural review | Adding or changing a cultural profile is a Tier-2 content parameter with source/rationale notes. |

# Consequences

Positive:

- Donation and root surfaces can feel more natural, respectful, and locally
  auspicious without changing the donation doctrine.
- The same `/donate` page can offer culturally resonant presets while remaining
  universal and custom-amount friendly.
- The design avoids accidental unlucky defaults such as Japanese or Chinese `4`
  endings in decorative UI.

Risks:

- Cultural tables can become caricature if treated as fixed truth. Mitigation:
  notes + reviewable registry + fallback humility.
- Lucky-number defaults could be misread as pressure. Mitigation: custom amount
  always visible; no benefit language; no leaderboard.
- Engineering teams may be tempted to use auspicious numbers for protocol
  constants. Mitigation: G6 hard boundary.

# Alternatives Considered

1. **One global etzhayyim lucky sequence.** Rejected: it would impose one culture
   on all donors and fail the founder's "国, 文化ごとに" requirement.
2. **No auspicious numbers.** Rejected: misses a low-cost way to make the
   donation/root experience warmer and more culturally literate.
3. **Auspicious numbers as mandatory donation amounts.** Rejected: coercive,
   anti-class, and incompatible with donation-only doctrine.
4. **Use locale to permanently profile donors.** Rejected: unnecessary and
   inconsistent with anti-surveillance posture.

# References

- ADR-2605192115 — non-profit / donation-only / no-ads
- ADR-2605192130 — tithe redistribution; rates remain engineering/governance parameters, not numerology
- ADR-2606012100 — donation-funded operation + in-kind compute donation
- ADR-2606111700 — public sponsor/donation solicitation surfaces
- ADR-2606111800 — donation-media expansion
- ADR-2606112200 — no-score-of-soul doctrine
- `DONATE.md`
- `/.well-known/donation.json`
- `90-docs/rules/ui/auspicious-number-profiles.md`
