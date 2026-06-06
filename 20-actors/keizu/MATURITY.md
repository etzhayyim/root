# 系図 (keizu) — Maturity

**ADR**: 2606066000 · **Status**: 🟡 R0 (design + offline analyzer + dry-run) · **Updated**: 2026-06-06

## Stage ladder

| Stage | Scope | Gate | State |
|---|---|---|---|
| **R0** | ontology + 4 lexicons + `:representative` global seed + analyzer (weave/concentration/social/ingest) + 5 cell scaffolds (`.solve()` raise) + tests | ADR-2606066000 (PROPOSED) | ✅ landed |
| R1 | ingest + committee_graph + money_graph build kotoba EAVT datoms over **offline** public-source batches; no live posting | Council Lv6+ ≥3 per cell | ⏳ |
| R2 | +relation_weave aggregate concentration on live read-path; first dry-run networkPosts reviewed | Council Lv6+ ≥4 + 30-day public comment | ⏳ |
| R3 | +social_post live publication under 1 SBT = 1 vote + member signature; live public-source ingest | Council Lv7+ + operator | ⏳ |

## R0 evidence

- **Tests**: `./run_tests.sh` green — **90 tests** across weave (19) / social (7) / ingest (9) / charter-invariants (27) / analyze (5) / lexicons (5) / consistency (6) / cells (12). The charter-invariant suite parses all THREE homes of each structural gate (ontology `:db/allowed`/closed-vocab + lexicon `:const`/`:enum` + seed values) and asserts they agree, AND drift-locks lexicon enum ⊆/⊇ ontology closed vocab **both directions** (rel-kinds, money-kinds, sourcing-grades, post-status).
- **Analyzer** (`analyze.py` over the seed: 18 public role/organ nodes / 3 committees / 15 rels / 6 money / 3 statements): committee cross-organ concentration, 1 cross-committee co-membership seat, money HHI ≈ 0.96 **by payee + by payer (jp-meti top disburser)**, 1 revolving-door chain, 2 dry-run mirror posts.
- **Registration**: `did:web:etzhayyim.com:actor:keizu` in `tier-b-actors.gen.ts` + `actor-profile-seed.kotoba.edn`.

## Invariant coverage (structural, 3 places each)

| Gate | ontology | lexicon | python | test |
|---|---|---|---|---|
| G1 public-role-only | `:node/scope :db/allowed` | members `:enum` | `validate_node` | `test_charter_invariants`, `test_weave` |
| G2 non-adjudicating | rel/money `:db/allowed` + notice `[true]` | `:enum` no-verdict + `:const true` | `validate_rel`/`validate_money` | `test_weave`, `test_ingest` |
| G3 ≥2 sources | `:rel/:money/sources` doc | `:minLength 2` | `validate_*` | `test_weave`, `test_social` |
| G4 edge-primary | no `:node/power-score` attr | — | `validate_node` raise | `test_weave`, `test_charter_invariants` |
| G7 no-server-key | `:post/server-held-key [false]` | `:const false` | `social._post` / cell | `test_social`, `cells` |
| G8 outward-gated | `:post/status [:dry-run]` | `:const "dry-run"` | `build_live`/`ingest_live`/`.solve()` | `test_social`, `test_ingest`, `cells` |

## Known R0 limits (honest)

- The seed is bounded `:representative` (public seats/organs, rounded figures), **not** a live authoritative capture; nodes are public roles, never named private individuals.
- No live public-source ingest (官報 / 政治資金収支報告書 / 調達ポータル / Federal Register / USAspending / TED / OECD) — G8-gated.
- No live social posting — G7/G8-gated (member signature + Council Lv6+/Lv7+).
- LLM narration (G6) is not yet wired; the analyzer is deterministic.
- Cells `.solve()` raise; only the coded state machines run.

## Next maturity steps (loop targets)

- ✅ ~~lexicon enum ⊆ ontology closed vocab drift-lock (both directions)~~ (iter 2).
- ✅ ~~payer-side money concentration (HHI by payer)~~ (iter 2).
- Add a `bridge.py` that maps danjo discrepancy observations + kanae fiscal edges into keizu `:rel`/`:money` (cross-actor compose), tested on real sibling outputs.
- Add appointment-tenure weighting to the relation graph (G10 as-of windows) + a betweenness/cross-organ centrality metric (still edge-primary, aggregate-first).
- Funding→committee proximity: surface a payer that both funds a party AND has a seat on a committee the party influences (multi-hop, aggregate, non-adjudicating).
- MIGRATION-NOTES for any legacy gov-relation surface keizu supersedes.
