# 20-actors/ainori 相乗り

**Pooled passenger-mobility commons — Uber charter-clean inversion. ADR-2606071500. Status: R0.**

Members already travelling offer seats; riders cost-share (fuel/wear only, no margin); the platform is paid `cash≡0`. Reuses the **`todoke` route crate** (`20-actors/todoke/route`: NN+2-opt sequencing + SAE-L4 refusal envelope) — ainori adds passenger/occupancy semantics, not a second routing engine.

Two non-gig supply modes:
- **human-pooled** — member contribution + displacement-dividend coupling (ADR-2606032130).
- **autonomous-pooled** — `wadachi`/`tazuna` SAE-L4 shuttle on fixed/semi-fixed loops.

## Hard prohibitions (structurally unrepresentable, not policy)
- **No gig piece-rate** (G1) — `driverPaidMinor:const=0`, `gig:const=false`; driver compensation is dividend, never per-trip pay.
- **No surge / dynamic price** (G2) — fare = flat cost-share split across pooled riders.
- **No person-tracking / pattern-of-life** (G7/G12) — rider location on-device + ephemeral; no "where is person X"; aggregate-first telemetry only.
- **SAE-L4 ceiling, refusal-not-clamp** (G3) — out-of-ODD / over-speed requests refused, shared todoke envelope.
- **No server-held key** (G5); cost-share settlement USDC+TitheRouter via warifu.

## Gating
Live dispatch + live actuation = **Council Lv6+ + operator** (G10); autonomous-pooled near persons = **Lv7+** (Transparent Force audit). R0 ships scaffold + `:representative` seed; settlement intent-only until warifu Phase-2.

See ADR-2606071500 for the full rationale; `manifest.edn` for the canonical gate list.
