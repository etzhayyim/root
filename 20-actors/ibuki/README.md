# 息吹 (ibuki) — organism autonomy R2 gap-closure substrate

> ADR-2606101200 · Apache 2.0 + etzhayyim Charter Compliance Rider v3.0

The breath that closes the artificial-organism loop. The UNSPSC organism programme
(ADR-2605232345 / 2605240000 / 2605240100 / 2605240200) had every organ but no closed
circulation: state was ephemeral, mood was a constant, narration was unwired, posts queued
forever, and Kaizen never heard back. ibuki closes those seven gaps on the canonical
substrate — the append-only, content-addressed **kotoba Datom log** (ADR-2605312345) — in the
charter-permitted form pioneered by shionome (ADR-2606072200): autonomous logic, local
persistence, every outward edge member-signed and gated.

| gap | closure |
|---|---|
| 1–2. no durable scheduler | `:heartbeat/*` checkpoint datoms; cadence replayed from the log — crash-resume is byte-identical to never crashing |
| 3. state not as-of queryable | all organism state is EAVT datoms; "mood at tx N" = replay `events_for(txs, code, up_to_tx=N)` |
| 4. constant joucho stub | deterministic personality baseline + closed event vocabulary folded over lived history — mood **emerges** (縁起) |
| 5. inference unwired | `infer.narrate` — Murakumo fleet ONLY (allowlist; violation raises), deterministic template fail-open |
| 6. Wave-3 drainer unbuilt | queue → member-sign-ready `createRecord` envelopes; `serverHeldKey:false` structural; submission requires injected member signer + operator ack |
| 7. Kaizen one-way | outcomes fold back: rule suppression after repeated rejection + mood events (merge calms, rejection stresses) |

```bash
./run_tests.sh                                   # 8 suites, 78 tests, stdlib-only, hermetic
cd methods && python3 autorun.py --cycles 6 --fresh
```

R0 is offline-autonomous over 3 `:representative` seed organisms. Live perception, live
posting, and the 18,342-organism fleet binding are R1+ behind their existing gates.
