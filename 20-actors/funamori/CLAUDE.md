# funamori 舫 — CLAUDE guidance

**DID**: `did:web:etzhayyim.com:actor:funamori` · **Tier**: B · **Status**: R0 · **ADR**: 2605265600
(sub-ADR of 2605264100 §4; closes the salinity-gradient membrane-IP gap)

## What this actor is

淡水化発電 — **marine-renewable salinity-gradient power**. Generates electricity from the
Gibbs free energy released when fresh river water mixes with seawater. Two open-membrane
methods, both modelled in `methods/salinity_gradient.cljc`:

- **PRO** (pressure-retarded osmosis) — fresh-water osmotic pull lifts brine pressure → turbine.
  `W = Jw·ΔP`, max at `ΔP = Δπ/2` ⇒ `W_max = A·Δπ²/4`. ADR band **1–3 W/m²**.
- **RED** (reverse electrodialysis) — salinity-driven ion flux across alternating
  cation/anion-exchange membranes → current. Stack EMF `= N·2α·(RT/F)·ln(C_draw/C_feed)`;
  closed-form power density `= E_cell²/(8·area-resistance)`. ADR band **0.5–2 W/m²**.

This is the previously-reserved `20-actors/funamori/cells/salinity_gradient_pro_red/` path
(ADR-2605265600 §5 R0), now instantiated as a runnable method.

## Layout

- `methods/salinity_gradient.cljc` — the only code that *runs* at R0. Pure Clojure
  (`clojure.core` only), portable `.cljc`. Physics + **Charter gates as throwing assertions**.
- `methods/test_salinity_gradient.cljc` — 24 tests / 57 assertions (`./run_tests.sh`, babashka).
- `kotoba/{schema,seed}.edn` — kotoba EAVT Datoms (`:funamori.salinity.*`); seed is `:representative`.
- `lex/` — 3 lexicons (membraneAttestation / siteAttestation / silenSalinityGradientReview), ADR §6.
- `manifest.edn` — actor manifest + 12 gates.

## Hard rules (ADR-2605265600 gates — enforced IN CODE, not just documented)

The defining property of this actor: the ADR's constitutional constraints are **executable
assertions** that throw `ex-info {:error :charter-gate}`, proven by tests.

- **G1 open-membrane mandatory** — `assert-membrane-permitted`: license ∈ {in-house,
  open-publication, openmta, apache-2.0} required (§1.1).
- **G2 no-commercial-membrane** — Toray / Hydranautics / GE-Power / Statkraft **absolutely
  prohibited** (`prohibited-membranes`, §2). Do NOT add a commercial membrane vendor.
- **G3 no-PFAS** — Nafion-class perfluorinated chemistry prohibited (`pfas-membranes`,
  Charter §2(c) + §1.2). Do NOT relax to "Nafion is the industry standard."
- **G4 salinity-floor ≥30 g/L** — `assert-salinity-difference`; brackish ≤15 g/L → DEFER R4+ (§1.4).
- **G5 power-density-floor ≥1 W/m²** — `assert-r3-power-density`; below = re-design or DEFER (§1.6).
- **G6 site-cap** — `assert-site-cap` ≤50 kW, `assert-site-count` ≤1 site through R3 (§1.9 / parent §4).
- **G7 mizuho-attested-site** — site MUST be `mizuho.waterSupplySourceRegistry` attested +
  Council Lv6+ ≥3 estuary baseline (§1.3; cross-actor, R2+).
- **G11 no-server-key** — methods are pure compute, build no real stack. R0 stops at design intent.

## Cross-actor mesh (ADR §4)

- **mizuho** R2+ — river-mouth site qualification + waterSupplySourceRegistry + pretreatment.
- **hikari** R2+ — electrical output → microgrid + diurnal-smoothing storage pairing.
- **chigiri** R1+ — estuarine ecosystem regulatory cross-jurisdictional.

## Build / test

```sh
./run_tests.sh          # babashka; 24 tests / 57 assertions green
# or directly:
cd .. && bb -cp . -e "(require '[clojure.test :as t] 'funamori.methods.test-salinity-gradient) \
                      (t/run-tests 'funamori.methods.test-salinity-gradient)"
```

## Roadmap (ADR §5)

R0 = this method + gates + schema + lexicons (design only). **R1** = post-Council +
≥1 membrane-chemist on Council + mizuho R2 river-mouth attested + bench ≤1 kW PRO / ≤500 W RED
single-stack pilot. **R2** = ≤10 kW + power-density ≥1 W/m² demonstrated + PRO-vs-RED selection.
**R3** = full §1 cap (50 kW, 1 site).

## Do not

- Do not add a commercial proprietary membrane vendor (G2 — `assert-membrane-permitted` throws).
- Do not add a PFAS/Nafion membrane chemistry (G3 — same).
- Do not weaken the ≥30 g/L salinity floor or the ≥1 W/m² power-density floor (G4/G5 are §1 conditions).
- Do not raise the 50 kW / 1-site cap without an ADR-2605265600 amendment + Council Lv7+ unanimity.
- Do not treat the gate numbers as tunable parameters — they are Tier-1 derived from the ADR.
