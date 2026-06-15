;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ake/methods/revision.py (unit_refactor stage 0)
;; revision.py — 朱 (ake) append-only revision history. ADR-2606052100.
(ns root.ake.methods.revision
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare rev append-revision promote-sourcing revert history-of as-of current)

(defn _rev [entity attr value sourcing as-of by op edit-id]
  (let [sourcing-val (if sourcing (str ":" sourcing) ":representative")
        op-val (str ":" op)]
    {:revision/entity entity
     :revision/attr attr
     :revision/value value
     :revision/sourcing sourcing-val
     :revision/as-of (int as-of)
     :revision/by by
     :revision/op op-val
     :revision/edit edit-id}))

;; TODO: port-failed unit append_revision (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpefugcd7p/scratch.clj:4:8: er)
;; def append_revision(history: list[dict], edit: dict, as_of: int) -> list[dict]:
;;     """Append a revision for an accepted edit. Returns a NEW list (G5 — never mutates/shrinks)."""
;;     rev = _rev(
;;         entity=edit.get(":edit/target-entity", "?"),
;;         attr=_kw(edit.get(":edit/target-attr", "")),
;;         value=str(edit.get(":edit/proposed-value", "")),
;;         sourcing=edit.get(":edit/sourcing", ":representative"),
;;         as_of=as_of,
;;         by=edit.get(":edit/author", "?"),
;;         op=edit.get(":edit/op", ":assert"),
;;         edit_id=edit.get(":edit/id", "?"),
;;     )
;;     return list(history) + [rev]
(defn append-revision [& _]
  (throw (ex-info "TODO: port-failed" {:from "append_revision"})))

;; TODO: port-failed unit promote_sourcing (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp1t3l_39z/scratch.clj:18:8: e)
;; def promote_sourcing(history: list[dict], entity: str, attr: str, provenance: str,
;;                      as_of: int, by: str, edit_id: str) -> list[dict]:
;;     """Promote the current value of (entity, attr) :representative → :authoritative (G4).
;; 
;;     Appends a NEW authoritative revision carrying the current value; the prior representative
;;     revision is left untouched (non-destructive). Raises if provenance is not verifiable, or if
;;     there is no current value to promote.
;;     """
;;     if not _verifiable_provenance(provenance):
;;         raise ValueError("G4: promotion to :authoritative requires verifiable provenance (URL/CID)")
;;     cur = current(history, entity, _kw(attr))
;;     if cur is None:
;;         raise ValueError(f"nothing to promote: no current revision for {entity}:{_kw(attr)}")
;;     rev = _rev(entity, _kw(attr), cur.get(":revision/value", ""), ":authoritative",
;;                as_of, by, ":promote-sourcing", edit_id)
;;     return list(history) + [rev]
(defn promote-sourcing [& _]
  (throw (ex-info "TODO: port-failed" {:from "promote_sourcing"})))

;; TODO: port-failed unit revert (assembled-lint error)
;; def revert(history: list[dict], entity: str, attr: str, by: str, edit_id: str,
;;            as_of: int) -> list[dict]:
;;     """Roll back the CURRENT revision of (entity, attr) to its predecessor (edit-war resolution).
;; 
;;     The Wikipedia 'revert/rollback', append-only: when a `:challenge` of the current value is
;;     upheld by a vote, the challenged revision is UNDONE by appending a NEW revision that restores
;;     the predecessor's value (op `:retract`). Nothing is deleted — the challenged revision remains in
;;     the history at its own `as-of`, so the edit war is fully auditable (danjo-observable). Reverting
;;     the very first revision restores the empty pre-existence state.
;; 
;;     Raises if there is nothing to revert.
;;     """
;;     hist = history_of(history, entity, _kw(attr))
;;     if not hist:
;;         raise ValueError(f"nothing to revert: no revision for {entity}:{_kw(attr)}")
;;     prior = hist[-2] if len(hist) >= 2 else None
;;     restored_value = prior.get(":revision/value", "") if prior else ""
;;     restored_sourcing = prior.get(":revision/sourcing", ":representative") if prior else ":representative"
;;     rev = _rev(entity, _kw(attr), restored_value, restored_sourcing,
;;                as_of, by, ":retract", edit_id)
;;     return list(history) + [rev]
(defn revert [& _]
  (throw (ex-info "TODO: port-failed" {:from "revert"})))

;; TODO: port-failed unit history_of (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpujfxtrkt/scratch.clj:5:24: w)
;; def history_of(history: list[dict], entity: str, attr: str) -> list[dict]:
;;     """Full ordered revision history for (entity, attr) — the 'view history' tab."""
;;     attr = _kw(attr)
;;     rows = [r for r in history
;;             if r.get(":revision/entity") == entity and _kw(r.get(":revision/attr", "")) == attr]
;;     return sorted(rows, key=lambda r: int(r.get(":revision/as-of", 0)))
(defn history-of [& _]
  (throw (ex-info "TODO: port-failed" {:from "history_of"})))

;; TODO: port-failed unit as_of (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpu5lkh9io/scratch.clj:3:14: e)
;; def as_of(history: list[dict], entity: str, attr: str, ts: int) -> dict | None:
;;     """The value of (entity, attr) as it stood at instant `ts` (time-travel read)."""
;;     rows = [r for r in history_of(history, entity, attr) if int(r.get(":revision/as-of", 0)) <= ts]
;;     return rows[-1] if rows else None
(defn as-of [& _]
  (throw (ex-info "TODO: port-failed" {:from "as_of"})))

(defn current [history entity attr]
  "The latest revision for (entity, attr)."
  (let [rows (history-of history entity attr)]
    (if (seq rows)
      (last rows)
      nil)))

