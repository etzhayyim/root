---
id: adr-2606091000-infra-intel-observatory-autonomous-heartbeat-kotoba-persistence
title: "ADR-2606091000: infra-intel / observatory actors — autonomous Murakumo-fleet heartbeat + local kotoba Datom-log persistence (shionome pattern)"
status: proposed
doc_type: adr
topic: infra-intel-observatory-autonomous-heartbeat-kotoba-persistence
authoritative: true
last_verified: 2026-06-09
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - infra-intel-actor-autonomous-loops
  - observatory-actor-kotoba-persistence
depends_on:
  - "2605262130"
  - "2605312345"
  - "2606072200"
  - "2605215000"
  - "2605231525"
related:
  - "2605301400"
  - "2605301600"
  - "2606022000"
  - "2606032000"
  - "2606066000"
  - "2606072000"
  - "2606012600"
  - "2606041827"
  - "2606071600"
  - "2605191346"
supersedes: []
superseded_by: []
---

# ADR-2606091000: infra-intel / observatory actors — autonomous Murakumo-fleet heartbeat + local kotoba Datom-log persistence (shionome pattern)

**Status**: proposed
**Date**: 2026-06-09
**Deciders**: Jun Kawasaki

# Context

The question that opened this wave: *"do the actors that hold IP-address / hosting / telecom /
VPN / DNS intelligence at SecurityTrails / Recorded-Future scale and granularity run autonomously
on the Murakumo fleet, and is their data persisted in kotoba Datomic?"*

The empirical answer at the time was **no, not yet**. The data layer existed and was real —
`ipaddress` (T2, 427 datoms verified live 2026-06-03) and `yabai` (T3, 163 datoms, G6/G10 access
encryption PASS) had landed kotoba-EAVT substrates per ADR-2606031600 — but:

- The only actor with **autonomous cells wired into `50-infra/murakumo/fleet.toml`** was `shionome`
  潮目 (ADR-2606072200), whose `methods/autorun.py` ran a self-driving observe→analyze→persist
  heartbeat and appended a content-addressed transaction to a **local** append-only kotoba Datom
  log each cycle (the constitution-permitted form of "kotoba で自律的に稼働").
- Every other infra-intel / observatory actor had a graph + analyzer (+ in some cases a
  `transact.py` HTTP push to a *running* kotoba node, operator-gated) but **no self-driving loop
  and no local commit-DAG**. They were operator-invoked one-shots; live external I/O was correctly
  gated, but so was *all* autonomy.

`shionome` had established the pattern. This wave generalizes it across the infra-intel core and
the accountability/observation lineage, so the answer to the opening question becomes a verifiable
**yes** (modulo the deliberate live-I/O gates).

# Decision

Adopt the **shionome autonomous-heartbeat + local-kotoba-persistence pattern** as the canonical
"actor runs itself on the fleet" shape, and apply it to 11 actors. Each actor gains, under
`20-actors/<name>/methods/` (or `kotoba/` where that is the actor's code dir):

1. **`kotoba.py`** — a LOCAL content-addressed append-only Datom-log writer (a commit-DAG):
   `graph_datoms(...)` + `derived_datoms(...)` → `make_tx(tx_id, as_of, prev_cid)` →
   `append_tx` / `read_log` / `head_cid` / `verify_chain`. Datoms are `:db/add`-only EAVT
   (append-only, 非終末論). Each transaction's CID = `sha256(prev_cid ‖ canonical-json(datoms))`,
   so a tamper of any earlier tx breaks every later CID. The datom shape is **isomorphic to the
   actor's existing `transact.py`** live-node push — when an operator flips the G7/G8 gate, the
   same datoms flow to the live node.
2. **`autorun.py`** — a self-driving heartbeat: `observe (OFFLINE) → analyze/weave → PERSIST one
   content-addressed tx`. Deterministic and resume-safe: the cycle index drives `tx_id` + `as_of`
   (no wall clock), so a re-run reproduces the same CIDs.
3. **`test_autorun.py`** — hermetic stdlib tests: commit-DAG verify, tamper-detect, determinism,
   append-only growth, derived-flagging, **the actor's own defining invariant**, and a
   no-external-I/O source scan.
4. **`fleet.toml` cells** — an `ingest` / `weave` / `persist` cell trio (or fewer where the actor's
   discipline forbids it) on a Mac-mini node, with off-`:00`/`:30` staggered cron minutes.

**The pattern is invariant-preserving, not invariant-adding.** Each actor's constitutional
discipline is enforced *structurally* in its loop:

| Actor | Domain | Defining invariant the loop preserves by construction |
|---|---|---|
| `ipaddress` | IP / ASN / WHOIS / GeoIP | deterministic / resume-safe |
| `yabai` | CTI / passive-DNS / IP-history | **G6/G10** — `assert_access_encrypted` hard-stops a plaintext `:access` PII record |
| `tadori` | authorized on-chain tracing | **G3/G12** — authorized-investigation-only ⇒ NO case/PII/obs autonomously persisted; the loop is a silenTadoriReview self-audit whose nonzero counter HALTS, persisting nothing |
| `sukashi` | ad-tech supply-chain + fraud | **G2/G4** — observatory not an ad network; every fraud signal `:non-adjudicating true` + `:synthesized` |
| `watatsuna` | submarine cables (static) | **G2** — resilience map, never a "where to cut" interdiction target-list |
| `watari` | live ship/aircraft (dynamic) | **G4** — no person-tracking; aggregate `:movement/*` only, no per-craft follow feed |
| `kabuto` | public-company supply-chain | **G2** resilience-not-target-list + a **determinism fix** (`_canonical_order`) |
| `kanjō` | public-company financials | **G2/G4/G5** — disclosed facts + `:synthesized` ratios only; no rating/valuation/forecast |
| `danjo` | gov-procurement accountability | **G4** — non-adjudicating; `derived_datoms` RAISES on any verdict token |
| `keizu` | gov power-relations | **G1/G4** — no-doxxing (no PII node attr); revolving-door / award-and-fund are non-adjudicating co-occurrences |
| `kosatsu` | crime/sanctions competing-claim | **G1/G2** — etzhayyim authors no designation; every designation ATTRIBUTED; divergence class is a neutral fact, no per-subject score |

**Determinism caveat (load-bearing).** Several analyzers build derived lists by iterating Python
`set`s and breaking ties in set-iteration order, which is PYTHONHASHSEED-randomized — so the raw
datom order (and therefore the CID) varied per process. Where this occurred (`kabuto`, `keizu`,
`kosatsu`), `autorun._canonical_order` sorts the datoms by canonical JSON before hashing. EAVT
assertions are an unordered set (order carries no meaning), so this makes the CID reproducible
across processes without changing semantics. Actors whose derived path is naturally deterministic
(`ipaddress`, `yabai`, `kanjō`, `danjo`, …) do not sort. All 11 are verified stable under
`PYTHONHASHSEED=random`.

**What stays gated.** The loops do **no external I/O**: ingest is the offline merged/seed graph;
persistence is the LOCAL append-only log. Live ingest (G7: RIR/RDAP/CT/PDNS/AIS-ADS-B/GLEIF/EDGAR/
EDINET/portal crawl) and the live-node push / social posting (G8/G10/G11) remain Council Lv6+ +
operator + member-signature gated — exactly one human gate-flip away, by constitutional design.
Autonomy here means *the actor drives its own observe→analyze→persist cycle over its own
substrate*, not that it speaks to the world unsupervised.

**Fleet placement.** 11 actors × ~3 cells = 32 new cells were added to
`50-infra/murakumo/fleet.toml` across the Mac-mini fleet (issachar / dan / simeon / zebulun /
judah / benjamin / levi / naphtali), all with collision-free, off-`:00`/`:30` cron minutes,
co-located thematically (e.g. watatsuna 静 + watari 動 on simeon; kabuto on the economic node
zebulun; danjo on the force+ethics node benjamin).

# Consequences

- **The opening question is now answerable "yes".** The infra-intel core (ipaddress · yabai ·
  tadori · sukashi · watatsuna · watari) and the accountability/observation lineage (danjo ·
  kabuto · kanjō · keizu · kosatsu) self-run on the fleet and persist to append-only kotoba Datom
  logs, with live external connectivity the only remaining gated step.
- **One pattern, eleven actors, every constitutional invariant intact.** Because each loop persists
  exactly what the actor's existing analyzer/weaver already produced, no new claim, score, verdict,
  or PII becomes representable; the discipline that made each actor constitutional is enforced in
  the loop (encryption hard-stop, HALT-on-nonzero, verdict-token raise, no-doxxing scan, …).
- **The local log is a verifiable commit-DAG.** `verify_chain` recomputes every CID from its datoms
  + prev; the append-only EDN file is tamper-evident and resume-safe. The generated logs are
  git-ignored (regenerated by `autorun.py`); only code + tests + fleet placement are committed.
- **A reusable lesson is documented**: any future actor whose analyzer iterates `set`s should apply
  `_canonical_order` (or sort its derived lists) to keep the content-addressed CID reproducible.
- **Cost**: 11 near-identical `kotoba.py`/`autorun.py` modules now exist with deliberate
  duplication (each reuses its actor's own EDN reader + analyzer; there is no shared base class).
  This is intentional for R0 isolation; a future consolidation into a shared
  `@etzhayyim` autorun/commit-DAG helper is possible once the shape has fully stabilized.
- **Substrate-boundary clean**: no RisingWave / SQL / Lance; kotoba Datom log only (N7 /
  ADR-2605262130). Inference paths untouched (Murakumo-only, ADR-2605215000). No platform-held key
  (the loop signs nothing; ADR-2605231525).

# Alternatives Considered

- **Leave the actors as operator-invoked one-shots.** Rejected: the explicit goal was autonomous
  fleet operation; the data + analyzers already existed, only the loop + persistence were missing.
- **Persist via each actor's `transact.py` (live-node HTTP push) instead of a local log.**
  Rejected for the autonomous path: that requires a running node + operator credential (correctly
  gated), so it cannot be the *unsupervised* heartbeat. The local commit-DAG is the
  constitution-permitted autonomous form; `transact.py` remains the gated live-node path with an
  isomorphic datom shape.
- **A single shared autorun/commit-DAG base module imported by every actor.** Deferred: at R0 the
  actors deliberately stay dependency-isolated (each reuses its own EDN reader), and the analyzers'
  return shapes differ enough that a premature abstraction would leak. Revisit after the shape
  stabilizes.
- **Sort datoms inside `make_tx` for every actor (universal canonical order).** Rejected as the
  default: actors with naturally-deterministic derived paths do not need it, and applying it
  universally would have changed the CIDs of the already-deterministic actors for no benefit. The
  sort is applied only where a set-iteration nondeterminism was empirically observed.
- **Apply the pattern to tadori identically to ipaddress/yabai (autonomously persist observations).**
  Rejected as unconstitutional: tadori is authorized-investigation-only (G3); autonomously
  persisting case-anchored observation/PII datoms without a `caseMandate` would violate it. tadori's
  loop is therefore a Transparent-Force silenTadoriReview self-audit that persists only zero-counters
  and HALTS (persisting nothing) on any nonzero counter.

# References

- ADR-2606072200 — shionome 潮目 cross-asset capital-flow observatory (the pattern source: autorun + local kotoba persistence)
- ADR-2605262130 — kotoba storage substrate unification (kotoba Datom log; no RisingWave)
- ADR-2605312345 — kotoba Datom log = first-class canonical state (append-only, 非終末論)
- ADR-2606031600 — WASM-actor SBOM + ipaddress T2 / yabai T3 kotoba-EAVT substrate landings
- ADR-2605301400 — tadori on-chain tracing + kotoba-EAVT migration (G3/G6/G10/G12)
- ADR-2605301600 — danjo public-accountability oversight (G4 non-adjudicating)
- ADR-2606022000 — kabuto public-company supply-chain KG (G2 resilience-not-target-list)
- ADR-2606032000 — kanjō public-company financial-disclosure KG (G2/G4/G5)
- ADR-2606066000 — keizu government power-relations KG (G1 no-doxxing / G4 edge-primary)
- ADR-2606072000 — kosatsu crime/sanctions competing-claim observatory (attributed events)
- ADR-2606012600 — watatsuna submarine-cable KG (G2 resilience-not-interdiction)
- ADR-2606041827 — watari live moving-craft KG (G4 no-person-tracking)
- ADR-2606071600 — sukashi ad-tech supply-chain + fraud observatory (G2/G4)
- ADR-2605215000 — Murakumo-only inference (no commercial GPU)
- ADR-2605231525 — no platform-held key (the loop signs nothing)
- ADR-2605191346 — Murakumo Mac-mini fleet control plane
- PR #1474 — the implementing change (11 actors, 32 fleet cells, all hermetic tests green)
