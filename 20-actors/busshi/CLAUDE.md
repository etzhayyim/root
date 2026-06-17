# 20-actors/busshi — CLAUDE.md

## What this is

**busshi 物資** — the world **commodity & raw-materials** KG-mirror observatory.
Mirrors commodities/materials (precious metals 金銀PGM · base metals · rare/critical
metals · energy 石油ガス石炭 · agricultural softs) into the kotoba Datom log and runs
the **§2(l) multi-generational (子・孫) × wellbecoming RISK axis** (ADR-2606161700).
Umbrella sibling of `rare-earth-coverage` (rare-metals specialist), `kabuto`
(supply-chain), `kanjō` (financials), `kasa` (compute), `shionome` (capital flows).

`did:web:etzhayyim.com:busshi` · `com.etzhayyim.busshi.*` · ADR-2606161730 · clj-native R0.

## OBSERVATION ONLY (hard invariants — proven by tests)

- **取引しない (never a trade)** — G1: no buy/sell/position/order; `:busshi/trade` is unrepresentable.
- **採掘しない (never extracts)** — N1: extraction is gated by §2(l) as its OWN actor (ADR-2606161700); busshi only observes.
- **never forecasts** — G3: a producer SHARE + a price LEVEL are DISCLOSED facts, never a verdict and never a forecast point (mitooshi 見通し owns distributions). No `:busshi/signal`.
- **a resilience map, NEVER a target-list** — G2/G5: aggregate-first, no mine/well coordinates; the report says so in words.

## Analytical core (§2(l) risk axis)

Per commodity (pure clj): top-producer-share + named-HHI (concentration, `:other`
residual excluded) → chokepoint-risk; **multigen-risk** = 0.40·monopoly +
0.30·carbon-intensity + 0.30·irreversibility; **route** ∈
`{:resilience, :de-monopolization, :restoration}` by dominant driver:

- `:de-monopolization` → route-around (abaki / kabuto / tsumugi)
- `:restoration` → circular path (kanayama recycling / kamado energy-transition / inochi)
- `:resilience` → diversify supply + build stock/recovery buffers (default)

## Files

```
methods/busshi_edn.cljc   loader + classify (clojure.edn; :clj file I/O)
methods/analyze.cljc      analyze → datoms → render-datoms → coverage → render-report (+ bb CLI)
methods/kotoba.cljc       Wave 2: content-addressed append-only OBSERVATION LEDGER (tamper-evident commit-DAG)
methods/autorun.cljc      Wave 2: deterministic, idempotent-by-content heartbeat — analyze → append ONLY on change (+ bb CLI)
methods/test_*.cljc       loader + analytics + G1/G3/G5 + ledger/heartbeat invariants
kotoba/ontology.busshi.edn  EAVT schema + negative space (unrepresentable attrs)
kotoba/seed.edn           Wave 1 seed (25 commodities, all 5 classes, :representative)
data/ (gitignored)        generated observation ledger — never committed/hand-edited
manifest.edn              gates G1–G8 + non-goals N1–N5 + method/seed/ledger registry
```

## Datom convention

`[":db/add" entity ":busshi.<resource>/<aspect>" value]` (attrs are `:`-prefixed
strings, kotoba EAVT). Entities: `busshi-commodity:<id>`, `busshi-class:<class>`.
Every DERIVED datom carries `:busshi/derived true` + `:busshi/sourcing ":representative"`
(never re-ingested as authoritative). Disclosed-fact namespaces: `:busshi.commodity/*`,
`:busshi.producer/*`. Derived: `:busshi.obs/*`, `:busshi.class/*`.

## Run

```bash
bb --classpath 20-actors 20-actors/busshi/methods/test_busshi_edn.cljc   # loader (3 tests)
bb --classpath 20-actors 20-actors/busshi/methods/test_analyze.cljc      # analytics + invariants (9 tests / 55 assert)
bb --classpath 20-actors 20-actors/busshi/methods/analyze.cljc           # print the resilience map
bb --classpath 20-actors 20-actors/busshi/methods/autorun.cljc           # heartbeat → append observations to ledger
./20-actors/busshi/run_tests.sh                                          # 4 suites
```

## R0 → later waves

- R0 (ADR-2606161730): clj-native scaffold + `:representative` seed + analyze/datoms/coverage + tests.
- **Wave 2 (landed, ADR-2606171000)**: content-addressed observation-ledger persistence
  (`kotoba.cljc`) + deterministic, **idempotent-by-content** heartbeat (`autorun.cljc`) —
  observations appended to a tamper-evident commit-DAG (verify-chain) ONLY when they change
  (identical beat = no-op); resume-safe, no-server-key, gitignored. Mirrors ugachi (ADR-2606170900).
- Wave 2+: per-commodity depth (stocks/curve as facts, recycling-loop linkage to kanayama,
  primary-source ingest behind G7), Murakumo-narrated digest, fleet registration, lexicons.

## Related

- `/90-docs/adr/2606161730-busshi-commodity-materials-observatory-r0.md`
- `/90-docs/adr/2606161700-multigenerational-extraction-risk-gate-not-blanket-mining-ban.md` (the axis)
- `/20-actors/rare-earth-coverage/` (rare-metals specialist sibling)
- `/CHARTER-RIDER.md` §2(l) v3.2
