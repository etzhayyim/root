# com.etzhayyim.junkan.* — Lexicons

Lexicons for **junkan (循環)**, the analysis-only societal feedback-loop
observer. R0 skeletons per ADR-2605290927; full schema hardening at R1.

| Lexicon | Purpose | Key structural gates |
|---|---|---|
| `societalStockObservation` | Append-only observation of a society-level stock at a valid-time, from a public archive | G6 individualModeled=false · G9 mutable=false · G3 passiveOnlyAttested=true |
| `causalLoopFinding` | A discovered R/B causal loop + current regime (好循環/悪循環/neutral/transitioning) | G5 hypothesisOnly=true · G4 actuationTaken=false |
| `leveragePointFinding` | Meadows leverage-point candidate for a loop | G11 prescriptionGiven=false · G4 actuationTaken=false |
| `regimeShiftEvent` | Detected 好循環⇄悪循環 transition | G7 framingNonEschatological=true · G4 actuationTaken=false |
| `silenJunkanReview` | Quarterly Council self-audit | G4 actuationEventsCount=0 + outwardChannelAcquiredCount=0 · G5/G6/G8/G11 zero-counters |

## Data model note

These records map to **datom / Datalog** entities on canonical **kotoba-kqe**
(ADR-2605262130, Datomic-isomorphic `EAVT/AEVT/AVET/VAET`):
`:junkan.stock/*`, `:junkan.flow/*`, `:junkan.loop/*`. Append-only (G9);
time-travel (`as-of` / `history`) is what makes regime detection possible.
Proprietary Datomic is **not** used (Charter Rider §2(e)+§2(c)).

## The analysis-only spine

junkan has **no outward channel**. The `actuationTaken` / `actuationEventsCount`
/ `outwardChannelAcquiredCount` const fields are the structural teeth: any
nonzero value is a critical violation → cell halt + chigiri.disputeMediation.
Publication beyond Council is performed by *other* actors (ossekai / kataribe)
under G13 — never by junkan itself.
