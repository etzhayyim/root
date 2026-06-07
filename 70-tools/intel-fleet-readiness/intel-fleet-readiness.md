# intel-fleet-readiness — Murakumo deploy pre-flight

> 8/8 intel actors READY-PENDING-GATE · 227 tests green · **this tool never deploys** — live placement/ingest/publish is per-actor outward-gated (Council Lv6+ + operator). It reports what is ready and which gate remains.

| actor | suite | tests | artifacts | verdict | blocking gate |
|---|---|---:|---:|---|---|
| mitooshi | green | 135 | 9 | READY-PENDING-GATE | G10 — live promotion = Council Lv6+ + operator |
| watari | green | 13 | 1 | READY-PENDING-GATE | G7 — live AIS/ADS-B ingest = WATARI_OPERATOR_GATE=1 + Council |
| watatsuna | green | 14 | 1 | READY-PENDING-GATE | G7 — live cable-bulletin ingest = operator + Council |
| kabuto | green | 14 | 1 | READY-PENDING-GATE | G7 — live supply-chain ingest = operator + Council |
| kanjo | green | 17 | 1 | READY-PENDING-GATE | G7 — live EDGAR/EDINET fetch = KANJO_OPERATOR_GATE=1 + Council |
| tadori | green | 12 | 1 | READY-PENDING-GATE | live write = operator-staged + case-id + Council (passive-only) |
| danjo | green | 9 | 1 | READY-PENDING-GATE | G3/G10 — live gov-corpus ingest + named-party publish = Council + 1 SBT=1 vote |
| himotoki | green | 13 | 1 | READY-PENDING-GATE | G14/G10 — dispatch = verified target + HIMOTOKI_OPERATOR_GATE=1 + Council |
