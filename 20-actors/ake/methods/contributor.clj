;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ake/methods/contributor.py (unit_refactor stage 0)
;; contributor.py — 朱 (ake) anti-vandalism rate + Wellbecoming trajectory (G9). ADR-2606052100.
(ns root.ake.methods.contributor
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare rate-window empty record events counts acceptance-rate rate-ok is-throttled trajectory)

(def RATE-WINDOW 3600)          ;; seconds
(def RATE-MAX-IN-WINDOW 20)     ;; proposals per DID per window
(def THROTTLE-RECENT 5)         ;; look at the last N outcomes
(def THROTTLE-REFUSED-RUN 5)    ;; …throttle only if ALL of the last N were refused (a clear run)
(def _ACCEPT "accepted")
(def _REFUSE "refused")

(defn empty []
  "A fresh trajectory store: {did -> [event, ...]}, event = {outcome, as_of}."
  {})

;; TODO: port-failed unit record (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpcdk3ixzk/scratch.clj:3:18: w)
;; def record(traj: dict, did: str, outcome: str, as_of: int) -> dict:
;;     """Append one outcome event for `did`. Returns a NEW dict (append-only, never mutates)."""
;;     outcome = str(outcome).lstrip(":")
;;     if outcome not in (_ACCEPT, _REFUSE):
;;         raise ValueError(f"outcome must be {_ACCEPT!r} or {_REFUSE!r}, not {outcome!r}")
;;     new = {k: list(v) for k, v in traj.items()}
;;     new.setdefault(did, []).append({"outcome": outcome, "as_of": int(as_of)})
;;     return new
(defn record [& _]
  (throw (ex-info "TODO: port-failed" {:from "record"})))

;; TODO: port-failed unit events (assembled-lint error)
;; def events(traj: dict, did: str) -> list[dict]:
;;     return sorted(traj.get(did, []), key=lambda e: int(e["as_of"]))
(defn events [& _]
  (throw (ex-info "TODO: port-failed" {:from "events"})))

(defn counts [traj did]
  (let [evs (get traj did [])
        acc (reduce + (map #(if (= (:outcome %) _ACCEPT) 1 0) evs))
        ref (reduce + (map #(if (= (:outcome %) _REFUSE) 1 0) evs))]
    {"accepted" acc "refused" ref}))

(defn acceptance-rate [traj did]
  (let [c (counts traj did)
        total (+ (:accepted c) (:refused c))]
    (if (= total 0)
      nil
      (let [res (/ (:accepted c) total)]
        (Math/round (* res 10000.0) 4) / 10000.0))))

(defn rate-ok [traj did now {:keys [window max-in-window]}]
  "True if `did` may submit one more proposal at `now` without exceeding the flood ceiling."
  (let [history (get traj did nil)
        window-start (- now window)
        recent (filter #(> (int (get % "as_of")) window-start) history)]
    (< (count recent) max-in-window)))

;; TODO: port-failed unit is_throttled (assembled-lint error)
;; def is_throttled(traj: dict, did: str,
;;                  recent: int = THROTTLE_RECENT, refused_run: int = THROTTLE_REFUSED_RUN) -> bool:
;;     """Throttled ⟺ the last `recent` outcomes exist and are an unbroken run of refusals.
;; 
;;     RECOVERABLE by construction: a single accepted edit anywhere in the recent window breaks the
;;     run, so a contributor un-throttles themselves by proposing well again. This is a behavioural
;;     signal, NOT a stored score and NOT permanent (G9 — no score-of-soul).
;;     """
;;     evs = events(traj, did)
;;     if len(evs) < recent:
;;         return False
;;     tail = evs[-recent:]
;;     return len(tail) >= refused_run and all(e["outcome"] == _REFUSE for e in tail)
(defn is-throttled [& _]
  (throw (ex-info "TODO: port-failed" {:from "is_throttled"})))

;; TODO: port-failed unit trajectory (assembled-lint error)
;; def trajectory(traj: dict, did: str) -> dict:
;;     """A Wellbecoming view (as-of), NOT a ranking: counts + rate + current throttle state."""
;;     return {
;;         "did": did,
;;         **counts(traj, did),
;;         "acceptanceRate": acceptance_rate(traj, did),
;;         "throttled": is_throttled(traj, did),
;;         "events": len(traj.get(did, [])),
;;     }
(defn trajectory [& _]
  (throw (ex-info "TODO: port-failed" {:from "trajectory"})))

