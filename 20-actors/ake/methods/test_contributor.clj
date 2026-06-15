;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/ake/methods/test_contributor.py (unit_refactor stage 0)
;; Tests for contributor.py — anti-vandalism rate + recoverable Wellbecoming trajectory (G9).
(ns root.ake.methods.test-contributor
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare test-record-is-append-only-and-non-mutating test-record-rejects-bad-outcome test-acceptance-rate test-rate-limit-blocks-a-flood test-throttle-only-on-an-unbroken-refusal-run test-throttle-is-recoverable test-new-contributor-is-never-throttled test-trajectory-view-shape test-contributors-are-isolated-no-cross-did-leak test-no-ranking-or-score-of-soul-api-exists test-events-are-returned-in-as-of-order-regardless-of-record-order test-throttle-recovers-with-a-recent-accept-amid-later-refusals test-rate-window-lower-edge-is-exclusive)

;; TODO: port-failed unit test_record_is_append_only_and_non_mutating (assembled-lint error)
;; def test_record_is_append_only_and_non_mutating():
;;     t0 = contrib.empty()
;;     t1 = contrib.record(t0, "did:m:a", "accepted", 100)
;;     assert t0 == {} and contrib.counts(t1, "did:m:a") == {"accepted": 1, "refused": 0}
;;     t2 = contrib.record(t1, "did:m:a", "refused", 200)
;;     assert contrib.counts(t1, "did:m:a")["refused"] == 0     # t1 untouched
;;     assert contrib.counts(t2, "did:m:a") == {"accepted": 1, "refused": 1}
(defn test-record-is-append-only-and-non-mutating [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_record_is_append_only_and_non_mutating"})))

;; TODO: port-failed unit test_record_rejects_bad_outcome (assembled-lint error)
;; def test_record_rejects_bad_outcome():
;;     try:
;;         contrib.record(contrib.empty(), "did:m:a", "maybe", 1)
;;         assert False, "expected ValueError"
;;     except ValueError:
;;         pass
(defn test-record-rejects-bad-outcome [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_record_rejects_bad_outcome"})))

;; TODO: port-failed unit test_acceptance_rate (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpcohjk_lu/scratch.clj:3:12: w)
;; def test_acceptance_rate():
;;     t = contrib.empty()
;;     assert contrib.acceptance_rate(t, "did:m:a") is None        # no events
;;     for o in ("accepted", "accepted", "refused"):
;;         t = contrib.record(t, "did:m:a", o, 1)
;;     assert contrib.acceptance_rate(t, "did:m:a") == round(2 / 3, 4)
(defn test-acceptance-rate [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_acceptance_rate"})))

;; TODO: port-failed unit test_rate_limit_blocks_a_flood (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpnuh4lbtx/scratch.clj:3:12: w)
;; def test_rate_limit_blocks_a_flood():
;;     t = contrib.empty()
;;     for i in range(contrib.RATE_MAX_IN_WINDOW):
;;         t = contrib.record(t, "did:m:flood", "accepted", 1000 + i)
;;     # the ceiling is reached within the window → next is blocked
;;     assert not contrib.rate_ok(t, "did:m:flood", now=1000 + contrib.RATE_MAX_IN_WINDOW)
;;     # but far in the future the window has slid past → allowed again
;;     assert contrib.rate_ok(t, "did:m:flood", now=1000 + contrib.RATE_WINDOW + 10_000)
(defn test-rate-limit-blocks-a-flood [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_rate_limit_blocks_a_flood"})))

;; TODO: port-failed unit test_throttle_only_on_an_unbroken_refusal_run (assembled-lint error)
;; def test_throttle_only_on_an_unbroken_refusal_run():
;;     t = contrib.empty()
;;     for i in range(contrib.THROTTLE_REFUSED_RUN):
;;         t = contrib.record(t, "did:m:vandal", "refused", 100 + i)
;;     assert contrib.is_throttled(t, "did:m:vandal")
(defn test-throttle-only-on-an-unbroken-refusal-run [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_throttle_only_on_an_unbroken_refusal_run"})))

;; TODO: port-failed unit test_throttle_is_recoverable (assembled-lint error)
;; def test_throttle_is_recoverable():
;;     # a run of refusals throttles…
;;     t = contrib.empty()
;;     for i in range(contrib.THROTTLE_REFUSED_RUN):
;;         t = contrib.record(t, "did:m:x", "refused", 100 + i)
;;     assert contrib.is_throttled(t, "did:m:x")
;;     # …but a single subsequent accepted edit breaks the run → un-throttled (no score-of-soul)
;;     t = contrib.record(t, "did:m:x", "accepted", 999)
;;     assert not contrib.is_throttled(t, "did:m:x")
(defn test-throttle-is-recoverable [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_throttle_is_recoverable"})))

;; TODO: port-failed unit test_new_contributor_is_never_throttled (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp1luqahke/scratch.clj:4:5: er)
;; def test_new_contributor_is_never_throttled():
;;     t = contrib.record(contrib.empty(), "did:m:new", "refused", 1)
;;     assert not contrib.is_throttled(t, "did:m:new")    # too few events to judge
(defn test-new-contributor-is-never-throttled [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_new_contributor_is_never_throttled"})))

;; TODO: port-failed unit test_trajectory_view_shape (assembled-lint error)
;; def test_trajectory_view_shape():
;;     t = contrib.record(contrib.empty(), "did:m:a", "accepted", 1)
;;     v = contrib.trajectory(t, "did:m:a")
;;     assert v["did"] == "did:m:a" and v["accepted"] == 1 and v["throttled"] is False
;;     assert "acceptanceRate" in v and "events" in v
(defn test-trajectory-view-shape [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_trajectory_view_shape"})))

;; TODO: port-failed unit test_contributors_are_isolated_no_cross_did_leak (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp4hc6djam/scratch.clj:3:12: w)
;; def test_contributors_are_isolated_no_cross_did_leak():
;;     # one DID's flood/refusals must NOT change another DID's trajectory or throttle state —
;;     # the membrane judges each contributor only against their OWN history, never a leaderboard.
;;     t = contrib.empty()
;;     for i in range(contrib.THROTTLE_REFUSED_RUN):
;;         t = contrib.record(t, "did:m:vandal", "refused", 100 + i)
;;     t = contrib.record(t, "did:m:saint", "accepted", 200)
;;     assert contrib.is_throttled(t, "did:m:vandal")
;;     assert not contrib.is_throttled(t, "did:m:saint")
;;     assert contrib.counts(t, "did:m:saint") == {"accepted": 1, "refused": 0}
;;     assert contrib.trajectory(t, "did:m:saint")["throttled"] is False
(defn test-contributors-are-isolated-no-cross-did-leak [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_contributors_are_isolated_no_cross_did_leak"})))

;; TODO: port-failed unit test_no_ranking_or_score_of_soul_api_exists (assembled-lint error)
;; def test_no_ranking_or_score_of_soul_api_exists():
;;     # G9 forbids a minted reputation number or a contributor ranking. Lock the surface:
;;     # no public helper may imply ordering/comparison/scoring of contributors against each other.
;;     forbidden = ("rank", "leaderboard", "compare", "score", "reputation", "best", "worst", "top")
;;     public = [n for n in dir(contrib) if not n.startswith("_") and callable(getattr(contrib, n))]
;;     leaks = [n for n in public for f in forbidden if f in n.lower()]
;;     assert not leaks, f"G9: ranking/score-of-soul-shaped API leaked: {leaks}"
(defn test-no-ranking-or-score-of-soul-api-exists [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_no_ranking_or_score_of_soul_api_exists"})))

;; TODO: port-failed unit test_events_are_returned_in_as_of_order_regardless_of_record_order (bb-compile error)
;; def test_events_are_returned_in_as_of_order_regardless_of_record_order():
;;     t = contrib.empty()
;;     for outcome, ts in (("accepted", 300), ("refused", 100), ("accepted", 200)):
;;         t = contrib.record(t, "did:m:a", outcome, ts)
;;     order = [e["as_of"] for e in contrib.events(t, "did:m:a")]
;;     assert order == [100, 200, 300]
(defn test-events-are-returned-in-as-of-order-regardless-of-record-order [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_events_are_returned_in_as_of_order_regardless_of_record_order"})))

;; TODO: port-failed unit test_throttle_recovers_with_a_recent_accept_amid_later_refusals (bb-compile error)
;; def test_throttle_recovers_with_a_recent_accept_amid_later_refusals():
;;     # an accept anywhere inside the recent window breaks the run — even if more refusals follow,
;;     # so long as the accept stays within the last THROTTLE_RECENT outcomes (recoverable, not sticky).
;;     t = contrib.empty()
;;     seq = ["refused"] * 3 + ["accepted"] + ["refused"] * 3   # accept sits inside the last 5
;;     for i, o in enumerate(seq):
;;         t = contrib.record(t, "did:m:x", o, 100 + i)
;;     assert not contrib.is_throttled(t, "did:m:x")
(defn test-throttle-recovers-with-a-recent-accept-amid-later-refusals [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_throttle_recovers_with_a_recent_accept_amid_later_refusals"})))

;; TODO: port-failed unit test_rate_window_lower_edge_is_exclusive (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpotmwa9mc/scratch.clj:3:8: er)
;; def test_rate_window_lower_edge_is_exclusive():
;;     # an event exactly at (now - window) has aged OUT of the sliding window (strict `>`),
;;     # so it does not count toward the flood ceiling.
;;     t = contrib.empty()
;;     for i in range(contrib.RATE_MAX_IN_WINDOW):
;;         t = contrib.record(t, "did:m:edge", "accepted", 1000 + i)
;;     now = 1000 + contrib.RATE_WINDOW          # oldest event (t=1000) is now exactly at the edge
;;     assert contrib.rate_ok(t, "did:m:edge", now=now)  # edge event excluded → under ceiling again
(defn test-rate-window-lower-edge-is-exclusive [& _]
  (throw (ex-info "TODO: port-failed" {:from "test_rate_window_lower_edge_is_exclusive"})))

