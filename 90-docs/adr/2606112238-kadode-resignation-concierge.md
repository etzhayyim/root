---
id: adr-2606112238-kadode-resignation-concierge
title: "ADR-2606112238: kadode 門出 — labour-resignation concierge + 使者 (退職代行), UPL-bounded"
status: active
doc_type: adr
topic: kadode-resignation-concierge
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.5
priority_note: "First worker-EXIT concierge; charter-clean inversion of commercial 退職代行 with the 非弁 boundary enforced in code."
authoritative_for:
  - labor-resignation-concierge
  - labor-exit-ontology
  - 退職代行-upl-boundary
depends_on:
  - 2605262700
  - 2606111954
  - 2605181100
  - 2605231525
  - 2605312345
  - 2605215000
  - 2605261000
  - 2605302357
related:
  - 2605312030
  - 2605312500
  - 2606060900
  - 2605263700
supersedes: []
superseded_by: []
---

# ADR-2606112238: kadode 門出 — labour-resignation concierge + 使者 (退職代行)

**Status**: active
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

退職代行 (resignation-proxy) is a large, fast-growing service in Japan: a third party that
helps a worker leave a job they cannot face quitting — the trapped-worker, ブラック企業,
退職拒否, harassment situation. It sits squarely inside the etzhayyim Charter §mission
(人類の構造的労働解放) and Wellbecoming: a worker set free from coercive employment, with dignity.

But the commercial industry blurs a hard legal line. A non-lawyer 退職代行 may act only as a
**使者 (messenger)** — *conveying* a worker's already-formed, unilateral resignation. It may NOT
**negotiate** terms, severance, unpaid wages, or settlements: that is 法律事務 reserved to
lawyers (弁護士法72条, 非弁行為禁止), or to a labour union exercising 団体交渉権 (労働組合法6).
Many vendors cross that line. etzhayyim already had the worker-side gap (no resignation actor)
and the pattern to fill it cleanly: the concierge lineage (toritsugi 取次 / kurashimori 暮らし守 /
tasuke 助), all UPL-bounded + default-self-submit, plus hinagata 雛形 (ADR-2606111954) for the
document layer.

# Decision

Introduce **kadode 門出** ("setting out on a new path"), a Tier-B worker-EXIT concierge that is
the **charter-clean, free inversion** of a commercial 退職代行, with the 非弁 boundary **enforced
in code and proven by tests**, not merely documented.

1. **`labor-exit-ontology` (`00-contracts/schemas/`)** — nodes `:lx/kind` ∈ `{:scenario :ground
   :document :route :risk}`; edges `{:supported-by :requires-route :produces :rests-on :counters
   :triggers :upl-bound}`. The load-bearing table `:route/negotiation-capability` marks only
   `:labor-union` + `:lawyer` as able to negotiate; `:worker-self` + `:kadode-messenger` cannot.
2. **Seed graph** — 10 real worker scenarios, 12 real Japanese labour-law grounds (民法627/628/626,
   労基法137/15-2/16/5/24/39, 労働組合法6, 弁護士法72, 雇用保険法7 — each with its e-Gov URL),
   5 documents (退職届/退職願/即時退職通知/内容証明/有給取得届), 4 routes, 5 employer risk-patterns
   (退職拒否/損害賠償脅迫/有給拒否/離職票不交付/強制労働) each with a countering ground.
3. **Edge-primary analyzer (`analyze.py`)** — per scenario, the lawful **route** (escalation
   ladder), with the **UPL invariant enforced**: a `:scenario/needs-negotiation true` situation
   is constrained to a negotiating route (union/lawyer); `recommend_route()` raises on a graph
   that would route it to a 使者/self lane.
4. **Document generator (`generate.py`)** — renders the worker's OWN resignation documents
   (一身上の都合 only, never a demand), content-addressed (CIDv1+SHA-256). `assert_no_negotiation()`
   rejects demand/negotiation language injected into a free-text field. `build_relay()` builds an
   **UNSENT** 使者 relay for non-negotiating scenarios and **refuses + escalates** anything
   needing negotiation — the action-layer expression of G1.
5. **Lexicons** — `com.etzhayyim.kadode.{resignationRelay, escalation}`: the messenger relay
   record (negotiates=false, status drafted-unsent, PII via himotoki envelope) and the escalation
   record (the on-log proof the boundary was respected).
6. **kotoba pywasm component** — `analyze`/`datoms`/`coverage`/`generate`/`relay` exports;
   G1 + no-server-key hold in WASM.

**Constitutional gates**: G1 使者-not-agent (negotiation → union/lawyer, code-enforced) · G2
worker-authored · G3 non-adjudicating · G4 free · G5 sourcing-honest (UPL invariant measured) ·
G6 Murakumo-only · G7 outward-gated (sending is consent+Council) · G8 no-server-key + himotoki
PII. 26 tests green, incl. the UPL-invariant and the relay-refusal tests.

# Consequences

- **Positive**: fills the worker-exit gap with a working, tested actor that is honest about the
  exact 非弁 line the commercial industry blurs; the boundary is a code invariant, not a promise.
  Reuses the concierge pattern + hinagata document layer; serves 労働解放 + Wellbecoming directly.
- **Boundary**: kadode is **not** a law firm or a negotiator — it relays a unilateral resignation
  and drafts the worker's own documents. Anything adversarial (unpaid wages, 損害賠償, harassment)
  routes to a union or a lawyer. Actually transmitting the resignation is **G7-gated** (worker
  consent + operator step); R0 ships analyze + generate + UNSENT relay.
- **Negative / deferred**: jurisdiction is Japan-only at R0; the relay's transmission channel
  (email/内容証明/郵送) is unimplemented (G7); mental-health and victimisation hand-offs (kokoro/
  tasuke) are cross-link stubs, not live integrations.

# Alternatives Considered

- **Fold into chigiri or toritsugi** — rejected: the worker-exit domain has its own scenario↔
  ground↔route↔risk structure and a distinct, load-bearing UPL invariant worth isolating and
  testing on its own.
- **A full代行 that negotiates** (the commercial model) — rejected categorically: that is 非弁
  行為 for a non-lawyer (弁護士法72条). The whole point is to invert that model, not replicate it.
- **Charge a fee** (industry norm ¥20k–50k) — rejected: kadode is free (G4), like tasuke; the
  worker submits their own documents.

# References

- ADR-2605262700 (chigiri 契 — legal-procedure substrate)
- ADR-2606111954 (hinagata 雛形 — legal-template commons, the document layer)
- ADR-2605181100 (himotoki PII envelope) · ADR-2605231525 (no-server-key)
- ADR-2605312345 (kotoba Datom = canonical state) · ADR-2605215000 (Murakumo-only)
- ADR-2605261000 (Labor-Liberation ladder) · ADR-2605302357 (Social Security §1.16)
- siblings: ADR-2605312030 (toritsugi) · 2605312500 (kurashimori) · 2606060900 (tasuke) · 2605263700 (kokoro)
