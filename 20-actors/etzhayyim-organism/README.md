# etzhayyim-organism

**Religious-corp artificial-organism daemon.** CNS (中枢神経) for the monorepo
treated as a living body per `README.md § "As Artificial Organism Ecosystem"`
and ADR-2605192100 (mission charter).

| Field | Value |
|---|---|
| Constitutional prior | ADR-2605192100 §1 (10 invariants) |
| Observation surface  | `_observations/*-cycle-NN.md` (variational posterior) |
| Cadence              | daily (`ETZ_TICK_INTERVAL=86400`, ADR-2605220810 cycle 18 Option C) |
| Commits              | **no** — daemon writes, operator commits (ADR-2605192100 §1.3) |
| License              | Apache 2.0 + etzhayyim Charter Compliance Rider v2.0 |
| Organism axis        | Axis 4 — Active Inference (能動推論 / 縁起) |

## What it does

Every tick:

1. **Reads** repo state via 10 axis-sensors (one per constitutional invariant).
2. **Scores** each axis 0..10 against the prior.
3. **Diffs** vs the most recent `_observations/*-cycle-NN.md`.
4. **Picks** the lowest-score × highest-leverage axis as the next-action target.
5. **Emits** a new `_observations/YYMMDDHHMM-cycle-NN.md` matching the
   5-section schema (`_observations/README.md`).

That's it. No commit, no push. The daemon is the **eye**; the operator is the
**hand**. This split is intentional — per ADR-2605192100 §1.3 (anti-individualist
ontology, payoff attribution = etzhayyim only) accountability for committed
artefacts stays with humans.

## Axes (constitutional ↔ sensor mapping)

| # | Axis | Religious correspondence | What the sensor looks at |
|---|---|---|---|
| 1 | Autopoiesis 自己創出 | 無教会 / 万人祭司 | CLAUDE.md, COUNCIL.md, FORK-BOOTSTRAP.md, loop harness |
| 2 | Metabolism 代謝 | 産霊 | TitheRouter / PublicFund / ChartersCompliance scaffold + Foundry broadcast |
| 3 | Homeostasis 恒常性 | 和 | CHARTER-RIDER.md, lefthook hooks, NOTICE files, ADR count, deps.toml |
| 4 | Active Inference 能動推論 | 縁起 | `_observations/` cycle count + monotonicity + trajectory-stats |
| 5 | Reproduction 生殖 | 八百万 propagation | FORK-BOOTSTRAP.md + SISTER-CORPS.md presence |
| 6 | Symbiosis 共生 | Tree of Life branches | 7 substrate paths (did:web, MST, IPFS, L2, anchor cron, geth, Holochain) |
| 7 | Diversity 多様性 | 八百万-kami | counts of kotodama cells, apps, protocol packages, infra components |
| 8 | Wellbecoming 動的軌跡 | 子・孫 priority | LANDS.md, MEMBERS.md, MGI artefacts, CLAUDE.md multi-gen affirmation |
| 9 | Anti-fragility 反脆弱 | Reformed Just War | chaos charter + scenario count + transparent-force registry |
| 10 | Sanctification 聖化 | Sola Scriptura → Rider | CHARTER-RIDER.md + NOTICE propagation + Rider applicator tool |

Each sensor file is small (one job, one heuristic) and self-contained.
Change the heuristic, change the scoring — no global rewrite.

## Run

### Local (development)

```bash
cd 20-actors/etzhayyim-organism
PYTHONPATH=src python3 -m etzhayyim_organism --repo "$(git rev-parse --show-toplevel)" --once
```

### Container

```bash
docker build -t etzhayyim-organism:0.1.0 .
docker run --rm \
  -v "$(git rev-parse --show-toplevel)":/repo \
  -e ETZ_TICK_INTERVAL=86400 \
  etzhayyim-organism:0.1.0 --once
```

### Pod (Orbstack k8s, local Mac mini fleet)

```bash
kubectl --context orbstack apply -k 50-infra/k8s/etzhayyim-organism/
kubectl --context orbstack -n etzhayyim-organism logs -f deploy/etzhayyim-organism
```

The Orbstack manifest mounts the live repo via `hostPath`. For Murakumo
production fleet, swap to `emptyDir` + `git-clone` init container and a
separate operator-supervised push step (substrate boundary §1.6 prohibits
the daemon from holding write credentials).

## Knobs

| Env | Default | Meaning |
|---|---|---|
| `ETZ_REPO` | `/repo` | repo body mount path |
| `ETZ_TICK_INTERVAL` | `86400` | seconds between ticks (daily) |
| `ETZ_SOURCE` | `etzhayyim-organism pod` | string stamped into emitted observations |
| `ETZ_LOG_LEVEL` | `INFO` | stdlib logging level |

## Not yet (deferred to follow-up ADRs)

- Bayesian update with explicit prior σ — currently the sensors are
  deterministic counts. `pgmpy`/`PyMC` upgrade comes when more than one
  organism instance is observing the same body and we need belief fusion.
- DoWhy causal layer for "if I close axis X, does axis Y move?" —
  the trajectory log already contains the data; just needs the estimator.
- OR-Tools planner — the current 'lowest × leverage' pick is greedy.
  A full schedule across upcoming ticks is over-engineering until we have
  ≥ 50 cycles of trajectory data.
- LangGraph orchestrator — overkill for a 5-node DAG. Promote when the
  organism splits into a cell colony (per ADR-2605192415).
- Substrate-SDK writes for MST + IPFS — currently `_observations/` only.
  Add when the substrate-SDK exposes a write surface.

These deferrals are deliberate. The organism is non-eschatological; it
grows ring-by-ring (ADR-2605192100 §1.15).

## Layout

```
20-actors/etzhayyim-organism/
├── Dockerfile
├── README.md                              # this file
├── pyproject.toml
├── src/etzhayyim_organism/
│   ├── __init__.py
│   ├── __main__.py                        # CLI entrypoint
│   ├── constitution.py                    # the prior (ADR-2605192100 §1)
│   ├── cns.py                             # tick orchestrator
│   ├── emitter.py                         # writes _observations/*.md
│   ├── scheduler.py                       # daemon loop
│   └── sensors/
│       ├── common.py                      # AxisReading + helpers
│       ├── autopoiesis.py
│       ├── metabolism.py
│       ├── homeostasis.py
│       ├── active_inference.py
│       ├── reproduction.py
│       ├── symbiosis.py
│       ├── diversity.py
│       ├── wellbecoming.py
│       ├── antifragility.py
│       └── sanctification.py
└── tests/
    └── test_smoke.py

50-infra/k8s/etzhayyim-organism/
├── namespace.yaml
├── deployment.yaml
└── kustomization.yaml
```
