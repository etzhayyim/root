---
id: adr-2606212020-amime-energy-mesh-flow-network
title: "ADR-2606212020: amime 網目 — multi-site energy MESH flow-network (Energy Order SoS layer)"
status: proposed
doc_type: adr
topic: amime-energy-mesh
authoritative: true
last_verified: 2026-06-21
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - amime-energy-mesh-flow-network
depends_on:
  - 2606211200
  - 2606091800
related:
  - 2606172100
  - 2606212000
  - 2605261100
  - 2605265600
supersedes: []
superseded_by: []
---

# ADR-2606212020: amime 網目 — multi-site energy MESH flow-network (Energy Order SoS layer)

**Status**: proposed
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki

# Context

The Energy Order Protocol suite (ADR-2606211200: mio 澪 / tawami 撓 / okibi 燠 / toi 樋 / yudane 委 /
hikari 光) gave the org a Proof-of-Useful-Flow accounting backbone and four flexibility legs. But
its spatial model stopped at a **single site**:

- **hikari 光** (ADR-2605261100) designs ONE installation (solar + storage + grid-edge), and its
  own roadmap defers "multi-site mesh" to R2/R3.
- **mio 澪** verifies the org's aggregate Flowrate, but treats it as a scalar sum — not a
  topology.
- Nothing modelled **how ordered energy flows BETWEEN sites** across a network of
  capacity-bounded, lossy links: which paths carry the load, where transmission losses fall,
  what gets curtailed, and — critically — **which single link, if lost, strands load** (N-1).

So the system-of-systems question "where is the energy mesh brittle, and what is the
energy-flow 取 concentration?" had no answer, and kaname 要 had no `:energy` layer to consume
(ADR-2606212000).

# Decision

Introduce **amime 網目** — a clj-native R0 Tier-B actor that solves the **multi-site energy mesh
as a flow network**. The name (網目, "mesh / net-eye") is the topology it models.

**Model.**
- `SITE {:gen :load :role}` → `net = gen − load` (signed injection).
- `LINK {:from :to :capacity :loss}` — undirected; `capacity` bounds SENT kW; `delivered =
  sent · (1 − loss)`.
- **solve** (R0, deterministic single-hop transportation): each deficit pulls from adjacent
  surpluses over their links, sent bounded by remaining export AND link capacity, delivered net
  of loss; outputs served-fraction, transmission loss, curtailment, unserved, per-link flow,
  per-site import-dependence. Multi-hop routing + AC power-flow are R1+.
- **N-1 contingency**: re-solve with each link removed → the link whose loss-of-service is
  largest is the **critical chokepoint**, routed to REDUNDANCY.
- **import-dependence**: per deficit site, the fraction of import over its single most-loaded
  link (1.0 = SPOF) — the energy-flow 取 signal.

**Constitutional stance (gates, enforced in code + tests).**
- **G1 commons-not-market** — amime is a COMMONS mesh, never a market: `:amime/price` and
  `:amime/trade` are **unrepresentable** (never emitted; test-pinned). No bid/ask/clearing.
- **G2 ordered-flow-not-consumed** — it rewards delivered useful FLOW, never consumed energy —
  the mio PoUF stance (ADR-2606211200 G1).
- **G3 resilience-map-never-target-list** — chokepoints/SPOFs are a redundancy MAP, never a
  target-list; the report says so in words.
- **G4 sim-only-never-dispatches** — `:amime/dispatch` is unrepresentable; **hikari actuates
  under Council Lv7+ gate, never amime**.
- **G5 aggregate-no-person-metering** — `:amime.site/person` unrepresentable.
- **G6 kotoba-EAVT-native** · **G7 no-server-key** (no network I/O) · **G8 synthetic-seed**.

**Persistence + composition.**
- `methods/kotoba.cljc` — content-addressed append-only **mesh-resilience ledger** (commit-DAG,
  verify-chain tamper-evident); `methods/autorun.cljc` — deterministic, **idempotent-by-content**
  heartbeat (identical solve = no-op).
- `methods/emit.cljc` writes the **committed** kaname-facing `:energy` mirror
  (`out/energy-sos.kotoba.edn`): flow `:concentrates` onto loads, single-path import is a
  `:depends-on` SPOF. kaname 要 JOINs it as the `:energy` domain (ADR-2606212000).

**Empirical R0 result.** On the synthetic 6-site / 7-link seed the base mesh serves **100%** of
load (surplus 1700 kW > need 1350 kW), yet N-1 exposes **`l-wb-ct` (wind→city)** as critical —
losing it strands **+258 kW**. The SoS insight amime exists to surface: *the mesh looks healthy
at base but is fragile to a single link* → map it, route to redundancy. 11 tests / 52 assertions
green.

# Consequences

- The Energy Order suite gains its missing **inter-site flow** layer: hikari (one site) → amime
  (mesh flow) → mio (PoUF Flowrate). Chokepoints route to hikari's multi-site mesh redundancy
  (ADR-2606091800).
- kaname 要 gains a real `:energy` producer (ADR-2606212000) — the producer/consumer pair makes
  "energy as a system-of-systems domain" concrete and tested, not aspirational.
- **No charter amendment**: a new observatory/sim actor under the existing labor-liberation +
  Energy Order frame; map-not-target, sim-only, no-server-key, commons-not-market all preserved.
- R0 is single-hop + DC; the honest limits (multi-hop routing, AC power-flow, time-coupled
  storage, live-site ingest) are named in the R1 worklist, not hidden.

# Alternatives Considered

- **Extend hikari to multi-site (its R3 plan).** Rejected for separation of concerns: hikari is
  the single-site DESIGNER + the actuator; a mesh SOLVER that must stay sim-only and emit a
  cross-actor `:energy` mirror is a distinct responsibility (and amime feeds hikari's redundancy
  planning, not the reverse).
- **Put the mesh solve inside mio.** Rejected: mio is the PoUF VERIFICATION ledger (scalar
  Flowrate); a topology solver with N-1 contingency is a different shape and would overload mio's
  G1 PoUF boundary.
- **A full AC power-flow / optimal-power-flow solver at R0.** Rejected as premature: a
  transparent, dependency-free transportation flow is honest, testable, and sufficient to surface
  chokepoints and feed kaname; AC/OPF is R1+ behind real-site data (G7/G8).
- **Model it as an energy market (price-clearing).** Rejected on charter grounds: a market
  introduces price/trade — amime is a commons (G1), rewarding ordered flow, not clearing bids.

# References

- ADR-2606211200 (Energy Order Protocol suite — mio/tawami/okibi/toi/yudane/hikari)
- ADR-2606212000 (kaname 要 — :energy domain layer; the consumer of amime's mesh output)
- ADR-2606091800 (infra-robotics 3-layer substrate — hikari microgrid; redundancy target)
- ADR-2606172100 (kaname 要 — cross-domain SoS leverage synthesizer)
- ADR-2605261100 (hikari 光 — single-site energy) · ADR-2605265600 (funamori — marine renewable)
