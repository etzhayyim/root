# junkan (循環)

**Analysis-only societal feedback-loop observer.**

junkan applies systems-thinking to society at large: from passive, public,
aggregate data it continuously builds a system-dynamics model (stocks, flows,
reinforcing/balancing causal loops) and reads off which loops are currently
spinning **virtuous (好循環)**, **vicious (悪循環)**, **neutral**, or
**transitioning**, plus Meadows leverage-point candidates.

It then stops. **junkan has no actuator** — no post, no nudge, no email, no
transaction. Its only output is append-only structured findings for the Council
and other actors to read. That is the whole point: 分析するだけ.

## DID

- `did:web:junkan.etzhayyim.com`

## ADR

- ADR-2605290927 (R0 scaffold, 2026-05-29)
- Manifest: `20-actors/junkan/manifest.jsonld`

## Position in the ecosystem

| | Inward (self) | Outward (society) |
|---|---|---|
| Loop model | active-inference prior (doc 2605221243) | **junkan** |
| Continuous observer | KaizenObserver (ADR-2605240200) | **junkan** |
| Intervention | — | ossekai (ADR-2605264000) |

junkan is the outward, analysis-only complement of the inward self-model. It is
**not** ossekai (which intervenes) and **not** KaizenObserver (which is the self).

## Tech

- **Python LangGraph** heartbeat-cadence Pregel graph (8 cells).
- **datom / Datalog** data model (immutable society-stock facts + time-travel)
  on canonical **kotoba-kqe** (ADR-2605262130, Datomic-isomorphic
  EAVT/AEVT/AVET/VAET). Proprietary Datomic is **not** used (Charter Rider
  §2(e)+§2(c)).

## Constitutional spine

Analysis-only (G4, enforced by absence of any dispatch cell) · passive-only
collection (G3) · no causal overclaim (G5) · aggregate-only / no individual
modeling (G6) · non-eschatological framing (G7) · no prescription /
prediction-as-fact (G11) · Murakumo-only inference (G10) · default
Council-internal, publication-by-others (G13). Full table in ADR-2605290927.

## Status

R0 scaffold — 8 cells path-reserved + 5 Lexicon skeletons. No runtime code
until R1 (post Bootstrap-Council ratify).

## License

Apache-2.0 WITH etzhayyim Charter Compliance Rider v2.0 (`/CHARTER-RIDER.md`).
