(ns monosashi.methods.autorun
  "monosashi 物差し — deterministic autonomous heartbeat. ADR-2606271800.

  One cycle: read mitooshi score residuals (+ optional same-series tsuchifumi sysdyn context) →
  skill-band per (actor, baseline) → draft skill posts → emit (G1/G3/G7) → persist ONE
  content-addressed tx to the kotoba Datom log, BUT only when the content changed
  (idempotent-by-content; a re-run with identical inputs is a no-op, so the log is not padded with
  duplicate transactions). Deterministic / resume-safe: the caller supplies :tx-id + :as-of (no wall
  clock, no Math/random), and the tx CID chains onto the log's previous CID (commit-DAG).

  The EXTERNAL AT-Proto relay leg is operator-gated (a `transport` fn carrying a member/operator
  credential — see methods/transport.cljc); with no transport, posts persist on-protocol (kotoba
  log) and the relay is :pending-operator-transport. :published requires a member-DID :author (G7)."
  (:require [clojure.string :as str]
            #?(:clj [clojure.edn :as edn])
            #?(:clj [clojure.java.io :as io])
            [monosashi.methods.score :as score]
            [monosashi.methods.social :as social]
            [monosashi.methods.kotoba :as kotoba]))

#?(:clj
   (defn load-residuals
     "Read a seed EDN of {:residuals [...] :sysdyn {actor {:series :band-width}}}."
     [path]
     (with-open [r (io/reader path)] (edn/read-string (slurp r)))))

(defn run-cycle
  "Run one heartbeat cycle. opts:
     :as-of (required, G5)  :tx-id (required, deterministic)  :author (member-DID, G7)
     :status (:dry-run|:published)  :transport (operator relay fn, optional)  :log (path)
  Returns {:bands :posts :receipts :tx :appended?}. Idempotent-by-content: if the new band-datoms
  equal the last tx's band-datoms, no tx is appended (:appended? false). Pure except the one append."
  [{:keys [residuals sysdyn]}
   {:keys [as-of tx-id author status transport log]
    :or {author "" status ":dry-run" log #?(:clj kotoba/log-default :cljs nil)}}]
  (let [bands (score/evaluate residuals {:as-of as-of :sysdyn sysdyn})
        posts (mapv #(social/draft-skill-post % {:author author :status status}) bands)
        receipts (mapv #(social/emit % transport) posts)
        datoms (vec (concat (mapcat kotoba/band-datoms bands) (kotoba/post-datoms posts)))
        prev (kotoba/last-cid log)
        unchanged? (= datoms (some-> (kotoba/last-tx log) (get ":tx/datoms")))
        tx (kotoba/make-tx datoms {:tx-id tx-id :as-of as-of :prev-cid prev})]
    (when-not unchanged? (kotoba/append-tx! log tx))
    {:bands bands :posts posts :receipts receipts :tx tx :appended? (not unchanged?)}))
