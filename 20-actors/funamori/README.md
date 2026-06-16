# funamori 舫 — 淡水化発電 (salinity-gradient power)

Marine-renewable **salinity-gradient power**: electricity from the Gibbs free energy released
when fresh river water mixes with seawater. Tier-B actor, ADR-2605265600 (sub-ADR of 2605264100
§4), R0. The previously path-reserved `salinity_gradient_pro_red/` cell, now a runnable method.

## Two methods (`methods/salinity_gradient.cljc`)

| | Principle | Power density (ADR) | Membrane |
|---|---|---|---|
| **PRO** | osmotic pull lifts brine pressure → turbine; `W_max = A·Δπ²/4` at `ΔP=Δπ/2` | 1–3 W/m² | TFC polyamide on polysulfone |
| **RED** | salinity-driven ion flux across CEM/AEM stack → current; `W = E_cell²/(8·R_area)` | 0.5–2 W/m² | SPEEK sulfonated (open-design) |

## The point: ADR constraints are executable

The ADR-2605265600 constitutional gates are **throwing assertions**, not prose:

```clojure
(require '[funamori.methods.salinity-gradient :as sg])

;; 木曽川河口 reference site, in-house PRO membrane, 30 kW
(sg/evaluate-site
  {:pair (sg/make-source-pair :draw-g-l 36.5 :feed-g-l 0.5)
   :membrane (sg/make-pro-membrane :water-permeability 1.0e-12)
   :power-density-w-m2 1.5
   :total-membrane-area-m2 20000.0})
;; => {:permitted true :technology :pro :rated-kw 30.0 :delta-pi-bar 30.0 ...}

;; commercial Toray membrane → rejected at the gate
(sg/evaluate-site {:pair ... :membrane (sg/make-pro-membrane :vendor "Toray") ...})
;; => {:permitted false :violation :commercial-membrane :message "..."}
```

Gates: open-membrane mandatory (§1.1) · no Toray/Hydranautics/GE-Power/Statkraft (§2) ·
no PFAS/Nafion (§1.2) · Δsalinity ≥30 g/L (§1.4) · power-density ≥1 W/m² (§1.6) ·
≤50 kW & ≤1 site through R3 (§1.9).

## Test

```sh
./run_tests.sh    # 24 tests / 57 assertions, babashka
```

## Status

R0 = design + runnable method + gates + kotoba EAVT schema/seed + 3 lexicons. No hardware;
bench pilot is R1 (Council + membrane-chemist + mizuho R2 attested site gated). See `MATURITY.md`.

Apache-2.0 + etzhayyim Charter Compliance Rider v3.1.
