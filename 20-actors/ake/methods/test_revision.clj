;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ake/methods/test_revision.py (unit_refactor stage 0)
;; Tests for revision.py — append-only history, time-travel reads, non-destructive promotion (G5).
(ns root.ake.methods.test-revision
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare seed e test-append-returns-new-list-and-never-shrinks test-current-is-latest-as-of test-as-of-time-travel test-history-of-is-ordered-and-full test-promote-sourcing-is-non-destructive test-promote-requires-verifiable-provenance test-promote-with-nothing-to-promote-raises)

;; TODO: port-failed unit _SEED (bb-compile error)
;; _SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-edit-graph.kotoba.edn"
(def seed nil) ;; TODO: port-failed const

;; TODO: port-failed unit _e (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpjwdetkpg/scratch.clj:3:21: w)
;; def _e(eid):
;;     return {e[":edit/id"]: e for e in load_edn(_SEED)[":edit/batch"]}[eid]
(defn e [& _]
  (throw (ex-info "TODO: port-failed" {:from "_e"})))

;; TODO: port-failed unit test_append_returns_new_list_and_never_shrinks (assembled-lint error)
;; def test_append_returns_new_list_and_never_shrinks():
;;     h0: list = []
;;     h1 = append_revision(h0, _e("e1"), as_of=100)
;;     assert len(h0) == 0 and len(h1) == 1          # input untouched
;;     h2 = append_revision(h1, _e("e3"), as_of=110)
;;     assert len(h2) == 2 and len(h1) == 1
(defn test-append-returns-new-list-and-never-shrinks [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_append_returns_new_list_and_never_shrinks"})))

;; TODO: port-failed unit test_current_is_latest_as_of (assembled-lint error)
;; def test_current_is_latest_as_of():
;;     h = []
;;     h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "old"}, as_of=100)
;;     h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "new"}, as_of=200)
;;     cur = current(h, "org.corp.tsmc", "hq-address")
;;     assert cur[":revision/value"] == "new"
(defn test-current-is-latest-as-of [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_current_is_latest_as_of"})))

;; TODO: port-failed unit test_as_of_time_travel (assembled-lint error)
;; def test_as_of_time_travel():
;;     h = []
;;     h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "old"}, as_of=100)
;;     h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "new"}, as_of=200)
;;     assert as_of(h, "org.corp.tsmc", "hq-address", 150)[":revision/value"] == "old"
;;     assert as_of(h, "org.corp.tsmc", "hq-address", 250)[":revision/value"] == "new"
;;     assert as_of(h, "org.corp.tsmc", "hq-address", 50) is None
(defn test-as-of-time-travel [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_as_of_time_travel"})))

;; TODO: port-failed unit test_history_of_is_ordered_and_full (assembled-lint error)
;; def test_history_of_is_ordered_and_full():
;;     h = []
;;     h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "v1"}, as_of=300)
;;     h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "v2"}, as_of=100)
;;     h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "v3"}, as_of=200)
;;     hist = history_of(h, "org.corp.tsmc", "hq-address")
;;     assert [r[":revision/as-of"] for r in hist] == [100, 200, 300]   # sorted, nothing dropped
(defn test-history-of-is-ordered-and-full [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_history_of_is_ordered_and_full"})))

;; TODO: port-failed unit test_promote_sourcing_is_non_destructive (assembled-lint error)
;; def test_promote_sourcing_is_non_destructive():
;;     h = []
;;     h = append_revision(h, {**_e("e1"), ":edit/sourcing": ":representative",
;;                             ":edit/proposed-value": "addr"}, as_of=100)
;;     before = len(h)
;;     h2 = promote_sourcing(h, "org.corp.tsmc", "hq-address",
;;                           provenance="https://tsmc.com/profile", as_of=200, by="did:member:x",
;;                           edit_id="ePromote")
;;     assert len(h2) == before + 1                       # appended, not replaced
;;     assert current(h2, "org.corp.tsmc", "hq-address")[":revision/sourcing"] == ":authoritative"
;;     # the representative revision still exists at its own as-of
;;     assert as_of(h2, "org.corp.tsmc", "hq-address", 150)[":revision/sourcing"] == ":representative"
(defn test-promote-sourcing-is-non-destructive [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_promote_sourcing_is_non_destructive"})))

;; TODO: port-failed unit test_promote_requires_verifiable_provenance (levi: timed out)
;; def test_promote_requires_verifiable_provenance():
;;     h = append_revision([], _e("e1"), as_of=100)
;;     try:
;;         promote_sourcing(h, "org.corp.tsmc", "hq-address", provenance="trust me",
;;                          as_of=200, by="did:member:x", edit_id="eP")
;;         assert False, "expected ValueError"
;;     except ValueError as ex:
;;         assert "G4" in str(ex)
(defn test-promote-requires-verifiable-provenance [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_promote_requires_verifiable_provenance"})))

;; TODO: port-failed unit test_promote_with_nothing_to_promote_raises (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp2ks8x6_u/scratch.clj:4:6: wa)
;; def test_promote_with_nothing_to_promote_raises():
;;     try:
;;         promote_sourcing([], "org.corp.none", "x", provenance="https://e.com",
;;                          as_of=1, by="did:member:x", edit_id="eP")
;;         assert False, "expected ValueError"
;;     except ValueError as ex:
;;         assert "nothing to promote" in str(ex)
(defn test-promote-with-nothing-to-promote-raises [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_promote_with_nothing_to_promote_raises"})))

