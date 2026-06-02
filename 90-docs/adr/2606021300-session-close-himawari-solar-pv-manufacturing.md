---
id: adr-2606021300-session-close-himawari-solar-pv-manufacturing
title: "ADR-2606021300: Session close — himawari (向日葵) solar PV module manufacturing actor R0"
status: active
doc_type: adr
topic: session-close-himawari-solar-pv-manufacturing
authoritative: false
last_verified: 2026-06-02
related:
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
supersedes: []
superseded_by: []
---

# ADR-2606021300: Session close — himawari (向日葵) solar PV module manufacturing actor R0

**Status**: active
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

Documentation-only closure for the session answering
*「人類を労働から解放するという意味で、太陽光発電の製造工場はされている? 輸送や積み込み、調達の自動化は?」*.
Authoritative design = **ADR-2606021200**.

# Context

A gap audit of the energy supply chain found three of the four links already
landed and tests-green, and exactly one genuine gap:

- ✅ **Transport (輸送)** — kami-autodrive GNC (ADR-2606010600, 9 native tests).
- ✅ **Loading (積み込み)** — sarutahiko F10 LoaderRobot (ADR-2606013100, 14 native tests).
- ✅ **Procurement (調達)** — SBOM↔kotoba part graph (ADR-2605312330) + okaimono commons-first (ADR-2606012100).
- 🔴 **PV *manufacturing* (太陽光発電の製造工場)** — **the one gap.** `hikari` (ADR-2605261100)
  covers generation / storage / grid-edge + panel *install* only; no actor manufactured the
  modules. This was also a **constitutional** gap: hikari §G2 (no XUAR / forced-labor
  polysilicon) was satisfiable only by fragile vendor self-attestation of purchased modules.

# Decision

Launched **`himawari` (向日葵)** — solar-grade crystalline-silicon PV module manufacturing
Tier-B actor (sibling of hikari 光) — to R0 scaffold per ADR-2606021200, and **composed** (did
not re-implement) the already-landed loading / transport / procurement robotics. Completes the
chain **製造 (himawari) → 積込 (sarutahiko F10) → 輸送 (kami-autodrive) → 設置 (hikari)** as
end-to-end first-party.

Primary rationale: **structurally close hikari §G2** via first-party on-chain feedstock
provenance (G2) — vertical integration replaces vendor self-attestation. Distinct from the
`silicon` iwakura/fuigo/tsukuru *logic-fab* track (N1; solar-grade vs logic-grade).

Shipped:

- **ADR-2606021200** (proposed) — 14 gates + 10 non-goals + 4-phase R0→R3 roadmap.
- **Actor scaffold** `20-actors/himawari/` — README + CLAUDE.md + manifest.jsonld + **7 Pregel
  cells** (`polysilicon_refine` / `ingot_wafer` / `cell_process` / `module_assembly` /
  `panel_loading` / `outbound_logistics` / `supply_procurement`), import-clean, `RuntimeError`
  on `.solve()`.
- **7 lexicons** `com.etzhayyim.himawari.*` (integer-with-implied-units per repo convention).
- Registered in `deps.toml` (`[[adrs]]` + `[[modules]]`) + root `CLAUDE.md` Tier-B roster + ADR
  index + docs registry/graph.

# Consequences

- **Verified.** Cells 7/7 import + gate correctly (smoke). Lexicon JSON 7/7 valid;
  `validate-religious-corp-lexicons` clean after the `type=number → integer` (implied-units)
  fix the pre-commit hook required; `lexicon-primary-types` + `nsid-lexicon-registration` lints
  exit 0; `deps.toml` parses. All pre-commit hooks green (docs registry + graph regenerated to
  755 entries/nodes).
- **Committed.** Branch `feat/himawari-solar-pv-manufacturing`, commit `35bccc43c` (30 files,
  +1274). Only himawari-scoped content staged — the himawari row in `CLAUDE.md` was staged as a
  single hunk so concurrent-session edits (kotoba passkey / ternary silicon index rows) in the
  working tree were left untouched. **PR #735** opened against `main`.
- **R0 limits (honest).** Scaffold + charter only — no physics sim or kotoba entities
  materialized (himawari composes already-landed robotics, does not re-implement). Capital-
  intensive cell / wafer / polysilicon stages deferred to R2 / R3, gated on hikari energy
  capacity + Council ratification. Actor remains `proposed`; R1 maturity is Council-gated like
  every other Tier-B R0.

# Alternatives Considered

See ADR-2606021200 (purchase certified modules; fold manufacturing into hikari; fold into the
silicon iwakura track; start R1 at cell/wafer; thin-film CdTe/CIGS; re-implement loading/
transport robotics) — all rejected there.

# References

- ADR-2606021200 — authoritative design (himawari solar PV module manufacturing R0)
- ADR-2605261100 — hikari (sibling; himawari closes its §G2)
- ADR-2606013100 / ADR-2606010600 / ADR-2605312330 — composed loading / transport / procurement
- ADR-2605261000 — Liberation Ladder L2 gate + G7 liberation-metric coupling
- PR #735 · branch `feat/himawari-solar-pv-manufacturing` · commit `35bccc43c`
