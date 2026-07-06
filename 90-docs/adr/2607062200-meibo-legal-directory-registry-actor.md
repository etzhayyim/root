---
id: adr-2607062200-meibo-legal-directory-registry-actor
title: "ADR-2607062200: meibo (名簿) — verified legal-institution directory registry, honestly fulfilling ADR-0016's judge/bengoshi/adr/legal-aid vision"
status: accepted
doc_type: adr
topic: meibo-actor
authoritative: true
last_verified: 2026-07-06
priority: 5.5
axis: architecture
weight: 0.50
priority_note: "New Tier-B non-profit actor: a link-registry to real licensed-professional/court/institution search tools, expanding on the legal_directory field added to saisei."
authoritative_for:
  - meibo actor design (legal-institution directory registry)
  - the honest scope of "implementing ADR-0016's judge/bengoshi/adr/legal-aid actors"
depends_on:
  - adr-2607061800-saisei-self-filing-debt-relief-actor
  - adr-2606112301-tate-legal-defense-concierge-r0
  - adr-2606112400-tate-worldwide
related: []
supersedes: []
superseded_by: []
---

# ADR-2607062200: meibo (名簿) — verified legal-institution directory registry

**Status**: accepted
**Date**: 2026-07-06
**Deciders**: Jun Kawasaki

# Context

The owner asked for a "本格実装" (full/serious implementation) of connecting people to
real bar associations, courts, licensing bodies, and administrative/judicial
scriveners — as the legitimate path in place of saisei performing document drafting
itself (declined per G2/G3/N2 — see saisei's own CLAUDE.md and the conversation that
led to ADR-2607061800). A first, small step already landed directly inside saisei
(`data/legal-directory.edn`, 10 entries across jp/us/uk/de, wired into
`filing_plan.cljc`'s `"legal_directory"` field and the live Worker's UI).

Separately, `gftdcojp`'s ADR-0016 ("legal-cluster-topology") already named this exact
gap in 2026-04-14 — four planned actors (`judge`, `bengoshi`, `adr`, `legal-aid`)
meant to cover 200K judges / 2.5M lawyers / 1M ADR cases/yr / 10M legal-aid cases/yr —
and never built any of them. The same repo-wide survey that led to ADR-2607061800
found this ADR-0016 gap; this ADR is the honest follow-through.

**The ADR-0016 numbers were never achievable by direct means and shouldn't be
repeated in a different guise.** None of the four target directories (JFBA's
ひまわりサーチ, US state bars, individual national judicial councils, etc.) publish a
bulk-exportable dataset — most are opt-in/self-reported (JFBA's own disclaimer:
"日本弁護士連合会及び弁護士会はその掲載内容について、何らの責任を負うものではありません"),
several explicitly restrict scraping in their terms of use, and the underlying
personal data (individual attorneys' practice details, disciplinary history) carries
its own data-protection weight to republish at scale without the professional body's
own participation. Attempting to scrape/mirror "2.5M lawyer records" in one session
would be neither honest (the resulting dataset would be stale and incomplete the
moment it's built) nor lawful across every jurisdiction touched.

# Decision

**`meibo` (名簿 — "roster/registry"), a new Tier-B non-profit actor**: a
**verified LINK registry** to the official search tools those institutions
already run themselves — the same pattern already proven inside saisei
(`:proc/official-forms-url`, `:dir/*` legal-directory entries), generalized
into its own actor and grown beyond saisei's 4 jurisdictions.

| Field | Value |
|---|---|
| Operating entity | etzhayyim (non-profit) |
| Tier | B |
| Depends on | none (self-contained per the actor-independence convention — see Consequences) |

## What meibo is

A jurisdiction-keyed registry of **institution-level** (never individual-record)
entries, each verified live (WebSearch/WebFetch, never guessed — the same G10
provenance discipline as tate/saisei) before being recorded:

| `:dir/kind` | Meaning | Example |
|---|---|---|
| `:bar-association` | Official attorney/solicitor register or search tool | 日弁連 ひまわりサーチ, SRA Solicitors Register, BRAK Anwaltsverzeichnis |
| `:licensed-scrivener` | Japan-specific licensed non-attorney professions (司法書士/行政書士) | 日司連しほサーチ, 日行連会員検索 |
| `:court-locator` | Official court-finder tool | uscourts.gov Federal Court Finder, HMCTS find-court-tribunal |
| `:insolvency-practitioner-register` | UK-specific licensed IP register | gov.uk find-an-insolvency-practitioner |

**R0 seed: 10 jurisdictions** (jp/us/uk/de/kr/fr/au/ca/it/es — the 4 saisei already
seeded plus 6 more, chosen to overlap tate's existing 30-jurisdiction coverage so a
future wave can wire tate's own referrals to real URLs instead of names/phone
numbers only). `coverage_report.cljc` names the remaining ~183 as an honest,
explicit worklist (tate's own pattern) — never silently claimed as covered.

## Gates (same family as tate/saisei)

- **G1 institution-level only.** No individual practitioner records, no personal
  data about specific attorneys/judges — only the OFFICIAL search tool's URL.
  Looking someone up happens on the institution's own site, under their own terms.
- **G2 non-adjudicating.** meibo never asserts a professional is competent,
  in good standing, or a good fit — it points at the authoritative place to check.
- **G10 jurisdiction/provenance honesty.** Every URL verified live before recording
  (never guessed/remembered); `coverage_report` names uncovered jurisdictions
  honestly rather than silently omitting them.

## Non-goals

- Does not ingest, cache, or republish individual professional records (bar
  numbers, disciplinary history, case dockets) — those stay on the institution's
  own site, fetched live by the visitor, under that institution's own terms
- Does not rank, recommend, or vouch for any specific professional
- Does not replace saisei's own jurisdiction-scoped `legal_directory` field (that
  stays as-is, self-contained within saisei per the actor-independence
  convention below) — meibo is the broader, standalone, independently-growing
  reference for the wider ecosystem (tate, toritsugi, future actors)

# Consequences

**Positive**

- Real, honest progress on the exact gap ADR-0016 named in 2026-04-14 and never
  built, at a scale (institution-level links, verified) that is actually
  sustainable to maintain and legally clean to publish
- Growing this to more jurisdictions is pure data entry (one EDN entry + a
  verified URL), the same low-friction growth path tate itself already proved
  across 30 jurisdictions

**Negative / limits**

- This is NOT a lawyer-matching service and NOT what "2.5M lawyer records" would
  have implied — a visitor still has to use the institution's own search tool
  themselves. That was always going to be true even in the original vendor
  vision (ADR-0016 itself never specified how 2.5M individual records would be
  kept current — attorney rolls change constantly; a live link to the source of
  truth ages far better than a stale mirror)
- 10 of ~193 jurisdictions — most of the world is a named gap, not covered

## Actor independence: why meibo doesn't become a saisei/tate code dependency

Every Tier-B actor in this monorepo is designed to be split into its own
standalone GitHub repo by `actor:publish` (ADR-2607022300) — that's why tate,
toritsugi, yobel, and saisei each carry their **own** copy of a minimal
`methods/edn.cljc` reader rather than requiring a shared library namespace.
Had saisei's `filing_plan.cljc` been changed to `(require '[meibo.methods.directory ...])`,
splitting saisei into `com-etzhayyim-saisei` would silently break the moment
`meibo`'s files aren't present in that new repo. meibo therefore stays
**self-contained** (its own `edn.cljc`, no cross-actor `require`), and the
intended way saisei/tate consume its data going forward is the same pattern
already used for every other cross-org reference in this codebase: meibo's own
public API surface (its Worker, once deployed — see Consequences) or a
duplicated/synced EDN snapshot, never a source-level dependency. Wiring saisei's
UI to link out to meibo for jurisdictions beyond saisei's own 4, and upgrading
tate's 30-jurisdiction `:juris/referrals` text into meibo-backed URLs, are both
valid follow-ups explicitly left for a later wave — not done in this ADR, to
keep this landing bounded.

# Alternatives Considered

## A. Literally attempt the ADR-0016 scale (bulk ingest 2.5M lawyers / 200K judges)

Rejected — see Context. Not achievable honestly or lawfully as a same-session
scrape, and even if attempted would be stale within months with no realistic
maintenance path, for representing something (an individual's current
disciplinary/licensing status) where staleness itself causes harm.

## B. Four separate actors (judge / bengoshi / adr / legal-aid), matching ADR-0016's original naming

Rejected for the same Shannon-optimality reasoning yobel's own ADR already used
for its 5 doctrinal rite types: the data model (jurisdiction → verified link →
kind) is identical across all four; a `:dir/kind` discriminator in one actor is
simpler than four near-identical actors with four near-identical `coverage_report`
implementations to keep in sync.

## C. Wire meibo as a direct code dependency of saisei/tate

Rejected — see the "Actor independence" section above. Breaks the moment either
actor is split into its own repo, which is the explicit, intended lifecycle for
every Tier-B actor here.

# References

- ADR-0016 (gftdcojp: legal-cluster-topology — the original, never-built
  judge/bengoshi/adr/legal-aid vision this ADR honestly fulfills at real scale)
- ADR-2607061800 (saisei — the `:proc/official-forms-url` / `legal_directory`
  pattern this ADR generalizes)
- ADR-2606112301 + 2606112400 (tate — the 30-jurisdiction `:juris/referrals`
  precedent meibo's coverage was chosen to overlap with)
- ADR-2607022300 (unified actor deploy — the per-actor `actor:publish` split
  pipeline motivating meibo's self-containment)
