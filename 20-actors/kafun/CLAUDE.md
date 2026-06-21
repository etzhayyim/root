# 20-actors/kafun — CLAUDE.md

## What this is

**kafun 花粉** — the **花粉撲滅 remediation** actor. 撲滅 = ecological RESTORATION
(主伐再造林), **never deforestation-for-profit**. The clj-native Tier-B
actor-ization of the legacy `60-apps/etzhayyim-project-public-kafun-bokumetsu`
pipeline (ADR-2605100100 + 2605210928) onto the kotoba Datom log.

**ASSESSMENT + R0 DESIGN ONLY — kafun never cuts and never plants** (no actuation
method; live forestry is the landowner's + operator/Council step, exactly as
ugachi never digs).

`did:web:etzhayyim.com:kafun` · `com.etzhayyim.kafun.*` · ADR-2606211712 · clj-native R0.

## The gate (verdict algebra, `methods/remediate.cljc`)

Edge-primary `pollen-burden = min(1, area-ha/10000) · emission-density ·
(0.5 + 0.5·exposed-pop-weight)` scored on read. `verdict` →
`{:refuse :await-consent :protected-selective :await-sapling-supply
:reforest-priority :monitor}`, in order:

1. `replant=false` (主伐 without 再造林) → `:refuse :clearcut-without-reforest` (G1/G4)
2. `carbon :net-positive` → `:refuse :carbon-positive` (G4 / §2(d))
3. consent absent → `:await-consent` (G3, land sovereignty)
4. `protected` → `:protected-selective` (never 皆伐; gradual/selective)
5. `sapling-supply :none` → `:await-sapling-supply` (**L1-1** 無花粉苗木)
6. `burden ≥ 0.3` AND `reforest-viability ≥ 0.5` → `:reforest-priority` (**L3-1** 主伐再造林)
7. else → `:monitor`

**Hard refusals precede every other route** (meta-invariant: no `replant=false` /
net-carbon-positive stand returns a permit; test-enforced).

## Hard invariants (proven by tests)

- **G1 撲滅-is-restoration** — `:kafun/clearcut` + `:kafun.stand/eradicate-species` unrepresentable.
- **G5 never-acts** — no `:kafun/actuate`; assessment + R0 design only.
- **G2 map-not-cut-list / no person data** — `:kafun.person/health` unrepresentable.
- refuse-precedes-routing; report declares it is NOT a cut-list, DESIGN-ONLY, "never cuts".

## Files

```
methods/kafun_edn.cljc    loader + classify
methods/remediate.cljc    pollen-burden → verdict → assess → render-datoms → render-report (+ bb CLI)
methods/kotoba.cljc       content-addressed append-only REMEDIATION LEDGER (tx-cid/make-tx/append-tx/read-log/verify-chain)
methods/autorun.cljc      deterministic, idempotent-by-content heartbeat — assess → append ONLY on change (+ bb CLI)
methods/test_*.cljc       loader + gate + ledger + heartbeat invariants
kotoba/ontology.kafun.edn EAVT schema + enums + refuse-reasons + negative space
kotoba/seed.edn           12 synthetic stands spanning all verdicts
data/ (gitignored)        generated remediation ledger — never committed/hand-edited
manifest.edn              gates G1–G8 + non-goals N1–N5
```

## 持続永続化 (persistence) — `methods/kotoba.cljc` + `methods/autorun.cljc`

Same content-addressed commit-DAG machinery as ugachi (ADR-2606170900): the
heartbeat appends verdict datoms as one content-addressed tx (prev-cid chained,
`verify-chain` tamper-evident) ONLY when they change (identical beat = no-op,
`:appended false :reason :no-change`); deterministic (caller supplies tx-id +
as-of, no wall clock) → resume-safe; no-server-key (local file, no network I/O).

## Run

```bash
./20-actors/kafun/run_tests.sh                                  # 4 suites (22 tests / 62 assert)
bb --classpath 20-actors 20-actors/kafun/methods/remediate.cljc # print the remediation map
bb --classpath 20-actors 20-actors/kafun/methods/autorun.cljc   # heartbeat → append to ledger
```

## Pairs with

- **sanae** (planting robotics — L1-1 苗木 + L3-1 再造林 body) · **inochi** (biosphere restoration)
- **mitate** + **iyashi** (allergic-rhinitis diagnosis/care — kafun does NOT diagnose/treat, N4)
- legacy App `60-apps/etzhayyim-project-public-kafun-bokumetsu` (outreach + Public Fund surface)
- Authorized by **ADR-2606211712**. Live forestry = landowner + operator/Council (never kafun).

## R0 → later

- **R1+**: inochi-grounding bridge (habitat sensitivity as a real gate input,
  ugachi/busshi bridge pattern); real cadastral + Sentinel-2/ALOS canopy → kotoba
  (the legacy scout→cadastral→envoy pipeline, behind a G7 operator flip);
  Murakumo-narrated remediation digest; fleet registration (cell-runner + healthz);
  live kotoba-engine bridge (ibuki-R3 pattern); lexicon JSON under
  `00-contracts/lexicons/com/etzhayyim/kafun/`. Live actuation stays landowner +
  operator/Council, never kafun.
