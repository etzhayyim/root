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
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [cheshire.core :as json]
            [etzhayyim.pds.client :as client]))

;; ── ibuki post-queue (ADR-2605240100 §Line schema, v=1) → drain specs ─────────
;; ibuki's react_loop --live already appends NDJSON lines of this shape; the drainer
;; consumes them verbatim so the actor side needs NO change — it just writes its queue.
(def ^:private SCHEMA-VERSION 1)
(def ^:private REQUIRED ["v" "ts" "actorDid" "text" "lexicon" "createdAt"])

(defn queue-line->spec
  "Map one ADR-2605240100 v=1 queue line (a parsed map) to a drain post-spec. The
  queue `ts` is the idempotency key; lexicon is the collection + record $type."
  [m]
  {:key (str (get m "ts"))
   :repo (get m "actorDid")
   :collection (get m "lexicon")
   :record {"$type" (get m "lexicon")
            "text" (get m "text")
            "createdAt" (get m "createdAt")}})

(defn parse-queue
  "Parse NDJSON queue `text` → {:specs [..] :errors [\"line N: ..\"]}. Unknown schema
  versions and missing keys are REJECTED (never guessed), exactly like ibuki's
  drainer; blank lines are skipped."
  [text]
  (reduce
   (fn [acc [i line]]
     (let [line (str/trim line)]
       (if (str/blank? line)
         acc
         (let [m (try (json/parse-string line) (catch Exception _ ::bad))]
           (cond
             (= m ::bad) (update acc :errors conj (str "line " i ": not JSON"))
             (not= (get m "v") SCHEMA-VERSION)
             (update acc :errors conj (str "line " i ": unknown schema version " (pr-str (get m "v"))))
             (seq (remove #(contains? m %) REQUIRED))
             (update acc :errors conj (str "line " i ": missing keys "
                                           (pr-str (vec (remove #(contains? m %) REQUIRED)))))
             :else (update acc :specs conj (queue-line->spec m)))))))
   {:specs [] :errors []}
   (map-indexed vector (str/split-lines (str text)))))

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

(defn run-queue!
  "Parse an ibuki NDJSON queue and drain its valid specs. Returns the `drain!` result
  merged with {:parse-errors [..]}. The operational entry the `bb drain` task wraps."
  [base queue-text opts]
  (let [{:keys [specs errors]} (parse-queue queue-text)]
    (assoc (drain! base specs opts) :parse-errors errors)))

(defn run-file!
  "`bb drain` task entry: drain the NDJSON queue at `:queue-path` to PDS `:base`,
  persisting the posted-key cursor at `:cursor-path` (one key/line) so re-runs are
  idempotent, and writing receipts NDJSON to `:receipts-path`. Stdlib file IO; the
  posting uses the live HTTP client (the actor holds no key — the PDS signs)."
  [{:keys [base queue-path cursor-path receipts-path transport]}]
  (let [seed (if (and cursor-path (.exists (io/file cursor-path)))
               (set (remove str/blank? (str/split-lines (slurp cursor-path)))) #{})
        res (run-queue! base (slurp queue-path)
                        (cond-> {:posted seed} transport (assoc :transport transport)))]
    (when cursor-path (spit cursor-path (str/join "\n" (sort (:posted res)))))
    (when receipts-path
      (spit receipts-path (str/join "\n" (map json/generate-string (:receipts res)))))
    res))
