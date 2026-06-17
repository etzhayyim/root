# kanayama 金山 — Maturity

**Stage: R0** (scaffold) — ADR-2605252400. Circular-metallurgy actor (Wave 1 = closed-loop
UBC aluminum recycling). RECYCLING-ONLY by constitution; mass-balance ≥98% closure; recovery
≥95% + ≤6 kWh/kg; renewable energy only. Closes the EOL loop for igata/suki (kanayama
recovers what they cast).

| Dimension | State |
|---|---|
| Lexicons | ✅ 8 under `com.etzhayyim.kanayama.*` (intake / decoating / melting / dcCasting / rolling / coilQualification / airEmissionsAudit / silenRecyclingReview) — R0 skeleton-level required arrays |
| Cells | 🟡 path-reserved in `20-actors/kanayama/cells` + 40-engine (R0) |
| Manifest | ✅ `manifest.jsonld` — `constitutionalGates` (G1–G14) + `nonGoals` (N1–N8) machine-readable |
| Tests | ✅ **23 green** — `methods/test_charter_gates.cljc` (**5**, added 2026-06-16: manifest gate-set + recycling-only non-goals + emissions basis) **+** `py/test_agent.py` (18, agent-layer gates); `./run_tests.sh` aggregates both |
| Methods | 🟡 agent present; offline metallurgy engine = R1 |

## Charter gates pinned by the new charter-gate test

- **Full gate set** — manifest `constitutionalGates.gates` declares exactly G1–G14.
- **Recycling-only (N1–N4)** — N1 excludes bauxite/primary mining; N2 excludes Hall-Héroult
  primary smelting; N3 excludes munitions/cartridge-brass recovery; N4 excludes
  nuclear-decontamination feedstock.
- **G2/G12/G13 quantitative** — mass-balance ≥98% closure; recovery ≥95%; captive
  coal/petcoke prohibited (renewable energy only).
- **G8 emissions/leachate** — `airEmissionsAuditRecord.regulatoryBasis` cites EU IED
  2010/75/EU + EN 12457 leachate (+ JP 大気汚染防止法 / JIS K 0058).
- **G4 witness quorum** — `meltingAttestation` requires `attestingRobots` + `alloyComposition`.

## Bug fixed 2026-06-17

`cells/mass_balance_binder/{state_machine,cell}.py` carried the bad-rename **broken Python
identifier** (`kotoba-datomicAnchor` / `transition_to_kotoba-datomic_anchored`, hyphen =
`SyntaxError`). Fixed identifier sites → underscore; record-key string `"kotoba-datomicAnchor"`
kept. Both files `ast.parse` OK; kanayama suite still 18/18 green. (Part of the cluster-wide
fix: sarutahiko + yamabiko + watatsumi + kanayama — all 4 `*_binder` cells now parse.)

## R0 → R1 gate

silenRecyclingReview `r1-benchtop-pot-melt` + Council Lv6+ + metallurgist SME
(ADR-2605252415); G2/G12 quantitative caps enforced in the R1 cell logic.

> **2026-06-17 substrate-native migration (ADR-2606160842):** the charter-gate test above was ported Python→Clojure (`methods/test_charter_gates.py` → `methods/test_charter_gates.cljc`, ns `kanayama.methods.test-charter-gates`, reads the lexicons via cheshire/edn) and the Python was pruned. Run via `./run_tests.sh` (now `exec bb`) or `bb run test:charter` (all 34 charter suites; 244 tests / 924 assertions green). Assertions unchanged (1:1 port).
