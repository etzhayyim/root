# itonami 営み — factory-operations agent (ADR-2606082300)

The charter-clean inversion of an **"AI Factory Brain" / NVIDIA Factory Operations
Blueprint (FOX)**. FOX wires AI agents into a running plant to optimize energy / quality /
throughput for the operator. itonami does the same *observation + optimization* maths —
**OEE, energy/good, idle-energy, scrap-rate** — but inverts the telos and the boundary:

| FOX (operator-optimizing) | itonami (charter-clean) |
|---|---|
| AI agents can write back to the OT bus / actuate | **observe → recommend only**; never actuates (no-server-key, liveActuation:false) |
| factory floor monitoring → worker productivity | **station/line scale only**; per-worker monitoring **structurally unrepresentable** (G2) |
| efficiency → throughput / line-speed-up | efficiency → **improvement + Wellbecoming**, never labor intensification |
| proprietary platform, telemetry | open-source, kotoba Datom-native, Murakumo-only |

## What it is

Reads a kotoba-EDN operations log (`:station/*` cells + `:tick/*` scan-cycle observations —
the **kotoba-os scan-cycle = Datom transaction** analog, ADR-2606031600) and computes,
aggregate-first:

- **OEE = Availability × Performance × Quality** per station + line rollup (gated by the
  weakest station — a serial line *is* its bottleneck)
- **energy/good-unit (kWh)** + **idle-energy fraction** — the FOX "cut 10% energy" lever
- **scrap-rate** — routed to vision inspection (**manako**, ADR-2606034800) + root-cause

Findings are *routed* to a human / Council, never written back.

## Where it sits

The **"run the factory"** observer paired with the **"build the factory"** sims:
- builds: giemon-factory (ADR-2606010030), sarutahiko truck line (ADR-2606013100),
  tatekata (ADR-2605250715) — physics on kami-genesis
- runs: kotoba-os scan-cycle Datoms (ADR-2606031600) → **itonami** OEE/energy/quality
- quality → manako vision · energy → hikari · ledger → toritate

The seed (`data/seed-factory-ops.kotoba.edn`) is the sarutahiko 8-cell line, tying the
observer to the existing build sim.

## Gates (constitutional — read `manifest.jsonld` for full text)

- **G1** observe→recommend, NEVER actuate. No write-back to the OT bus.
- **G2** station/line scale ONLY — no `:worker/*`/`:person/*`; anti-labor-surveillance.
- **G3** non-adjudicating — states/counts are disclosed facts; KPIs are read-time aggregates
  flagged `:bond/is-transient`, never durable verdicts.
- **G4** civilian producing actors only (Charter §1.12).
- **G5** sourcing honesty — R0 seed is `:representative` synthetic, never live OT.
- **G6** outward-gated — live OT/SCADA ingest (Modbus/OPC-UA/EtherCAT via kotoba-os device
  worlds) requires Council + operator DID; R0 = analyzer + schema + seed.
- **G7** Murakumo-only narration (ADR-2605215000).

## Run

```bash
python3 tests/test_analyze.py          # 10 tests, pure stdlib
python3 methods/analyze.py             # → out/operations-report.md
python3 methods/datom_emit.py --tx 1   # → out/itonami-datoms.kotoba.edn
```

## Status / roadmap

- **R0 (this)** — analyzer + datom-emit + ontology + seed + 10 tests. design-only.
- **R1** — line-balancing recommendation (bottleneck-relief proposal) + energy-schedule
  optimizer (idle-power-down windows); cross-check OEE against the sarutahiko produce sim.
- **R2** — live scan-cycle ingest from a kotoba-os `plc-host-runner` Datom stream (G6/Council
  gated); manako scrap-image hand-off; Murakumo-narrated daily ops digest.
