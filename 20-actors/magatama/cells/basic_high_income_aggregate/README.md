# basic_high_income_aggregate — liberation (R0 scaffold)

Assemble the aggregate `basicHighIncome` block of the quarterly
`app.etzhayyim.liberation.metricReport` from the toritate per-adherent outputs
(`toritate_imputed_income_compute` FLOW + `toritate_commons_asset_value` STOCK).
Emits median/percentile figures only — never per-adherent identity — computes
`highIncomeBenchmarkRatioPermille`, and asserts `cashStipendUsdMicros == 0` on
every report.

Per ADR-2605301020 §5/§8 + ADR-2605261000 §4. R0 scaffold — `cell.py` raises at
import time until R1 (Council Lv6+ ≥3 ratify + toritate compute cells R1-active).

- **Doctrine**: Basic High Income (基本高所得)
- **Murakumo node (proposed)**: levi (liberation metric tribe)
- **Output Lexicon**: `app.etzhayyim.liberation.metricReport` (basicHighIncome block)
- **Ceiling**: `cashStipendUsdMicros≡0` (on-chain N1 proof) · AGGREGATE-ONLY-NO-PII (N6; cf. ADR-2605260215 pattern) · Wellbecoming guard (§6 — income↑ with Wellbecoming↓ ⇒ holdStage) · Murakumo-only inference (ADR-2605215000)
