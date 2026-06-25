(ns etzhayyim.pds.drain
  "Post-queue drainer — the actor-side bridge from a queue of records to the PDS
  (Path B slice 4: react_loop --live → drainer → createRecord). Each queued post is
  submitted through the PDS client; the PDS signs it with the actor's own key.

  IDEMPOTENT by a per-post key (`:key`, e.g. the queue timestamp, falling back to a
  content hash): re-draining the same queue never double-posts, and a post that
  fails (non-200) stays UN-posted so the next drain retries it. The drainer holds no
  key and makes no network call itself — it forwards to `client` over an injectable
  transport, so it is deterministic and offline-testable.

  Stdlib + the PDS client; no external deps."
  (:require [etzhayyim.pds.client :as client]))

(defn post-key
  "A stable idempotency key for a post-spec: the explicit `:key` (the queue's own id —
  preferred), else repo|collection|<content-hash> so re-draining the SAME record is a
  no-op even when the rkey is server-assigned."
  [{:keys [key repo collection record]}]
  (or key (str repo "|" collection "|" (hash record))))

(defn drain!
  "Submit each post-spec `{:repo :collection :record :rkey? :key?}` whose key is not
  already in `posted` (a set). Returns
  `{:receipts [{:key :status :uri :cid :sig :signedBy} ..] :posted <updated set>
    :errors [{:key :status} ..]}`. A non-200 leaves the key UN-posted (retryable);
  an already-posted key is skipped (idempotent)."
  [base specs {:keys [posted transport] :or {posted #{}}}]
  (reduce
   (fn [acc spec]
     (let [k (post-key spec)]
       (if (contains? (:posted acc) k)
         acc                                          ; idempotent: already posted
         (let [res (client/create-record!
                    base (select-keys spec [:repo :collection :record :rkey])
                    :transport transport)]
           (if (= 200 (:status res))
             (-> acc
                 (update :receipts conj (assoc res :key k))
                 (update :posted conj k))
             (update acc :errors conj {:key k :status (:status res)}))))))
   {:receipts [] :posted posted :errors []}
   specs))
