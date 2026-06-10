---
id: adr-2606101540-session-close-shionome-stock-pyramid-grounding-live-edgar-fleet-heartbeat
title: "ADR-2606101540: Session close — 潮目 stock pyramid + entity grounding + first live EDGAR ingest (kanjō) + fleet-heartbeat runner"
status: active
doc_type: adr
topic: shionome-cross-asset-capital-flow-observatory
authoritative: false
last_verified: 2026-06-10
priority: 5.0
axis: actor
weight: 0.5
depends_on:
  - adr-2606072200-shionome-cross-asset-capital-flow-observatory-r0
  - adr-2606032000-kanjo-world-public-company-financial-disclosure-kg
  - adr-2606022000-kabuto-world-public-company-supply-chain-kg
  - adr-2606073400-hokorobi-world-systemic-finance-risk-observatory
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - 90-docs/adr/2606072800-session-close-shionome-capital-flow-kotoba-wasm-fleet-cron.md
supersedes: []
superseded_by: []
---

# Context

Question that opened the session: *「https://www.visualcapitalist.com/all-of-the-worlds-money-and-markets-in-one-visualization/
と同様に いまの全世界の資本を actor として整理するのはどれぐらい設計されている?」* — then, successively:
*「このデータのベースとなる世界の実世界の actor, entity coverage は?」*, *「実際の ingest や分析も含めて
repo 全体が 生きている状態にして」*.

Answer at the time: shionome (ADR-2606072200) modeled cross-asset capital **FLOWS** (edge-primary,
どこからどこへ) but had **no stock axis** — the Visual-Capitalist "how big is everything" sizing of
each asset class against the others was unrepresentable. No actor modeled absolute asset-class
totals (M2 / bond-market size / derivatives notional / real-estate value); the entity ledgers that
DO exist (kabuto 1,719 listed cos · hokorobi 17 systemic institutions · kanjō 5 disclosed filers ·
ooyake 7,089 gov units) were not connected to any capital sizing; and the actor cohort's autonomous
loops existed but nothing ran them continuously.

# Decision (what landed — PR #1533, squash-merged 2026-06-10)

1. **Stock layer** (`:outstanding-usd`): one new snapshot metric across the three invariant homes
   (ontology `:db/allowed` · `bucketSnapshot` lexicon `:enum` · `weave.SNAPSHOT_METRICS`);
   `weave.stock_pyramid` sizes the latest stock per asset class against the grand total. Seed adds
   8 global `:representative` layers totalling 1,383 tn (derivatives notional 600 / real-estate 380
   / debt 140 / broad-money 121 / equities 115 / gold 16 / cash 8 / crypto 3). A SIZE is factual
   (like `:return-pct`), carries `no_trade_notice=true`, is never a rating/signal/target (G2/G4),
   and is never summed with flow magnitudes (usd-tn ≠ usd-bn).
2. **Entity-grounding bridge** (`methods/grounding.py`): decomposes a pyramid layer into the named
   real entities sibling ledgers already mirror — equities ← kabuto (1,719 cos; value coverage
   $46.8tn/$115tn ≈ 40.7% LOWER BOUND, count ≈ 3.1% of a `:representative` ~55k listed universe);
   disclosure DEPTH ← kanjō; systemic-institutions overlay ← hokorobi (17, 14 authoritative); plus a
   per-layer ROADMAP naming why each ungrounded layer cannot yet be entity-decomposed (e.g. the
   debt layer is a bond-market aggregate and must NOT be conflated with kanjō corporate-BS
   liabilities). Fail-open; the hermetic core never imports it.
3. **First live EDGAR ingest** (kanjō G7 gate flipped by operator instruction, 2026-06-10): 12 real
   filers (Apple/Microsoft/NVIDIA/Amazon/Alphabet/Meta/Berkshire/Broadcom/Tesla/Intel/AMD/Micron)
   via the documented offline-bridge workflow (companyfacts JSON → `data/ingest/` (gitignored) →
   offline merge). `facts.merged.kotoba.edn` (committed, 1.1MB): 183 filings / 2,484 facts (2,462
   `:authoritative`) / 15 companies → 1,631 `:synthesized` metrics + 88 aggregates;
   `EDGAR_CIK_TO_ORG` extended 2→12 (kabuto `org.corp.*` linkage); shionome grounding depth 5→15.
   kanjō tests 1,744 green. EDINET live fetch, full-universe parse, and shionome's own live
   market-data ingest remain Council-gated (untouched).
4. **Fleet-heartbeat runner** (`70-tools/scripts/fleet-heartbeat/heartbeat.sh`): beats all 11
   offline autonomous loops (shionome/kanjo/kabuto/kosatsu/keizu/danjo/watari/watatsuna/sukashi/
   ipaddress/yabai) fail-open — 11/11, each appending a verified content-addressed tx per beat.
   Size-based **log segmentation** (`LOG_ROTATE_MB`, default 16) bounds the per-beat cost: an
   over-threshold local Datom log is moved to `archives/` (segmentation NOT erasure — the heartbeat
   log is a deterministic regenerable runtime artifact; canonical state = committed seed/merged
   graphs; newest 3 segments retained). Measured: kanjō segmented at 36MB → fleet beat 9s → 2s,
   steady-state 2–6s. The runner itself does no live I/O; per-actor gates stay authoritative.
   During the session the runner ran on a 30-min in-session cron (session-only; stopped at close).

# Honest boundary

- Murakumo narration stayed DOWN all session: `~/.ollama/models` symlinks to `/Volumes/251220`
  (external disk, not attached); LiteLLM :4000 and EVO-X2 also unreachable. Narration cells
  degraded gracefully; no non-Murakumo LLM was substituted (ADR-2605215000 held). Remedy is
  physical (attach the disk) or an operator decision (re-point the symlink + fresh `gemma3:4b` pull).
- The stock pyramid's 8 layer totals are `:representative` rounded figures, not authoritative
  captures; 7 of 8 layers remain entity-ungrounded with stated reasons (the roadmap).
- The in-session heartbeat loop dies with the session; durable scheduling (fleet cron cells per
  ADR-2606072200, or /schedule cloud routine) is the operator's next step.

# Consequences

shionome answers three questions it could not before — how big is everything / who is inside each
layer / how alive is the cohort — with computed, test-pinned outputs (shionome 182 tests · kanjō
1,744 autorun tests green). First `:authoritative` live capture in the disclosure cohort. ZERO
invariant amendments; the G7 flip is recorded here as the operator act.

# Alternatives Considered

- New "world-capital-stock" actor instead of extending shionome — rejected: the bucket/snapshot
  ontology already carried the right shape; one metric + read-side views sufficed.
- Grounding the debt layer via kanjō balance-sheet liabilities — rejected as dishonest (bond-market
  outstanding ≠ corporate BS liabilities); recorded as `ungroundable-at-r0` with reason.
- Tail-only chain verification inside 11 actors' kotoba.py — rejected for scope; runner-level log
  segmentation bounds cost without touching any actor's code.

# References

- PR #1533 (squash-merged); ADR-2606072200 (in-file R1 addenda: stock layer · entity grounding)
- `20-actors/shionome/methods/{weave,grounding}.py` · `70-tools/scripts/fleet-heartbeat/heartbeat.sh`
- `20-actors/kanjo/data/facts.merged.kotoba.edn` (first live-merged authoritative graph)
