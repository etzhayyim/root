---
id: adr-2606161830-ugachi-busshi-grounding-bridge
title: "ADR-2606161830: ugachi × busshi grounding bridge — the §2(l) gate's monopoly-effect grounded in observed concentration (Wave 2)"
status: accepted
doc_type: adr
topic: ugachi-busshi-grounding-bridge
authoritative: true
last_verified: 2026-06-16
priority: 6.0
axis: architecture
weight: 0.55
authoritative_for:
  - the ugachi→busshi grounding bridge (monopoly-effect from observed concentration)
  - the corroborate/downgrade/never-fabricate grounding rule
depends_on:
  - adr-2606161800-ugachi-extraction-risk-gate
  - adr-2606161730-busshi-commodity-materials-observatory
related:
  - adr-2606161700-multigenerational-extraction-risk-gate
supersedes: []
superseded_by: []
---

# ADR-2606161830: ugachi × busshi grounding bridge (Wave 2)

**Status**: accepted (landed, clj-native, tests green)
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki

# Context

The three layers of the §2(l) extraction stance are in place: the axis (ADR-2606161700),
the OBSERVATION of commodity concentration (busshi 物資, ADR-2606161730), and the EXECUTION
gate (ugachi 穿ち, ADR-2606161800). But they were not yet connected: ugachi's gate read
`:monopoly-effect` (`:entrench`/`:neutral`/`:diversify`) as a **free-standing project field** —
a claim taken at face value. A project could simply *declare* "we diversify the market" and the
gate would treat it as favorable, even if the commodity is not concentrated at all.

This ADR composes busshi into ugachi (the repo's cross-actor bridge pattern — cf.
kakaku→meyasu, tate↔kaiyaku, shionome `grounding.py`): the gate's monopoly input is now
**grounded in busshi's actual observed concentration**, so a diversification claim is checked
against whether there is, in fact, a chokepoint to dilute.

# Decision

`20-actors/ugachi/methods/bridge.cljc` (requires `busshi.methods.analyze` + `ugachi.methods.gate`):

1. **Map** a project's `:resource` → a busshi commodity id (`resource->commodity`).
2. **Pull** that commodity's observed `chokepoint-risk` + `top-producer-share` from
   `busshi.analyze` over busshi's own seed (`busshi-index`).
3. **Ground** the declared `:monopoly-effect` (`ground-monopoly-effect`):
   - `:diversify` + commodity concentrated (`:high`/`:critical`) → **corroborated** (keep)
   - `:diversify` + commodity NOT concentrated (`:low`/`:moderate`) → **downgrade `:neutral`** + flag `:overclaimed-diversification`
   - `:entrench` + concentrated → corroborated (keep)
   - `:entrench` + not concentrated → keep + flag `:entrench-on-unconcentrated`
   - `:neutral` → keep; resource unmapped → keep declared, context `:unmapped`
4. `ground-and-assess` grounds every project then runs `gate/assess` unchanged, returning the
   assessment + an `"adjustments"` list of every grounded change.

**Conservative invariant (test-enforced)**: grounding **never fabricates** an `:entrench` —
it only corroborates or downgrades. It can therefore never create a *false* refusal; it can
only (a) strip an unsupported diversification credit, or (b) confirm what the project declared.

## Result on the R0 seed

- `cu-diversify-b` (copper): declared `:diversify` → grounded `:neutral` (`:overclaimed-diversification`)
  — busshi copper chokepoint `:low` (top share 24%): nothing to diversify. Permit unchanged
  (still `:propose-r0`; the credit is corrected, not the verdict).
- `w-diversify-c` (tungsten): `:diversify` **corroborated** — busshi tungsten `:critical` (80%): a real chokepoint to dilute.
- `ree-entrench-f` (rare-earth): `:entrench` corroborated — busshi REE `:critical` (69%); still `:refuse :monopoly-entrenchment`.

# Consequences

**Positive** — the gate's monopoly judgment is now evidence-grounded rather than claim-based;
a diversification overclaim on an unconcentrated commodity is automatically stripped. The
observation layer (busshi) and execution layer (ugachi) are now one composed system. The
conservative rule keeps grounding from ever manufacturing a refusal.

**Negative / deferred** — grounding covers only busshi-mapped resources (aggregate /
polymetallic-nodule stay `:unmapped`, declared effect preserved). busshi's seed is
`:representative`; when busshi gains live primary-source ingest (its G7), the grounding
tightens automatically. rare-earth-coverage detail + kamado carbon-balance as gate inputs
remain Wave 2+ (this ADR does the monopoly leg only).

# Alternatives Considered

1. **Let grounding upgrade `:neutral`→`:entrench` when a project sits in the dominant country.**
   Rejected for R0: the synthetic seed has no reliable jurisdiction→producer mapping, and
   auto-fabricating `:entrench` risks false refusals — the conservative rule is safer.
2. **Put the bridge in busshi.** Rejected: busshi has no project concept; the consumer
   (ugachi) owns the bridge, exactly as meyasu owns the kakaku fuse.

# References

- ADR-2606161800 — ugachi §2(l) gate (the consumer)
- ADR-2606161730 — busshi commodity observatory (the source)
- ADR-2606161700 — the §2(l) axis
