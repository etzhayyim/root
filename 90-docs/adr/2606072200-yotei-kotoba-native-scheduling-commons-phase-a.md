---
id: adr-2606072200-yotei-kotoba-native-scheduling
title: "ADR-2606072200: yotei — kotoba-native scheduling commons (Calendly inversion); remediation Phase A"
status: proposed
doc_type: adr
topic: yotei-kotoba-native
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/yotei
depends_on:
  - 2606071800   # substrate remediation wave (Phase A)
  - 2606072000   # business-manager (Phase A recipe)
  - 2605262130   # kotoba storage substrate
related:
  - 2605181100   # encrypted envelope
supersedes: []
superseded_by: []
---

# ADR-2606072200: yotei — kotoba-native scheduling commons (Calendly inversion); remediation Phase A

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

`yotei` (the Calendly equivalent) existed only as a **legacy T1 MCP-Compose scaffold** whose
read/write path is **Cypher over RisingWave-via-yata-graph** (`:Calendar`/`:Availability`/
`:Event`/`:Booking` nodes). That is the Phase-A category of the substrate remediation wave
(ADR-2606071800): manifest-only legacy actor → rewrite kotoba-native, cheap, no data migration.

A faithful Calendly clone is also a charter conflict: Calendly monetizes via **paid seat tiers**
and **harvests scheduling/contact data** of every booker (an ad/CRM funnel). The underlying need
— coordinate a meeting time — is neutral and mission-fine; the inversion drops the monetization
and the surveillance.

# Decision

Rewrite `yotei` as a **kotoba-EAVT-native scheduling commons**, mirroring the `business-manager`/
`omise` recipe (manifest.edn + lex + kotoba/schema.edn + py agent + tests). R0→R1.

**Charter-clean inversions / invariants (gates, see manifest.edn):**

| Calendly term | yotei dual | gate |
|---|---|---|
| paid seat tiers | **free**, no tiers, no subscription (no external inflow §1.3) | G1 no-tier |
| harvest booker contact/scheduling data into a CRM/ad funnel | **no data resale, no booker profiling**; booking PII encrypted, used only to hold the slot | G2 no-harvest |
| mutable calendar rows | **append-only Datoms**; a confirmed slot cannot be silently overwritten | G3 kotoba-eavt-native |
| double-booking races resolved server-side | **no-double-book invariant**: a proposal overlapping a confirmed booking is structurally refused | G4 no-double-book |
| platform-held calendar credentials | **member-signed** confirmations; server holds no key | G5 no-server-key |
| "3 spots left", urgency nudges | **no scarcity/urgency dark-patterns**; honest availability only | G6 anti-dark |
| vendor LLM copilots | Murakumo-only | G7 murakumo-only |

**Preserved domain semantics:** calendar owner = path DID; availability windows (day-of-week +
start/end, recurring); event; booking (requester/responder DID, duration, proposed slots,
confirmed slot, status); social announce on confirm.

**Deliverables:** `manifest.edn`, `lex/{availability,booking}.edn`, `kotoba/schema.edn`,
`py/agent.py` (availability → slot generation, **overlap/no-double-book detection**, propose →
member-signed confirm), `py/test_agent.py`, `DEPRECATED-jsonld.md` + CLAUDE.md banner. yotei has
no code files on the substrate frozen-allowlist (manifest-only), so this adds zero new debt.

# Consequences

- Closes the Calendly slot charter-clean (free, no harvest, no double-book) and removes a
  substrate-boundary violation.
- Reuses the Phase-A recipe (business-manager); net-new is the slot/availability/overlap logic.

# Alternatives Considered

1. **Keep the JSON-LD scaffold** — rejected: encodes the forbidden RisingWave/Cypher path.
2. **Calendly-faithful with a free tier + analytics** — rejected: booker-data harvesting is the
   surveillance the inversion exists to remove (G2).

# References

- ADR-2606071800 — substrate remediation wave (Phase A)
- ADR-2606072000 — business-manager (Phase A recipe)
- ADR-2605262130 — kotoba storage substrate
- ADR-2605181100 — encrypted envelope (booking PII)
