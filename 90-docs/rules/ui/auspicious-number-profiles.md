# Auspicious Number Profiles for Donation and Root Surfaces

**Status**: draft companion profile table for ADR-2606290830
**Scope**: human-facing defaults only; never protocol constants, donor tiers, or obligations.

This file keeps culturally local number choices out of the ADR body. The ADR
defines the invariant; this profile table defines tunable presentation defaults.

## Core Rule

Use a profile only when the donor or reader locale is explicit or strongly
implied by the selected language/region. Unknown locale uses the neutral
fallback. Always keep custom amount entry visible.

## Neutral Fallback

| Profile | Prefer | Avoid | Use |
|---|---:|---:|---|
| neutral | 12, 18, 36, 72, 108 | none | Default when locale is unknown |

`12` is included here because it is broadly legible as a complete set without
being culturally narrow. `18`, `36`, `72`, and `108` remain etzhayyim-wide
cycle/life/wholeness defaults.

## West / United States

The US and broader Western profile should lean less on "lucky number" language
and more on familiar complete-count units: dozen, half-dozen, gross, score,
and common civic/calendar counts.

| Profile | Prefer | Soft-avoid | Notes |
|---|---:|---:|---|
| US | 7, 12, 18, 24, 36, 72, 108, 144 | 13 | `12` dozen, `24` two dozen, `36` three dozen, `72` six dozen, `144` gross; `7` is common lucky; `18/36/108` align with etzhayyim fallback |
| WEST-GENERAL | 7, 12, 24, 36, 52, 72, 108, 144 | 13 | `52` weeks/cards may be useful for yearly/cyclic UI; keep `13` as soft-avoid only |
| EU-GENERAL | 7, 12, 24, 36, 72, 108 | 13 | Prefer complete-count / calendar feel over prosperity framing |

Donation examples:

| Locale | Example presets | Rationale |
|---|---:|---|
| US | USD 12, 18, 36, 72, 144 | dozen + etzhayyim life/cycle + gross |
| US small-gift | USD 7, 12, 18, 36 | low-friction, familiar |
| WEST-GENERAL | 12, 24, 36, 72, 108 | dozen multiples; avoids overfitting to one country |

Root/apex UI examples:

- show 12 featured actors, not 10, when no layout constraint decides;
- show 24 or 36 recent records for scan-oriented pages;
- use 72 or 108 for deeper read-only samples;
- use 144 only where the UI can handle the density, because "gross" is
  culturally neat but too large for many screens.

Do not overuse `13` as an avoid rule. In Western contexts it is often unlucky,
but it is also normal in technical counts, addresses, dates, and civic data.
Avoid it only for decorative presets.

## Japan

| Profile | Prefer | Avoid | Notes |
|---|---:|---:|---|
| JP | 5, 8, 88, 108, 888 | 4, 9 | `5` go-en association; `8` opens outward; `108` cleansing/wholeness |

Donation examples: JPY 500, 800, 1,080, 8,888.

## Chinese-Language Contexts

| Profile | Prefer | Avoid | Notes |
|---|---:|---:|---|
| ZH | 8, 88, 168, 888 | 4 | Prosperity / smooth-going associations; keep tasteful and non-coercive |

Donation examples: CNY/TWD/HKD 88, 168, 888.

## Korea

| Profile | Prefer | Avoid | Notes |
|---|---:|---:|---|
| KR | 7, 8, 88, 108 | 4 | 4 is a common soft avoid; 7/8 are broadly positive |

## India

| Profile | Prefer | Avoid | Notes |
|---|---:|---:|---|
| IN | 11, 21, 51, 101, 108, 501, 1008 | none | Odd-plus-one gift convention; `108` sacred-count association |

Donation examples: INR 108, 501, 1,008.

## Jewish / Israel Contexts

| Profile | Prefer | Avoid | Notes |
|---|---:|---:|---|
| IL-JEWISH | 18, 36, 72, 108 | none | `18` chai/life; `36` double-chai |

Donation examples: ILS/USD 18, 36, 72, 108.

## Registry Shape

```edn
{:auspicious-number/v 1
 :source "90-docs/rules/ui/auspicious-number-profiles.md"
 :fallback {:numbers [12 18 36 72 108]
            :avoid []
            :notes ["neutral complete-count fallback"]}
 :profiles
 {:US {:numbers [7 12 18 24 36 72 108 144]
       :avoid [13]
       :avoid-strength :soft
       :notes ["dozen" "two-dozen" "gross" "common lucky seven"]}
  :WEST-GENERAL {:numbers [7 12 24 36 52 72 108 144]
                 :avoid [13]
                 :avoid-strength :soft
                 :notes ["dozen-family" "calendar/card cycles"]}
  :JP {:numbers [5 8 88 108 888]
       :avoid [4 9]
       :avoid-strength :default}
  :ZH {:numbers [8 88 168 888]
       :avoid [4]
       :avoid-strength :default}
  :KR {:numbers [7 8 88 108]
       :avoid [4]
       :avoid-strength :soft}
  :IN {:numbers [11 21 51 101 108 501 1008]
       :avoid []
       :avoid-strength :none}
  :IL-JEWISH {:numbers [18 36 72 108]
              :avoid []
              :avoid-strength :none}}}
```
