# 20-actors/shinka/cells — Shinka self-evolution engine (CLAUDE.md)

## Identity

- **Engine**: `shinka_engine` — the Shinka self-evolution engine (Loop A + Loop B + flywheel).
- **DID**: shares `did:web:shinka.etzhayyim.com` with the actor's social-evolution scheduler (`../actor-manifest.jsonld`).
- **ADR**: ADR-2606142200 (`90-docs/adr/2606142200-shinka-self-evolution-engine.md`, proposed).
- **External basis**: DeepMind co-scientist (generate→debate→evolve, Elo tournament) + Robin (Nature 2026, hypothesis→experiment→analyse→update) + MIT TLT (arXiv 2511.16665, Tracks B/E).
- **Status**: S0 + S1 — engine + research-Track-A eval harness implemented; **150 pure-logic tests green**; LLM-free deterministic kernel + typed Murakumo/fleet hooks. NOT operationally activated (no live Murakumo wiring, EVO-X2 offline, no registry flip, no live kotoba transact — all operator/leash-gated).

## What this is (and is not)

`shinka_engine` evolves **actors / cells / code / hypotheses** (capability) and **the Maxwell weight** (weight) on the murakumo fleet. It is a **SIBLING** of the existing shinka social-evolution scheduler (which evolves social posting cadence) — same DID, different target.

It is **NOT** a frontier-beating chase: the thesis is `frontier-class = small weight × fleet test-time compute × tournament/verify × Datom-log retrieval → distilled back`. The baien edge invariant (ADR-2605241900, frontier-beating non-target) is untouched.

## Architecture

```
            Loop A — capability (co-scientist)                  Loop B — weight (Robin/RSi)
  propose → reflect → cluster → rank(Elo) → recombine → synthesize    hypothesis → experiment → analyse → update
     │  (FleetSampler best-of-N)              │ PR draft (no auto-merge)    collect → gate → train(EVO-X2) → eval → deploy
     └────────────── kotoba commit-DAG (:db/add) ──────────────┘            gate: ≥250 steps OR ≥+5pp
                          ▲ corpus_candidates (dry-run flywheel) ───────────────┘
                ShinkaOrchestrator (Supervisor, ibuki beat cycle):
       replay → perceive → decide(Loop A) → flywheel → maybe_train(Loop B) → narrate(Murakumo) → checkpoint → act
```

## Co-scientist agent → cell mapping

| Co-scientist | Cell / node | Function |
|---|---|---|
| Supervisor | `ShinkaOrchestrator.beat` | ibuki beat cycle; drives both loops + flywheel |
| Generation | `node_propose` | candidates; bodies via FleetSampler best-of-N (Track A) |
| Reflection | `node_reflect` | Charter G1-G8 pre-scan (reuses charter_rider.scan) + review score |
| Proximity | `node_cluster` | dedup/diversity, keep best per cluster |
| Ranking | `node_rank` | Elo pairwise debate (Murakumo hook, fail-open kernel) |
| Evolution | `node_recombine` | merge top-2 Elo into a recombinant (re-scanned) |
| Meta-review | `node_synthesize` | PR draft (never auto-merge) + dry-run corpus feed |

## Invariants (enforced in code + tests)

- **I1 append-only** — every fact is a `:db/add` datom; `cell._datom` and the sink refuse `:db/retract`. Rejections are evidence, not deletions. Commit-DAG is tamper-evident (`expected_parent` chaining).
- **I2 no autonomous merge** — `synthesize` emits a PR draft (`member_signed/auto_merge` False); committable ONLY with a member CACAO capability (ADR-2606111400). The engine presents, never signs.
- **I3 Murakumo-only** — all inference resolves to the fleet; every hook fails OPEN to the deterministic kernel (never a commercial GPU / vendor call).

## Modules

| Module | Role | Tests |
|---|---|---|
| `cell.py` | Loop A: ShinkaEvolutionCell + 6 nodes + Elo | 24 |
| `maxwell_rsi.py` | Loop B: DeployGate, Robin loop, flywheel_ingest | 29 |
| `orchestrator.py` | Supervisor beat cycle (ibuki), replay/resume | 23 |
| `fleet_sampler.py` | Track A: fleet best-of-N + Elo, pass@k | 20 |
| `kotoba_sink.py` | append-only commit-DAG (InMemory + KotobaBridge) | 20 |
| `bench_harness.py` | Track A: pass@k vs k standing eval (S1) | 16 |
| `test_flywheel_e2e.py` | Loop A → Loop B coupling | 6 |
| `test_fleet_wiring.py` | FleetSampler ↔ Loop A propose | 12 |

## Research tracks (ADR §Research Program)

A fleet test-time compute ✅ (fleet_sampler + bench_harness) · B adaptive-drafter speculative (TLT) ⏳ · C MatFormer E2B/E4B ⏳ · D Datom-log RAG ⏳ · E verifier-grounded RL (+TLT rollout) ⏳ · F distillation flywheel ⏳ · G fleet quantization ⏳.

## Build & test

```bash
cd 20-actors/shinka/cells
for t in test_cell test_maxwell_rsi test_flywheel_e2e test_orchestrator \
         test_fleet_sampler test_fleet_wiring test_kotoba_sink test_bench_harness; do
  python3 shinka_engine/$t.py
done
# pure-stdlib; no pytest/langgraph required (langgraph used if present, else sequential driver)
```

## Related files

- `90-docs/adr/2606142200-shinka-self-evolution-engine.md` — master ADR
- `90-docs/adr/2606061000-maxwell-default-llm-weight.md` — Maxwell weight (Loop B target)
- `90-docs/baien/maxwell-models.jsonl` — corpus/weight provenance (125/1000)
- `70-tools/scripts/maxwell/{collect_corpus,gate_candidates}.py` — upstream RSi pipeline
- `50-infra/murakumo/fleet.edn` — fleet roster (9 worker nodes + judah gateway)
- `../actor-manifest.jsonld` — shinka social-evolution scheduler (sibling)
- `20-actors/ibuki/` — beat-cycle + commit-DAG + leash pattern this reuses
