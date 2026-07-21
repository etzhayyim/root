#!/usr/bin/env bb
;; fleet_audit.clj — etzhayyim datomic-ledger FLEET health audit.
;;
;; Run from the west superproject root:
;;   bb 70-tools/scripts/datomic-health/fleet_audit.clj
;;   bb 70-tools/scripts/datomic-health/fleet_audit.clj --actors tate,inochi   ;; subset
;;   bb 70-tools/scripts/datomic-health/fleet_audit.clj --quiet                ;; table only
;;
;; WHAT IT PROVES (per actor, over the REAL committed seed, in a throwaway temp ledger):
;;   1. heartbeat appends GROUND datoms to a content-addressed append-only commit-DAG
;;      (methods/autorun beat → methods/kotoba append-tx);
;;   2. the chain VERIFIES (tamper-evident verify-chain :ok, prev-cid linkage intact);
;;   3. the beat is IDEMPOTENT-BY-CONTENT — a second beat over the same seed is a NO-OP
;;      (the ledger records CHANGES, never a wall-clock liveness tick → a 30-min loop over a
;;      static seed never bloats the chain);
;;   4. GROUND-ONLY — no transient/derived datom (:bond/* / :ops/* / :enkiri/*) is persisted
;;      (read-time aggregates are never stored as ground state, N1/G2).
;;
;; This is the FLEET-level assertion that the org's actors are "datomic で設計実装されている":
;; not just emitting EAVT, but persisting it to tamper-evident, resume-safe, content-addressed
;; commit-DAGs with deterministic heartbeats. Pure audit — writes only to java.io.tmpdir,
;; touches no actor data, no network (no-server-key). Exit 0 iff every audited actor is healthy.
(ns datomic-health.fleet-audit
  (:require [clojure.string :as str]
            [clojure.java.io :as io]))

(def repo-root
  ;; this file = 70-tools/scripts/datomic-health/fleet_audit.clj → up 4 = repo root
  (-> *file* io/file .getCanonicalFile .getParentFile .getParentFile .getParentFile .getParentFile))

(def actors-dir (io/file repo-root "orgs" "etzhayyim"))

(defn ledger-actors
  "Every com-etzhayyim-* checkout that carries BOTH methods/kotoba.cljc and
  methods/autorun.cljc — the datomic-ledger family. Sorted, deterministic."
  []
  (->> (.listFiles actors-dir)
       (filter #(.isDirectory %))
       (filter (fn [d] (and (.exists (io/file d "methods" "kotoba.cljc"))
                            (.exists (io/file d "methods" "autorun.cljc")))))
       (map #(subs (.getName %) (count "com-etzhayyim-")))
       sort
       vec))

(def derived-prefixes
  "Attribute namespaces that are DERIVED (read-time aggregates) and must NOT appear as ground."
  [":bond/" ":ops/" ":enkiri/"])

(defn- derived-attr? [a]
  (let [s (str a)] (some #(str/starts-with? s %) derived-prefixes)))

(defn audit-actor
  "Audit one actor's ledger end-to-end in a throwaway temp log. Never throws.

  Classifies into :status
    :healthy      — standard-interface family, all invariants hold;
    :fail         — standard-interface family, but an invariant is VIOLATED (the only exit-1 case);
    :non-standard — a ledger actor that does not expose the standard family interface
                    (autorun/beat {:tx-id :as-of :log-path} + autorun/ground-datoms +
                    kotoba/verify-chain). NOT a failure — sibling/earlier-wave actors use
                    other conventions (shared kotoba.datom lib, different beat arity, …).
                    These rows are the datomic-ledger STANDARDIZATION worklist."
  [a]
  (let [tmp (str (System/getProperty "java.io.tmpdir") "/datomic-audit-" a "-" (gensym) ".edn")
        ;; Step 1: classify by what loads.
        ;;   :load-error  — the autorun/kotoba namespace FAILS to require (stale .clj shadow,
        ;;                  missing fn, broken twin). EVERY ledger actor must at least LOAD →
        ;;                  this is a FAILURE (exit 1), fleet-wide. (Catches the bug class
        ;;                  fixed in #2021/#2024 — stale .clj shadows, unported fns — for good.)
        ;;   {:beat …}    — exposes the standard beat/ground-datoms/verify-chain interface.
        ;;   :non-standard— loads cleanly but uses a different ledger convention (shared
        ;;                  kotoba.datom lib / run-cycle arity). NOT a failure — informational.
        iface (try
                (require (symbol (str a ".methods.autorun")))
                (require (symbol (str a ".methods.kotoba")))
                (let [beat   (resolve (symbol (str a ".methods.autorun") "beat"))
                      ground (resolve (symbol (str a ".methods.autorun") "ground-datoms"))
                      verify (resolve (symbol (str a ".methods.kotoba") "verify-chain"))]
                  (if (and beat ground verify)
                    {:beat beat :ground ground :verify verify}
                    {:non-standard "no standard beat/ground-datoms/verify-chain interface"}))
                (catch Throwable e
                  {:load-error (str (or (ex-message e) (class e)))}))]
    (cond
      (:load-error iface)
      {:actor a :status :load-error :note (:load-error iface)}

      (:non-standard iface)
      {:actor a :status :non-standard :note (:non-standard iface)}

      :else
      ;; Step 2: standard family — now any failure of the invariants (or a throw) IS a :fail.
      (try
        (let [{:keys [beat ground verify]} iface
              r1      (beat {:tx-id "audit-1" :as-of "audit-a1" :log-path tmp})
              r2      (beat {:tx-id "audit-2" :as-of "audit-a2" :log-path tmp})
              chain   (verify tmp)
              ds      (ground)
              gonly   (not-any? (fn [d] (derived-attr? (nth d 2 nil))) ds)
              add-ops (every? (fn [d] (= ":db/add" (first d))) ds)
              idem    (and (:appended r1) (not (:appended r2)) (= :no-change (:reason r2)))
              ok      (and (pos? (long (:count r1 0))) (:ok chain)
                           (= 1 (:length chain)) idem gonly add-ops)]
          {:actor a :status (if ok :healthy :fail) :datoms (:count r1) :chain-ok (:ok chain)
           :chain-len (:length chain) :idempotent idem :ground-only gonly :add-ops add-ops})
        (catch Throwable e
          {:actor a :status :fail :error (or (ex-message e) (str (class e)))})
        (finally (io/delete-file (io/file tmp) true))))))

(defn- parse-args [args]
  (let [m (apply hash-map (->> args (partition-all 2) (mapcat (fn [[k v]] [k (or v true)]))))]
    {:actors (when-let [s (get m "--actors")] (when (string? s) (str/split s #",")))
     :quiet  (contains? m "--quiet")}))

(defn -main [& args]
  (let [{:keys [actors quiet]} (parse-args args)
        targets  (or actors (ledger-actors))
        results  (mapv audit-actor targets)
        healthy  (filterv #(= :healthy (:status %)) results)
        failed   (filterv #(= :fail (:status %)) results)
        loaderr  (filterv #(= :load-error (:status %)) results)
        nonstd   (filterv #(= :non-standard (:status %)) results)
        ;; a ledger actor that does not even LOAD is a failure, fleet-wide (catches stale .clj
        ;; shadows / unported fns continuously); a standard-family invariant breach is also a fail.
        broken   (vec (concat failed loaderr))
        total-datoms (reduce + 0 (keep #(when (= :healthy (:status %)) (long (:datoms % 0))) results))]
    (when-not quiet
      (println (str "etzhayyim datomic-ledger FLEET AUDIT — " (count targets) " ledger actors"))
      (println "(heartbeat → content-addressed commit-DAG; verify-chain + idempotency + ground-only)\n")
      (println "── standard-interface family (audited) ──")
      (println (format "%-16s %8s %7s %6s %6s %8s" "actor" "datoms" "chain" "idem" "ground" "status"))
      (println (apply str (repeat 56 "-")))
      (doseq [r (sort-by :actor (concat healthy failed))]
        (if (:error r)
          (println (format "%-16s  FAIL: %s" (:actor r) (:error r)))
          (println (format "%-16s %8d %7s %6s %6s %8s"
                           (:actor r) (long (:datoms r 0))
                           (str (:chain-ok r)) (str (:idempotent r))
                           (str (:ground-only r)) (name (:status r))))))
      (when (seq loaderr)
        (println (str "\n── LOAD ERRORS (" (count loaderr) ") — a ledger actor that does not load is a FAILURE ──"))
        (doseq [r (sort-by :actor loaderr)]
          (println (format "  %-16s %s" (:actor r) (:note r)))))
      (when (seq nonstd)
        (println (str "\n── non-standard ledger actors (" (count nonstd)
                      ") — load cleanly, different ledger interface (STANDARDIZATION worklist, not failures) ──"))
        (doseq [r (sort-by :actor nonstd)]
          (println (format "  %-16s %s" (:actor r) (:note r))))))
    (println)
    (println (format "FLEET: %d standard-family healthy / %d audited · %d non-standard · %d load-error · %d datoms (single-beat ground)%s"
                     (count healthy) (+ (count healthy) (count failed)) (count nonstd) (count loaderr) total-datoms
                     (if (seq broken) (str " · BROKEN: " (str/join ", " (map :actor broken))) "")))
    ;; exit 1 when a standard-family actor breaks an invariant OR any ledger actor fails to load.
    (System/exit (if (seq broken) 1 0))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply -main *command-line-args*))
