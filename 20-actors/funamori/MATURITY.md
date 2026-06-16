# funamori 舫 — Maturity

**Stage: R0** (scaffold + runnable method) — ADR-2605265600. 淡水化発電 / marine-renewable
salinity-gradient power (PRO/RED) with open-membrane R&D gates. Instantiates the previously
path-reserved `cells/salinity_gradient_pro_red/` (ADR §5 R0).

| Dimension | State |
|---|---|
| Methods | ✅ `methods/salinity_gradient.cljc` — PRO/RED physics + Charter gates as throwing assertions (pure Clojure, portable `.cljc`) |
| Tests | ✅ `methods/test_salinity_gradient.cljc` — **24 tests / 57 assertions, green** (`./run_tests.sh`, babashka) |
| Datoms | ✅ `kotoba/schema.edn` (`:funamori.salinity.*` EAVT) + `kotoba/seed.edn` (`:representative` design site/membrane/measure) |
| Lexicons | ✅ 3 under `com.etzhayyim.funamori.*` (salinityGradientMembraneAttestation / salinityGradientSiteAttestation / silenSalinityGradientReview) — ADR §6 |
| Manifest | ✅ `manifest.edn` — 12 gates |
| Cells | ⛔ none yet (R1 — site_qualification / membrane_attestation / power_characterization Pregel cells, Murakumo-only) |
| Hardware | ⛔ none (R1 = bench ≤1 kW PRO / ≤500 W RED, Council + membrane-chemist gated) |

## Physics validated by the test (vs ADR-2605265600 Table)

- **Osmotic pressure** — seawater 35 g/L NaCl @20°C → **29 bar** (van't Hoff; textbook 27–28 bar). ✅
- **PRO max power density** — `A·Δπ²/4` at `ΔP=Δπ/2`, A=1e-12 → **2.1 W/m²**, inside ADR **1–3 W/m²** band. ✅
- **RED power density** — closed-form `E_cell²/(8·area-resistance)`, default 4e-3 Ω·m² → **~1.2 W/m²**, inside ADR **0.5–2 W/m²** band; independent of stack size N. ✅
- **Reverse-osmosis region** — `ΔP ≥ Δπ` ⇒ `Jw≤0` ⇒ no power. ✅

## Charter gates pinned by the test (enforced in code, ADR-2605265600)

- **G1/G2/G3 membrane** — open-publication/in-house mandatory; Toray/Hydranautics/GE-Power/Statkraft
  prohibited (§2); PFAS/Nafion prohibited (§1.2 / Charter §2(c)). `assert-membrane-permitted` throws.
- **G4 salinity-floor** — Δsalinity ≥30 g/L; brackish ≤15 g/L → DEFER R4+. `assert-salinity-difference` throws.
- **G5 power-density-floor** — ≥1 W/m² R3 gate. `assert-r3-power-density` throws.
- **G6 site-cap** — ≤50 kW/site, ≤1 site through R3. `assert-site-cap` / `assert-site-count` throw.
- **Integration** — `evaluate-site` runs ALL gates and returns `{:permitted false :violation <gate>}`
  for brackish / commercial-membrane / low-power / over-cap inputs (4 rejection paths tested).

## R0 → R1 gate

Post-Council + **≥1 membrane-chemist on Council** (ADR §5) + **mizuho R2** river-mouth
waterSupplySourceRegistry attestation + Council Lv6+ ≥3 estuarine baseline + LANDS-marine parcel.
Then bench ≤1 kW PRO OR ≤500 W RED single-stack pilot + open-membrane power-density characterization.
