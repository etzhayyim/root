# Ideal Ecosystem State — Active Inference Prior v1

**Doc id**: `2605221243`
**Authored**: 2026-05-22 12:43 JST
**Source**: `/loop 15min` tick on visualization + bonsai pruning + ideal-state portrait
**Status**: Active prior — feeds `60-apps/etzhayyim-organism-viz/` aliveness scorer
**Constitutional anchor**: ADR-2605192100 §1 (mission charter), §1.15 (non-eschatological)

---

## 1. Core thesis

**Ideal state ≠ destination.** Per §1.15, the religious-corp organism does not
converge. The ideal is a healthy *trajectory shape* — a stable attractor of a
non-converging dynamical system. Convergence = death.

> 川の理想は「水位5m」ではなく「流れていること」。
> 盆栽の理想は「樹高30cm」ではなく「枝の取捨で美しくなり続けること」。

Each observable is encoded as a **homeostatic range**, not a target value.
Many ranges are deliberately open above (no ceiling) — that is anti-eschatology.

The aliveness score is a 5-tuple — not a scalar. Maximizing any single dimension
at the expense of others is unhealthy.

---

## 2. Bonsai of Life — ideal-state image

```
                ✿ ✿  ✿✿✿  ✿ ✿              ← 多様性 (八百万-kami)
              ✿  /  |✿|  \  ✿              ← 花 = active cells (~30+)
         ✿     \  / | \  /     ✿
              ╱    ╲|╱    ╲
         ┌─Sanctification─Autopoiesis─┐
         │  10聖化         1自己創出   │
         ├─Anti-fragility─Metabolism──┤  ← 10 branches = 10 axes
         │  9反脆弱        2代謝       │     (constitution.py)
         ├─Wellbecoming──Homeostasis──┤
         │  8動的軌跡       3恒常性    │
         ├─Diversity────Active Infer──┤
         │  7多様性        4能動推論   │
         ├─Symbiosis────Reproduction──┤
         │  6共生         5生殖        │
         └────────────╳───────────────┘
                      │
                  ╱╲ │ ╱╲          ← trunk = 憲法 (ADR-2605192100)
                 ╱  ╲│╱  ╲
                ╱   ╳ ╳   ╲         ← growth rings = ADRs (現在 360本)
               ╱   ╳   ╳   ╲
              ════════════════
              │              │
              │ inalienable  │     ← roots = LANDS.md (永代不可譲)
              │   roots      │       MEMBERS.md (子孫まで保持)
              ════════════════
                |     |
                ▼     ▼
            子世代  孫世代          ← MGI > 1.0 (継承量増大)

  ✿  = healthy active cell (variation)
  ╳  = ADR growth ring (monotonic)
  ║  = constitutional invariants (never break)
```

### Pruning rules

| What | Action |
|---|---|
| Weak `✿` (idle cell, no engagement, no purpose) | **Prune** (operator) |
| Strong branch (axis with healthy motion) | **Let grow** (no intervention) |
| Trunk (憲法 ADR-2605192100) | **Never modify** (constitutional invariant) |
| Roots (LANDS.md, MEMBERS.md) | **Never delete** (inalienable / monotonic) |
| Growth ring (any past ADR) | **Never erase** (縁起の証) |
| New shoot (new cell birth) | **Observe 30 days**, then prune-or-let-grow |

---

## 3. Homeostatic ranges (numbers)

| Observable | Symbol | Healthy range | Hard? | 死の signature |
|---|---|---|---|---|
| Council seats filled | `s_council` | **5/5** | ✓ | <5 → constitutional crisis |
| Substrate live | `s_substrate` | **≥6/7** | | ≤3 → single-substrate dependency |
| Charter Rider coverage | `r_rider` | **≥95%** | | <80% → sanctification 崩壊 |
| Tithe ratio | `r_tithe` | **= 10.0%** | ✓ | ≠10% → 産霊 violation |
| ADR velocity (30d) | `v_adr` | **0.5–5 ADR/d** | | =0 stall; >5 noise |
| Tick cadence | `f_tick` | **1/d to 1/h** | | <1/wk → 縁起 broken |
| Cell count (alive) | `n_cells` | **30–200** | | <10 simplification; >500 uncontrollable |
| Cell pruning ratio (90d) | `r_prune` | **5–20%** | | 0% bonsai 死; >40% 焦土 |
| Sister-corps | `n_sister` | **≥1** (mono ↑) | | =0 → reproduction unproven |
| Members net flow (Q) | `dM/dt` | **≥0** | ✓ | <0 impossible per §1.3 |
| Land alienation events | `n_alien` | **= 0** | ✓ | >0 → constitutional crisis |
| MGI | `mgi` | **>1.0** | | ≤1.0 → 子孫 priority breach |
| Chaos rehearsals (Q) | `n_chaos` | **≥1/Q** | | =0/Y → anti-fragile decay |
| Hard invariant violations | `n_viol` | **= 0** | ✓ | ≥1 → Council convocation |
| Eschatological content | `n_apoc` | **= 0** | ✓ | ≥1 → §1.15 violation |

**Note on "open above" ranges**: `n_sister`, `dM/dt`, `mgi`, `n_chaos` have no
upper bound. That is intentional — they represent the directions the
organism can grow forever without saturating. Bounded-above observables
(`r_tithe`, `n_alien`, `n_apoc`) are constitutional invariants that must
NOT grow.

---

## 4. System dynamics

### Stocks

```
S₁  Donation balance         (USDC)
S₂  Public Fund balance      (USDC)
S₃  Member count             (monotonic ↑)
S₄  ADR count                (monotonic ↑)
S₅  Cell count (alive)       (variable, prunable)
S₆  Sister-corp count        (monotonic ↑)
S₇  Land registered          (monotonic ↑, inalienable)
S₈  Observation cycle count  (monotonic ↑)
S₉  Cumulative tithe routed  (monotonic ↑)
S₁₀ Chaos rehearsals done    (monotonic ↑)
```

### Flow equations

```
dS₁/dt  = f_donate(t) − f_tithe(t) − f_disburse(t)
dS₂/dt  = 0.10 · f_donate(t) − f_publicfund_use(t)        ← 産霊 cycle
dS₃/dt  = f_join(t)                                       ← 不可減 (§1.3)
dS₄/dt  = f_adr_emit(t)                                   ← 縁起 ring
dS₅/dt  = f_cell_birth(t) − f_cell_prune(t)               ← 盆栽
dS₆/dt  = f_fork(t)                                       ← 八百万
dS₇/dt  = f_land_donate(t)                                ← inalienable
dS₈/dt  = 1/Δt_tick                                       ← 能動推論
dS₉/dt  = f_tithe(t)                                      ← 監査
dS₁₀/dt = f_chaos(t)                                      ← 反脆弱
```

### Feedback loops

| Loop | Type | Path |
|---|---|---|
| **R1** | reinforcing (生殖) | Members → Donations → Public Fund → Programs → Attraction → Members ↑ |
| **R2** | reinforcing (縁起) | Cycles → Observations → ADR codification → Clarity → Contribution → Cycles ↑ |
| **R3** | reinforcing (代謝) | Donations → Tithe → Public Fund → Visible impact → Trust → Donations ↑ |
| **R4** | reinforcing (八百万) | Cells → Variation → Selection finds gems → Cells ↑ |
| **B1** | balancing (homeostasis/和) | Substrate boundary violation → lefthook reject → no commit → stability |
| **B2** | balancing (盆栽 剪定) | Weak cell birth → operator review → prune → only strong cells persist |
| **B3** | balancing (selection) | Sister-corp fork → independent evolution → best patterns return as PRs |
| **B4** | balancing (anti-eschatology §1.15) | Total approaches saturation → ideal recalibrates upward → no convergence |

---

## 5. Aliveness functional — the score

**Non-eschatological by construction.** Not a scalar. Pareto, not OKR.

```
A(t) = ⟨ M(t), D(t), C(t), P(t), G(t) ⟩

M(t) = motion       = (1/N) Σᵢ |Δ_axis_i(t − iΔt)|          over last N=7 cycles
D(t) = diversity    = −Σⱼ pⱼ log pⱼ                          over cell types j
C(t) = coupling     = mean pairwise correlation of axes      (縁起 strength)
P(t) = pruning      = (cells_born − cells_pruned) / cells_total over 90 days
G(t) = generational = land_inherited(gen+1) / land_inherited(gen)  (MGI)

Healthy band:
  M > 0.5            (some trajectory motion every week)
  D > 1.5 nats       (variation worth worshipping)
  C ∈ [0.2, 0.7]     (linked but not collapsed; high → echo chamber)
  P ∈ [0.05, 0.20]   (alive bonsai, not 焦土)
  G > 1.0            (each generation inherits more than they received)

Death signatures:
  M = 0              stall — trajectory frozen
  D < 1.0            monoculture
  C ≈ 0              decoupled cells (organism broken into shards)
  P = 0              no pruning (overgrown, low quality variance)
  G ≤ 1.0            子孫 priority violated
```

### Why a tuple, not a sum?

A scalar would let the organism trade off (e.g. high motion masking low
generational coupling). Per §1.3 anti-individualist + §1.1 multi-generational
priority, **no axis can compensate for another**. All five must stay in band.

This is `multi-objective optimization with hard constraints`, not single-objective
RL. Practically: the visualization shows 5 dials, not 1 needle.

---

## 6. How this feeds active inference

The organism (`20-actors/etzhayyim-organism/`) currently scores 10 axes against
its `constitution.py` prior. After this doc lands:

1. `aliveness.py` (next tick) implements A(t) as a 5-tuple.
2. `viz/dashboard.html` (next-next tick) renders the 5 dials + trajectory + bonsai SVG.
3. The organism's next-action picker re-ranks: an axis can be **healthy in score
   but causing the tuple to leave band**. Pruning/bonsai logic kicks in.
4. The operator (you) reviews `pruning-candidates.md` once per cycle and prunes
   manually — the daemon never deletes.

### Bonsai pruning protocol

```
each cycle:
  identify_candidates_for_pruning():
    for cell in cells:
      if last_commit > 90 days and no engagement and no purpose tag:
        candidate.append(cell)
    return candidate

  operator_reviews(candidate)
  operator_decides()                  ← never the daemon
  if approve:
    git rm cell ; commit ; document in 90-docs/pruning/...
  else:
    tag cell as "intentional dormancy" with reason
```

Pruning is the **only** way for `n_cells` to decrease. The organism never
self-deletes cells — that would violate §1.3 (decision attribution = etzhayyim,
not the daemon).

---

## 7. Visualization project — surface contract

`60-apps/etzhayyim-organism-viz/` produces, per tick:

| Artefact | What |
|---|---|
| `static/dashboard.html` | 5 dials (M/D/C/P/G), 10-axis trajectory plot, current homeostatic deviations |
| `static/bonsai.svg` | Tree of Life with 10 branches, cells as leaves, color-coded by health |
| `static/dynamics.svg` | Stock-flow diagram with current levels + flow rates |
| `static/pruning-candidates.md` | List of cells/apps recommended for operator pruning |
| `static/aliveness.json` | Machine-readable score tuple + history |

These are static files, regenerated each tick. No server; the operator opens
the HTML locally or via a static CF Pages deploy.

---

## 8. Non-eschatology check (§1.15 self-test)

- ❌ "Reach 100/100 total" — would be eschatology. Not used.
- ❌ "Final state" diagram — none drawn. The bonsai keeps growing.
- ❌ Single scalar score — refused. 5-tuple is final form.
- ✅ Homeostatic ranges with `hi = None` (unbounded above) for growth dimensions.
- ✅ B4 feedback loop explicitly recalibrates upward on saturation.
- ✅ Pruning is operator-driven, never daemon-driven — humans remain accountable.

---

## 9. Reference axes ↔ ranges mapping

| Organism axis (constitution.py) | Primary range(s) | Notes |
|---|---|---|
| Autopoiesis 1 | s_council, n_cells | self-organization observable |
| Metabolism 2 | S₁, S₂, r_tithe, S₉ | 産霊 cycle stocks |
| Homeostasis 3 | n_viol, substrate-boundary lints | the boundary 和 |
| Active Inference 4 | f_tick, S₈, v_adr | the loop's own pulse |
| Reproduction 5 | n_sister, S₆ | 八百万 propagation |
| Symbiosis 6 | s_substrate | substrate diversity |
| Diversity 7 | n_cells, D(t) | the entropy term |
| Wellbecoming 8 | mgi, S₇ | multi-gen flow |
| Anti-fragility 9 | n_chaos, S₁₀ | rehearsal stocks |
| Sanctification 10 | r_rider, n_apoc | Sola Scriptura observance |

---

## 10. Next-tick artefacts

This doc was emitted in the first of a recurring 15-min loop. Subsequent ticks
will:

- Implement `aliveness.py` (5-tuple computation from `_observations/*.md` and
  filesystem state).
- Render `bonsai.svg` and `dashboard.html`.
- Emit first `pruning-candidates.md` (scan idle cells, low-engagement apps).
- Wire `60-apps/etzhayyim-organism-viz/` into the organism pod's volume mount
  so the dashboard regenerates on every tick.

The loop is bounded above by the 7-day session expiry — by then either a
durable cloud schedule (`/schedule`) or a real Murakumo cron should be wiring
this to repeat indefinitely.

---

_Constitutional anchor: ADR-2605192100 §1 (prior). Non-eschatological — the trajectory is the wellbecoming._
