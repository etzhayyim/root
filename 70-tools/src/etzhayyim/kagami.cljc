;; kagami.cljc — Mirror/diff analysis pure logic.
;;
;; Ports the pure-logic subset of etzhayyim-py kagami.py:
;;   - compare          : diff two actor maps → list of change strings
;;   - diff-actors      : diff local vs remote actor maps → seq of KagamiDiff records
;;   - diff-summary     : aggregate stats from a seq of diffs
;;
;; IO (httpx PDS calls, fs walks) is DEFERRED — call from bb operator legs.
;;
;; ns: etzhayyim.kagami
;; Load check: bb --classpath 70-tools/src -e "(require 'etzhayyim.kagami)(println :ok)"

(ns etzhayyim.kagami)

;; ── field comparison ──────────────────────────────────────────────────────────

(def ^:private ^:const comparison-fields
  ["name" "did" "performerType" "uiType" "runtimeType"])

(defn compare-actors
  "Return a vector of human-readable change strings between local and remote actor maps.
   Pure function — no IO.

   Python equivalent: _compare(local, remote) -> list[str]"
  [local remote]
  (let [field-changes
        (for [k comparison-fields
              :let [lv (get local  k "")
                    rv (get remote k "")]
              :when (not= lv rv)]
          (str k ": " (pr-str lv) " → " (pr-str rv)))
        local-cols  (set (get local  "collections" []))
        remote-cols (set (get remote "collections" []))
        added       (sort (remove local-cols  remote-cols))
        removed     (sort (remove remote-cols local-cols))
        col-changes (concat
                     (when (seq added)
                       [(str "collections +" (count added) ": "
                             (clojure.string/join ", " (take 3 added)))])
                     (when (seq removed)
                       [(str "collections -" (count removed) ": "
                             (clojure.string/join ", " (take 3 removed)))]))]
    (vec (concat field-changes col-changes))))

;; ── diff record ───────────────────────────────────────────────────────────────

(defn make-diff
  "Construct a KagamiDiff map.

  status ∈ #{\"local-only\" \"remote-only\" \"changed\" \"ok\"}"
  [nanoid status local remote changes]
  {:nanoid  nanoid
   :status  status
   :local   (or local {})
   :remote  (or remote {})
   :changes (vec changes)})

(defn diff->map
  "Serialisable representation of a diff (omits full local/remote bodies)."
  [{:keys [nanoid status changes]}]
  {:nanoid  nanoid
   :status  status
   :changes changes})

;; ── diff-actors ───────────────────────────────────────────────────────────────

(defn diff-actors
  "Compare local-map {nanoid → actor-map} with remote-map {nanoid → actor-map}.
   Returns a vector of KagamiDiff maps.
   Pure function — no IO.

   Python equivalent: the diff logic inside kagami_diff command."
  [local-map remote-map]
  (let [local-only
        (for [[nanoid ldata] local-map
              :when (not (contains? remote-map nanoid))]
          (make-diff nanoid "local-only" ldata nil []))

        compared
        (for [[nanoid ldata] local-map
              :when (contains? remote-map nanoid)
              :let  [rdata   (get remote-map nanoid)
                     changes (compare-actors ldata rdata)
                     status  (if (seq changes) "changed" "ok")]]
          (make-diff nanoid status ldata rdata changes))

        remote-only
        (for [[nanoid rdata] remote-map
              :when (not (contains? local-map nanoid))]
          (make-diff nanoid "remote-only" nil rdata []))]

    (vec (concat local-only compared remote-only))))

;; ── summary ───────────────────────────────────────────────────────────────────

(defn diff-summary
  "Aggregate counts from a seq of KagamiDiff maps.
   Returns {:total :ok :changed :local-only :remote-only :drifted}.
   Pure function."
  [diffs]
  (let [by-status (group-by :status diffs)
        n         (fn [k] (count (get by-status k [])))]
    {:total       (count diffs)
     :ok          (n "ok")
     :changed     (n "changed")
     :local-only  (n "local-only")
     :remote-only (n "remote-only")
     :drifted     (+ (n "changed") (n "local-only") (n "remote-only"))}))
