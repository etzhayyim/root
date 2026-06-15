;; analyze.clj — 扶持 (fuchi) end-to-end allocation membrane over the :representative seed.
;;
;; Clojure port of analyze.py `run` (ADR-2606052300 R0 + R1 a/b/c/d), Wave 1 of the clj-native
;; migration (ADR-2606142300) — the FINAL fuchi method, completing the actor + Wave 1. Runs each
;; seed maintainer through the full pipeline over the now-clj methods:
;;
;;   covenant check → sustenance envelope → tenure-weighted allocation (cash≡0)
;;     → in-kind rail decomposition → governance gate
;;     → [auto | sbt-vote (real 1 SBT=1 vote + 48h timelock) | council-lv7 | refused]
;;     → provisioning intents to real producing actors (dry-run, published=false)
;;     → toritate ledgerEntry booking (cash≡0) + kanae-renderable flow graph
;;     → Displacement-Dividend cohort coupling (G2: no displacement without a funded cohort)
;;
;; NO live disbursement / provisioning / land grant / binding vote — all dry-run (G10). NOTE: only
;; the pipeline `run` is ported; analyze.py's `_report`/`main` are skipped (they read live-gate
;; condition keys the R2 autonomous gate no longer emits — i.e. that Markdown renderer is dead code
;; against the current live_gate). A clean `scorecard` summary is provided instead. stdlib only.
(ns fuchi.methods.analyze
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [fuchi.methods.allocate :as al]
            [fuchi.methods.route :as rt]
            [fuchi.methods.vote :as vote]
            [fuchi.methods.book :as book]
            [fuchi.methods.provision :as prov]
            [fuchi.methods.couple :as couple]
            [fuchi.methods.live-gate :as lg])
  (:import [java.math BigDecimal RoundingMode]))

(def default-seed "20-actors/fuchi/data/seed-sustenance-graph.kotoba.edn")

(defn- kw [v] (-> (str (or v "")) (str/replace #"^:+" "") (str/split #"/") last str/lower-case))
(defn- round-int [x] (.longValue (.setScale (BigDecimal/valueOf (double x)) 0 RoundingMode/HALF_EVEN)))

(defn- envelopes-for [seed did]
  (filterv #(= (:envelope/maintainer %) did) (:envelope/batch seed)))

(defn- ballots-for [seed did]
  (or (first (filter #(= (:gov/maintainer %) did) (:gov/ballots seed))) {}))

(defn run
  "Run the full allocation pipeline over the seed. Returns
   {:rows :derived :intents :ledger :flows :coupling :live-status}."
  ([] (run default-seed))
  ([seed-path]
   (let [seed       (edn/read-string (slurp (io/file seed-path)))
         records    (:maintainer/batch seed)
         ceiling    (long (:graph/stage-ceiling-usd-micros-yr seed 30000000000))
         now-h      (long (:graph/now-hours seed 0))
         cohort     (al/cohort-from-seed records)
         allocs     (into {} (map (juxt :maintainer-did identity) (al/allocate cohort ceiling 0 "sustenance")))
         note-of    (into {} (map (fn [r] [(:maintainer/did r) (get r :maintainer/note "")]) records))
         maintains-of (into {} (map (fn [r] [(:maintainer/did r)
                                             (str/join " " (map str (get r :maintainer/maintains [])))]) records))]
     (loop [rs records, as-of 3000
            acc {:rows [] :derived [] :intents [] :ledger [] :flows [] :in-kind-by-actor {}}]
       (if (empty? rs)
         (let [coupling (mapv (fn [ev]
                                (let [em (couple/earmark-from-surplus ev)
                                      committed (get (:in-kind-by-actor acc) (:displacing-actor ev) 0)]
                                  {:earmark em :gate (couple/coupling-gate ev em committed)}))
                              (couple/events-from-seed (:cohort/displacement seed)))
               live-status (mapv #(lg/gate-status (lg/make-gate {:leg %})) (keys lg/leg-policy))]
           (-> acc (dissoc :in-kind-by-actor) (assoc :coupling coupling :live-status live-status)))
         (let [r       (first rs)
               as-of   (+ as-of 10)
               did     (:maintainer/did r)
               cov     (kw (get r :maintainer/covenant ":vowed"))
               env     (envelopes-for seed did)]
           (if-let [rails (try (rt/route-envelope env) (catch Exception e {::refused (.getMessage e)}))]
             (if (::refused rails)
               (recur (rest rs) as-of
                      (update acc :rows conj {:did did :covenant cov :route ":refused-at-intake"
                                              :imputed "-" :in-kind "-" :outcome "refused" :note (::refused rails)}))
               (let [imputed-total (reduce + 0 (map :imputed-usd-micros-yr rails))
                     coverage (rt/in-kind-coverage rails)
                     ctx      (str (note-of did) " " (maintains-of did))
                     rider    (rt/rider-hit ctx)
                     inv      (rt/touches-invariant ctx)
                     route0   (rt/gov-route imputed-total inv rider)
                     [outcome route]
                     (case route0
                       "auto"        ["accepted" route0]
                       "council-lv7" ["pending" route0]
                       "refused"     ["refused" route0]
                       "sbt-vote"    (let [v (ballots-for seed did)
                                           ballots (vote/ballots-from-seed (get v :gov/votes []))
                                           t (vote/tally ballots (long (get v :gov/opened-at-hours 0)) now-h
                                                         (long (get v :gov/timelock-h 48)) vote/default-quorum)]
                                       [(:outcome t)
                                        (str "sbt-vote " (:yes t) "-" (:no t) "/" (:timelock-h t) "h"
                                             (if (:finalizable t) "✓" "…"))])
                       ["pending" route0])
                     a (allocs did)
                     row {:did did :covenant cov :route (str ":" route) :imputed imputed-total
                          :in-kind coverage :share (:share a 0.0) :rank (:priority-rank a "-")
                          :floor (:floor-usd-micros-yr a 0) :outcome outcome :note (note-of did)}]
                 (if (and a (#{"accepted" "pending"} outcome))
                   (let [in-kind-imputed (round-int (* imputed-total coverage))
                         acts (remove str/blank? (str/split (maintains-of did) #"\s+"))
                         these-intents (prov/provision rails (:maintainer-did a) #{})
                         these-ledger  (book/book-toritate rails (:maintainer-did a) (:maintainer-did a))
                         these-flows   (book/flow-graph rails (:maintainer-did a) (:maintainer-did a))]
                     (recur (rest rs) as-of
                            (-> acc
                                (update :rows conj row)
                                (update :in-kind-by-actor #(reduce (fn [m act] (update m (symbol act) (fnil + 0) in-kind-imputed)) % acts))
                                (update :intents into these-intents)
                                (update :ledger into these-ledger)
                                (update :flows into these-flows)
                                (update :derived conj
                                        {:alloc/maintainer did :alloc/instrument (str ":" (:instrument a))
                                         :alloc/share (:share a) :alloc/priority-rank (:priority-rank a)
                                         :alloc/floor-usd-micros-yr (:floor-usd-micros-yr a)
                                         :alloc/cash-usd-micros 0 :alloc/server-held-key false
                                         :gov/route (str ":" (first (str/split route #"\s+")))
                                         :gov/outcome (str ":" outcome) :rail/coverage-in-kind coverage
                                         :prov/intents (count these-intents) :book/entries (count these-ledger)
                                         :wb/as-of as-of}))))
                   (recur (rest rs) as-of (update acc :rows conj row)))))
             (recur (rest rs) as-of acc))))))))

(defn scorecard
  "A clean dry-run summary (replaces analyze.py's R2-broken Markdown _report)."
  [res]
  (str/join "\n"
    (concat
     ["# 扶持 (fuchi) — maintainer-sustenance allocation dry-run (R0 + R1 a/b/c/d)"
      ""
      (str "- maintainers: " (count (:rows res))
           " · accepted: " (count (filter #(= "accepted" (:outcome %)) (:rows res)))
           " · pending: " (count (filter #(= "pending" (:outcome %)) (:rows res)))
           " · refused: " (count (filter #(= "refused" (:outcome %)) (:rows res))))
      (str "- provisioning intents: " (count (:intents res))
           " · ledger entries: " (count (:ledger res))
           " · flow edges: " (count (:flows res)))
      (str "- coupling: " (count (filter #(get-in % [:gate :admissible]) (:coupling res)))
           "/" (count (:coupling res)) " cohorts admissible")
      "" "| maintainer | covenant | route | outcome |" "|---|---|---|---|"]
     (map (fn [r] (str "| " (last (str/split (str (:did r)) #":")) " | " (:covenant r)
                       " | " (:route r) " | " (:outcome r) " |")) (:rows res)))))
