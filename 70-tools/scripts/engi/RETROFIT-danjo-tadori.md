# Retrofit: danjo / tadori findings → 縁(`:en`) edges

ADR-2606011000 §D6/§D7 — **design-first, gated** (§D9: §D1–§D4 need Council Lv7+ before
binding; this is the design of record, not an executed migration).

danjo and tadori already emit edges in disguise. Re-expressing them in the engi
vocabulary puts the whole accountability surface on **one graph** (the Engi Knowledge
Graph), so kanae can render power-取 (danjo) and on-chain custody (tadori) together with
the atproto follow-graph しがらみ — all as `:en` with a common `:en/grasping-load`.

Reference transform: `retrofit_danjo_tadori.py` (+ tests in `test_engi_pipeline.py`).

## Crosswalk

| Source (today) | engi rewrite | `:en/kind` | grasping-load | adjudicating? |
|---|---|---|---|---|
| danjo `named-party` / institution entity | `:organism` (`:human` / `:institutional`) | — | — | — |
| danjo `discrepancyObservation` (ADR-2605301600) | `:en` edge, `:en/source :danjo-observation` | `:entangled-with` | observation `weight` | **NO** — observed relation, never a verdict |
| tadori actor / address / cluster | `:organism` (`:institutional` / `:synthetic`) | — | — | — |
| tadori `attributionFinding` rel∈{controls,custodies} (ADR-2605301400) | `:en` edge, `:en/source :onchain` | `:custodies` | `txValue` (real custody) | finding, gate-bound |
| tadori `attributionFinding` rel=funds/flow | `:en` edge | `:flows-to` | `txValue` | — |

## Invariants preserved

- **Non-adjudication (danjo's core gate).** A discrepancy observation is **not** a verdict,
  so it becomes `:en/kind :entangled-with` — an *observed* relation. It is never `:owns`
  and never asserts guilt. (`test_d_danjo_observation_is_non_adjudicating_edge`.)
- **§4(2) floor unchanged.** This transform only changes the **shape** of a fact danjo/
  tadori were *already permitted* to publish (their own named-party / attribution gates,
  aggregate-first, encrypted-to-authorized-DIDs). It does **not** widen who may be named.
- **`:owns` absent.** On-chain control becomes `:custodies` + `:en/grasping-load` (=txValue),
  consistent with §D2 (custody-debt, not title). (`test_d_no_owns_in_crosswalk`.)

## Migration plan (when ratified)

1. Land the engi vocabulary as a kotoba schema attached to danjo/tadori (it lives at
   `00-contracts/schemas/engi-organism-ontology.kotoba.edn`).
2. Dual-write: danjo/tadori emit their current findings **and** the `:en` projection via
   these transforms (no read-path change yet).
3. Point kanae's renderer at the unified `:en`/`:grasp` arrangements (kotoba-kqe).
4. Cut the read path; retire the bespoke `discrepancyObservation`/`attributionFinding`
   shapes once parity is verified.

Each step is independently revertible; none executes before Council Lv7+ ratification of
§D1–§D4.
