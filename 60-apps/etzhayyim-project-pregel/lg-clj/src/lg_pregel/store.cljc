(ns lg-pregel.store
  "Injectable HITL store seam for the pregel server — clj port of the kotodama
  helper calls in `lg/lg_pregel/server.py` (ADR-2606280030).

  The Python server reaches into the external `kotodama` package for its
  human-in-the-loop state:

    outlook_gray_review/list_pending_gray  get_gray_item  apply_verdict
    outlook_reply_draft/list_pending_drafts get_draft_item apply_draft_verdict
    outlook_stats/get_all_stats

  Those helpers persist to RisingWave via psycopg. DEVIATION (noted): the repo's
  substrate boundary FORBIDS RisingWave (deprecated per ADR-2605262130); the
  canonical state is the kotoba Datom log. So this port exposes the HITL backend
  as a SWAPPABLE map of functions (`*store*`) — the actor swap pattern — whose
  default is read-only / empty so the dispatch surface + envelope shaping verify
  offline under bb. Production rebinds `*store*` to a kotoba-Datom-log adapter
  (`:db-api` driven, append-only audit ledger) WITHOUT touching the routing.

  Keys (all pure data in / data out):
    :list-pending-gray   (limit)            -> [item ...]
    :list-pending-drafts (limit)            -> [item ...]
    :get-gray-item       (thread-id)        -> item | nil
    :get-draft-item      (thread-id)        -> item | nil
    :apply-verdict       (thread-id verdict)               -> any (commit)
    :apply-draft-verdict (thread-id action final-text)     -> any (commit)
    :get-all-stats       (days)             -> stats-map")

(def default-store
  "Read-only / empty default (no RisingWave, no live kotodama). Safe offline."
  {:list-pending-gray   (fn [_limit] [])
   :list-pending-drafts (fn [_limit] [])
   :get-gray-item       (fn [_thread-id] nil)
   :get-draft-item      (fn [_thread-id] nil)
   :apply-verdict       (fn [_thread-id _verdict] {:ok true})
   :apply-draft-verdict (fn [_thread-id _action _final-text] {:ok true})
   :get-all-stats       (fn [days] {:days days :stats []})})

(def ^:dynamic *store* default-store)

(defn store [] *store*)

(defn call
  "Invoke store fn `k` with `args` against the currently-bound `*store*`."
  [k & args]
  (apply (get *store* k) args))
