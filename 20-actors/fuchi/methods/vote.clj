;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/fuchi/methods/vote.py (unit_refactor stage 0)
;; vote.py — 扶持 (fuchi) R1(b): real 1 SBT = 1 vote with a 48h timelock.
(ns root.fuchi.methods.vote
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare default-timelock-h ballot kw cast ballots-from-seed tally finalize finalize-binding)

(def default-timelock-h 48)
(def default-quorum 3)
(def choices (set ["yes" "no" "abstain"]))

;; TODO: port-failed unit Ballot (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpb_xgiie4/scratch.clj:2:40: w)
;; class Ballot:
;;     voter_did: str
;;     choice: str
;;     cast_at: int                  # hour stamp
;;     weight: int = 1               # 1 SBT = 1 vote — always 1
;;     server_held_key: bool = False
;; 
;;     def __post_init__(self) -> None:
;;         if self.weight != 1:
;;             raise ValueError("1 SBT = 1 vote INVARIANT: ballot weight must be 1")
;;         if self.server_held_key:
;;             raise ValueError("no-server-key INVARIANT (G9): a ballot is member-signed")
;;         v = self.voter_did.lower()
;;         if v.startswith(("server", "did:server", ":server")) or v in ("server", "anon"):
;;             raise ValueError("G9/G4: a :server / :anon voter is unrepresentable")
;;         if _kw(self.choice) not in CHOICES:
;;             raise ValueError(f"ballot choice {self.choice!r} not in {CHOICES}")
(defn ballot [& _]
  (throw (ex-info "TODO: port-failed" {:from "Ballot"})))

;; TODO: port-failed unit _kw (bb-compile error)
;; def _kw(v) -> str:
;;     return str(v or "").lstrip(":").split("/")[-1].lower()
(defn kw [& _]
  (throw (ex-info "TODO: port-failed" {:from "_kw"})))

(defn cast [ballots ballot]
  "Append a ballot, enforcing 1 SBT = 1 vote (a duplicate voter DID is rejected)."
  (if (some #(= (:voter-did %) (:voter-did ballot)) ballots)
    (throw (ex-info "1 SBT = 1 vote: " (:voter-did ballot) {:ballot ballot}))
    (conj ballots ballot)))

;; TODO: port-failed unit ballots_from_seed (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp0es1ehxg/scratch.clj:2:1: wa)
;; def ballots_from_seed(records: list[dict]) -> list[Ballot]:
;;     """Build ballots from seed maps; rejects duplicate voters (1 SBT = 1 vote)."""
;;     out: list[Ballot] = []
;;     for r in records:
;;         out = cast(out, Ballot(
;;             voter_did=r.get(":ballot/voter", r.get("voter", "?")),
;;             choice=_kw(r.get(":ballot/choice", r.get("choice", "yes"))),
;;             cast_at=int(r.get(":ballot/cast-at", r.get("cast_at", 0))),
;;         ))
;;     return out
(defn ballots-from-seed [& _]
  (throw (ex-info "TODO: port-failed" {:from "ballots_from_seed"})))

;; TODO: port-failed unit tally (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpnvy6uehk/scratch.clj:5:57: w)
;; def tally(
;;     ballots: list[Ballot],
;;     opened_at: int,
;;     now: int,
;;     timelock_h: int = DEFAULT_TIMELOCK_H,
;;     quorum: int = DEFAULT_QUORUM,
;; ) -> dict:
;;     """Tally a vote. Only ballots cast within [opened_at, opened_at+timelock_h] count.
;; 
;;     Outcome:
;;       - pending   if the timelock window has not yet elapsed (now < close);
;;       - rejected  if quorum (yes+no participating) is not met;
;;       - accepted  if finalizable, quorum met, and yes > no;
;;       - rejected  otherwise.
;;     """
;;     close = opened_at + timelock_h
;;     in_window = [b for b in ballots if opened_at <= b.cast_at <= close]
;;     yes = sum(1 for b in in_window if _kw(b.choice) == "yes")
;;     no = sum(1 for b in in_window if _kw(b.choice) == "no")
;;     abstain = sum(1 for b in in_window if _kw(b.choice) == "abstain")
;;     participating = yes + no
;;     finalizable = now >= close
;;     quorum_met = participating >= quorum
;; 
;;     if not finalizable:
;;         outcome = "pending"
;;     elif not quorum_met:
;;         outcome = "rejected"          # never auto-accept on a thin vote
;;     elif yes > no:
;;         outcome = "accepted"
;;     else:
;;         outcome = "rejected"
;; 
;;     return {
;;         "yes": yes, "no": no, "abstain": abstain, "voters": len(in_window),
;;         "opened_at": opened_at, "close": close, "now": now, "timelock_h": timelock_h,
;;         "quorum": quorum, "quorum_met": quorum_met, "finalizable": finalizable,
;;         "outcome": outcome,
;;     }
(defn tally [& _]
  (throw (ex-info "TODO: port-failed" {:from "tally"})))

(defn finalize
  [ballots opened-at now ^:all timelock-h default-timelock-h quorum default-quorum]
  (let [timelock-h (if (nil? timelock-h) default-timelock-h timelock-h)
        quorum (if (nil? quorum) default-quorum quorum)]
    (if (< now (+ opened-at timelock-h))
      (throw (ex-info (str "timelock INVARIANT: cannot finalize before " 
                            (+ opened-at timelock-h) 
                            "h (now=" now 
                            "h, window=" timelock-h 
                            "h)")
                      {:opened-at opened-at :now now :timelock-h timelock-h}))
      (tally ballots opened-at now timelock-h quorum))))

;; TODO: port-failed unit finalize_binding (assembled-lint error)
;; def finalize_binding(
;;     ballots: list[Ballot],
;;     opened_at: int,
;;     now: int,
;;     gate: LiveGate,
;;     *,
;;     timelock_h: int = DEFAULT_TIMELOCK_H,
;;     quorum: int = DEFAULT_QUORUM,
;;     env: dict[str, str] | None = None,
;; ) -> dict:
;;     """Finalize a vote as BINDING (the on-chain outcome), or refuse.
;; 
;;     RAISES `live_gate.LiveGateRefused` unless the operator flag + attestation + Council Lv6+ +
;;     member signature are all present (the default). The 48h timelock still applies strictly (a
;;     binding finalize before the window closes raises `ValueError` via `finalize`), so the gate
;;     cannot be used to short-circuit the timelock. Returns the tally annotated `binding=True`.
;;     """
;;     require(gate, env=env)  # refuses by default
;;     result = finalize(ballots, opened_at, now, timelock_h, quorum)  # strict timelock still applies
;;     return {**result, "binding": True, "ratified_by": gate.operator_did,
;;             "council_level": gate.council_level}
(defn finalize-binding [& _]
  (throw (ex-info "TODO: port-failed" {:from "finalize_binding"})))

