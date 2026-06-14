;; test_freshness.clj — the committed GENERATED artifacts must match what the code produces.
;; Guards against scorecard/profile drift (the tate deploy-sync pattern): if a generator changes
;; output, the committed file must be regenerated or this fails. Run: bb test_freshness.clj.
(ns root.danjo.methods.test-freshness
  (:require [clojure.java.io :as io]))

(load-file "maturity.clj")        ; → coverage / org_actor / taxes / transfers / ingest / cofog_xcheck
(alias 'cov 'root.danjo.methods.coverage)
(alias 'm   'root.danjo.methods.maturity)
(alias 'o   'root.danjo.methods.org-actor)
(alias 't   'root.danjo.methods.taxes)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))
(defn committed [path] (slurp (io/file path)))

;; ── coverage scorecard ──
(check "REVENUE-COVERAGE.md is up to date (run coverage.clj -main to refresh)"
       (= (committed "../data/REVENUE-COVERAGE.md") (cov/full-md)))

;; ── maturity scorecard ──
(check "REVENUE-MATURITY.md is up to date (run maturity.clj -main to refresh)"
       (= (committed "../data/REVENUE-MATURITY.md") (m/scorecard (m/context))))

;; ── org mirror-actor profiles + index ──
(let [orgs  (o/load-orgs "../data/jp-fiscal-orgs.edn")
      taxes (t/combine (t/load-taxes "../data/jp-national-taxes.edn")
                       (t/load-local-taxes "../data/jp-local-taxes.edn"))]
  (doseq [org (:orgs orgs)]
    (check (str "profile up to date: " (:handle org))
           (= (committed (str "../data/actors/" (:handle org) ".profile.json"))
              (o/->json (o/org-profile org orgs taxes)))))
  (check "actors.json index up to date"
         (= (committed "../data/actors/actors.json")
            (o/->json {:actors (mapv (fn [x] {:handle (:handle x) :did (:did x)
                                              :displayName (:ja x) :type "gov-fiscal-mirror"
                                              :keyless true}) (:orgs orgs))
                       :note "keyless gov-fiscal mirror-actors (ADR-2606042330); observational only."}))))

(println (format "── freshness: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
