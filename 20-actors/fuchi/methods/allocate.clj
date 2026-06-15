;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/fuchi/methods/allocate.py (unit_refactor stage 0)
;; allocate.py — 扶持 (fuchi) maintainer sustenance allocation. ADR-2606052300.
(ns root.fuchi.methods.allocate
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare tenure-cap-years assert-instrument maintainer allocation capped-tenure-years hazard tenure-weight floor-decay allocate cohort-from-seed)

(def TENURE_CAP_YEARS 40.0)
(def HAZARD_MIN 1.0)
(def HAZARD_MAX 2.0)
(def HORIZON_YEARS 5.0)
(def ALLOWED_INSTRUMENTS (set ["in-kind-grant" "sustenance" "tooling-access" "compute-access"]))
(def FORBIDDEN_INSTRUMENTS (set ["equity" "debt" "convertible" "revenue-share" "profit-claim" "carry" "dividend" "loan" "interest" "warrant" "option" "exit"]))

;; TODO: port-failed unit assert_instrument (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp69_ixtm3/scratch.clj:3:16: w)
;; def assert_instrument(instrument: str) -> str:
;;     """G1 INVARIANT — only a sustenance instrument is allocatable. Anything resembling an
;;     investment / debt / return claim is a ValueError (not an investment fund)."""
;;     instr = str(instrument or "").lstrip(":").lower()
;;     if instr in FORBIDDEN_INSTRUMENTS:
;;         raise ValueError(
;;             f"G1: instrument {instr!r} is an investment/return vehicle — UNREPRESENTABLE "
;;             "(扶持 is sustenance, not a fund; Charter-Rider §2(b))"
;;         )
;;     if instr not in ALLOWED_INSTRUMENTS:
;;         raise ValueError(f"G1: instrument {instr!r} not in {ALLOWED_INSTRUMENTS}")
;;     return instr
(defn assert-instrument [& _]
  (throw (ex-info "TODO: port-failed" {:from "assert_instrument"})))

;; TODO: port-failed unit Maintainer (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpv7_1ai79/scratch.clj:4:19: e)
;; class Maintainer:
;;     did: str
;;     tenure_months: int            # 勤続 months of mission service
;;     hazard_permille: int          # [1000, 2000] -> 1.0 .. 2.0 toil-hazard
;;     maintains: tuple[str, ...] = ()      # actor handles kept alive
;;     prior_imputed_usd_micros_yr: int = 0  # in-kind valuation only; NEVER cash
;;     covenant: str = "vowed"       # "outreach" (minimal floor) | "vowed" (full sustenance)
;;     owns_payoff: bool = False     # G5 — structurally False; work product is commons
(defn maintainer [& _]
  (throw (ex-info "TODO: port-failed" {:from "Maintainer"})))

(defn allocation
  [maintainer-did instrument weight share priority-rank floor-usd-micros-yr cash-usd-micros server-held-key]
  (let [data {:maintainer-did maintainer-did
               :instrument instrument
               :weight weight
               :share share
               :priority-rank priority-rank
               :floor-usd-micros-yr floor-usd-micros-yr
               :cash-usd-micros cash-usd-micros
               :server-held-key server-held-key}]
    (if (not= (:cash-usd-micros data) 0)
      (throw (ex-info "cash≡0 INVARIANT (G2/N4): 扶持 never disburses cash" {:cash-usd-micros (:cash-usd-micros data)}))
      (if (:server-held-key data)
        (throw (ex-info "no-server-key INVARIANT (G9): allocation is member/Council-signed" {:server-held-key (:server-held-key data)}))
        (let [valid? (assert-instrument (:instrument data))]
          (if valid?
            data
            (throw (ex-info "Invalid instrument" {:instrument (:instrument data)})))))))

(defn allocation-constructor
  [maintainer-did instrument weight share priority-rank floor-usd-micros-yr]
  (allocation maintainer-did instrument weight share priority-rank floor-usd-micros-yr 0 false)))

(defn capped-tenure-years [tenure-months]
  (min (/ (float tenure-months) 12.0) TENURE_CAP_YEARS))

(defn _hazard [hazard-permille]
  (let [h (/ (float hazard-permille) 1000.0)]
    (if (or (< h HAZARD_MIN) (> h HAZARD_MAX))
      (throw (ex-info (str "hazard out of [1.0,2.0]: " h) {:h h}))
      h)))

;; TODO: port-failed unit tenure_weight (bb-compile error)
;; def tenure_weight(m: Maintainer) -> float:
;;     """w = ln(1 + min(tenure_years, cap)) * hazard. Log compresses the gradient so a 40y
;;     maintainer is ~2x a 5y one (not 8x) — honours service without a per-person income
;;     leaderboard (ADR-2605261000 N6; same curve as Displacement Dividend)."""
;;     return math.log1p(_capped_tenure_years(m.tenure_months)) * _hazard(m.hazard_permille)
(defn tenure-weight [& _]
  (throw (ex-info "TODO: port-failed" {:from "tenure_weight"})))

;; TODO: port-failed unit floor_decay (zebulun: timed out)
;; def floor_decay(elapsed_months: int) -> float:
;;     """decay(t) = clamp(1 - t/HORIZON, 0, 1). The sustenance floor tapers over 5 years as
;;     the maintainer ascends the Liberation Ladder toward full Basic High Income."""
;;     t = elapsed_months / 12.0
;;     return max(0.0, min(1.0, 1.0 - t / HORIZON_YEARS))
(defn floor-decay [& _]
  (throw (ex-info "TODO: port-failed" {:from "floor_decay"})))

;; TODO: port-failed unit allocate (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmprxq4le4z/scratch.clj:4:16: w)
;; def allocate(
;;     cohort: list[Maintainer],
;;     stage_ceiling_usd_micros_yr: int,
;;     elapsed_months: int = 0,
;;     instrument: str = "sustenance",
;; ) -> list[Allocation]:
;;     """Allocate tenure-weighted in-kind sustenance over a maintainer cohort.
;; 
;;     Only `vowed` maintainers join the tenure-weighted share pool (the covenant gate, G4).
;;     `outreach` maintainers receive a minimal floor (share 0) until they vow — they are not
;;     abandoned, but the full tenure-weighted sustenance is covenant-bound.
;; 
;;     Returns Allocations whose `cash_usd_micros` is structurally 0. Raises if any maintainer
;;     claims `owns_payoff` (G5) or if `instrument` is an investment vehicle (G1).
;;     """
;;     instr = assert_instrument(instrument)
;;     if any(m.owns_payoff for m in cohort):
;;         raise ValueError("G5: a maintainer cannot own the payoff — work product is commons")
;; 
;;     vowed = [m for m in cohort if m.covenant == "vowed"]
;;     total_w = sum(tenure_weight(m) for m in vowed)
;;     decay = floor_decay(elapsed_months)
;;     ranked = sorted(vowed, key=tenure_weight, reverse=True)
;;     rank_of = {m.did: i + 1 for i, m in enumerate(ranked)}
;; 
;;     out: list[Allocation] = []
;;     for m in cohort:
;;         if m.covenant == "vowed":
;;             w = tenure_weight(m)
;;             share = (w / total_w) if total_w > 0 else 0.0
;;             rank = rank_of[m.did]
;;             floor = min(m.prior_imputed_usd_micros_yr, stage_ceiling_usd_micros_yr)
;;             floor = int(round(floor * decay))
;;         else:  # outreach — minimal floor, no share (pre-vow)
;;             w = 0.0
;;             share = 0.0
;;             rank = len(vowed) + 1
;;             floor = int(round(min(m.prior_imputed_usd_micros_yr,
;;                                   stage_ceiling_usd_micros_yr) * decay * 0.25))
;;         out.append(Allocation(
;;             maintainer_did=m.did,
;;             instrument=instr,
;;             weight=round(w, 6),
;;             share=round(share, 6),
;;             priority_rank=rank,
;;             floor_usd_micros_yr=floor,
;;             cash_usd_micros=0,
;;             server_held_key=False,
;;         ))
;;     # vowed allocations first (priority order), then outreach
;;     out.sort(key=lambda a: (a.priority_rank, -a.weight))
;;     return out
(defn allocate [& _]
  (throw (ex-info "TODO: port-failed" {:from "allocate"})))

;; TODO: port-failed unit cohort_from_seed (assembled-lint error)
;; def cohort_from_seed(records: list[dict]) -> list[Maintainer]:
;;     """Build a cohort from seed :maintainer/* maps (edn keyword-keyed)."""
;;     def kw(v):
;;         return str(v or "").lstrip(":").split("/")[-1].lower()
;;     out = []
;;     for r in records:
;;         out.append(Maintainer(
;;             did=r.get(":maintainer/did", "?"),
;;             tenure_months=int(r.get(":maintainer/tenure-months", 0)),
;;             hazard_permille=int(r.get(":maintainer/hazard-permille", 1000)),
;;             maintains=tuple(r.get(":maintainer/maintains", []) or []),
;;             prior_imputed_usd_micros_yr=int(r.get(":maintainer/prior-imputed-usd-micros-yr", 0)),
;;             covenant=kw(r.get(":maintainer/covenant", ":vowed")),
;;             owns_payoff=bool(r.get(":maintainer/owns-payoff", False)),
;;         ))
;;     return out
(defn cohort-from-seed [& _]
  (throw (ex-info "TODO: port-failed" {:from "cohort_from_seed"})))

