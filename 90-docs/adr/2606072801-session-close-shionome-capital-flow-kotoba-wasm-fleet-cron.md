---
id: adr-2606072801-session-close-shionome-capital-flow-kotoba-wasm-fleet-cron
renumbered_from: "2606072800"
title: "ADR-2606072801: Session close — 潮目 (shionome) cross-asset capital-flow observatory: R0 actor + kotoba-WASM component + Murakumo-fleet cron cells"
status: active
doc_type: adr
topic: shionome-cross-asset-capital-flow-observatory
authoritative: false
last_verified: 2026-06-07
priority: 5.0
axis: actor
weight: 0.5
depends_on:
  - adr-2606072200-shionome-cross-asset-capital-flow-observatory-r0
  - adr-2606071000-intel-osint-actor-cohort-r1-and-fleet-readiness
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - 90-docs/adr/2606065000-session-close-kawaraban-news-medium.md
  - 90-docs/adr/2606063000-session-close-ooyake-world-model-reconcile-loop.md
supersedes: []
superseded_by: []
---

# Context

Question that opened the session: *「株式やコモディティ、国際、暗号資産、不動産価格の変動などから、
どこがどこに資金が流れているかを ingest, intel, analyze して social post、トレードはしない。actor を
kotoba で自律的に稼働するところまで進めて」*.

Answer at the time: there was **no cross-asset capital-flow actor**. Adjacent siblings cover other
objects — **mitooshi** forecasts (distribution-only), **kanjo** mirrors company *disclosure*,
**kanae** renders *government* fiscal flows, **watari** tracks live *physical* positions, **kabuto**
maps *supply-chain* concentration. None observes **where capital rotates between asset classes**.

A second, sharper follow-up tested the first claim: *「kotoba wasm として自律的に稼働している?
murakumo mac mini fleet で cron できているか?」* — exposing that the initial "autonomous on kotoba"
claim was true only for a **local Python loop over a local Datom file**, not a real kotoba-WASM
actor on the fleet.

# Decision

Authoritative design = **ADR-2606072200**. This is a documentation-only session closure recording
what landed (two commits on PR **#1361**, branch `feat/shionome-capital-flow`).

## Commit 1 — the R0 actor (`20-actors/shionome/`)

Cross-asset capital-flow observatory. Models the world's capital as a graph of public **buckets**
(asset-class / sector / region / theme) + observed **flows**; computes aggregate edge-primary
metrics (net flow per bucket = どこに資金が向かっているか, rotation pairs = どこからどこへ, inflow
HHI, by-asset-class / by-region, a FACTUAL risk-on/off/mixed regime) → **dry-run** social posts.

The defining invariant **トレードはしない (G2 no-trade)** is enforced in **four homes** — ontology
enum + no `:bucket/rating` attr · lexicon `noTradeNotice` const · `weave.TRADE_TOKENS` on flow/
bucket kinds · `social._guard_no_trade` on every post body — and `test_charter_invariants.py`
asserts the data homes agree. Plus the standard cohort gates (G1 no-doxxing, G3 ≥2 sources +
no-commercial-terminal, G4 edge-primary, G5 mirror, G6 Murakumo-only, G7 no-server-key, G8
outward-gated, G10 append-only, G11 sourcing-honesty).

Landed: ontology + 4 lex `com.etzhayyim.shionome.*` + 5 R0 cell scaffolds + methods
(weave/ingest/social/export/registry/analyze/kotoba/autorun) + `:representative` seed +
R1-ready 12-source registry. **153 tests green** (14 suites). `methods/autorun.py` self-drives
observe→validate→weave→analyze→dry-run-post→persist, appending a content-addressed transaction
to the append-only kotoba Datom log each heartbeat (commit-DAG, `verify_chain` OK, deterministic).

## Commit 2 — kotoba-WASM + Murakumo-fleet cron (answering the follow-up)

Honest correction: "autonomous on kotoba" was upgraded from a local Python loop to two real
kotoba-WASM artifacts, both **empirically built/verified off-fleet**:

1. **Standalone WASI component** (`20-actors/shionome/wasm/`) — componentize-py →
   `shionome-actor.wasm` (18.5 MB), `wasm-tools validate` clean, jco-transpiled + run under node
   (`regime=risk-on`, `no_trade=true`). CID
   `bafybeigk6whellozcybop4btzcrdtybd5yejjrax7tczxhapfsyya64hka` (dag-pb, T2 donated-mesh).

2. **5 Murakumo-fleet cron cells** (`20-actors/magatama/cells/shionome_*`) — `kotoba_langgraph`
   Pregel cells (the ossekai precedent), each with `trigger = { kind = "cron" }` on a real node:
   `ingest`@issachar `5 * * * *` · `flow_graph`@issachar `10 * * * *` · `rotation_weave`@dan
   `15 * * * *` · `regime_observer`@dan `20 * * * *` · `social_post`@naphtali `0 9 * * *`.
   Registered in `50-infra/murakumo/fleet.toml` + `cell_runner_main.py` (`shionome_*` glob). Pure
   logic in `shionome_core.py`, **14/14** off-fleet tests.

## Honest boundary (what is NOT done, by design)

The actual `ansible-playbook … k8s-gpu-cluster.yml` deploy onto the **physical Mac-mini fleet**, and
**live market-data ingest + live external posting**, are **operator/Council gated** (G7/G8 +
ADR-2606071000: "deploy to the fleet cannot be executed by an agent"). The reachable state —
**deploy-readiness** — is met: built, tested, cron-wired, one human gate-flip from live.

# Consequences

- A new, distinct cross-asset capital-rotation lens for the commons, with a test-pinned no-trade
  boundary that makes a robo-advisor structurally unrepresentable.
- Two kotoba-WASM runtime faces (standalone component + fleet cron cells) prove the actor can run
  as kotoba-WASM and is fleet-cron-wired — not merely a local script.
- Registries updated: root `CLAUDE.md` Tier-B row, `deps.toml` `[[adrs]]` entry,
  `90-docs/adr/README.md`, docs/graph sidecar registries.
- **ZERO invariant amendments.**

# Alternatives Considered

- **Fold into mitooshi** — rejected (realized-observation ≠ forecast; would muddy mitooshi's
  leak-free scoring).
- **Stop at the local Python loop** — rejected once the follow-up made the kotoba-WASM + fleet-cron
  bar explicit; built both runtime faces instead.

# References

- ADR-2606072200 (shionome R0 — authoritative design)
- `20-actors/shionome/` (actor) · `20-actors/shionome/wasm/` (WASI component) ·
  `20-actors/magatama/cells/shionome_*` (fleet cron cells) · `50-infra/murakumo/fleet.toml`
- PR #1361 · ADR-2606071000 (intel-cohort deploy-readiness framing)
