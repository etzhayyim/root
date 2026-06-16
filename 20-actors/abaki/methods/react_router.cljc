(ns abaki.methods.react-router
  "react_router.py — 暴 (abaki) React & Route-Around execution.
  1:1 Clojure port of `methods/react_router.py` (ADR-2606073100).

  Consumes a routing policy (the Route-Around payload abaki/analyze emits) and simulates the
  downstream structural reactions — NO active attack, only route-AROUND (the constitutional
  NO_ATTACK_JUST_BYPASS invariant): a Murakumo compute-router that redirects a blocked vendor's
  workload to a safe compute provider (or fails securely when none exists), and an Ossekai
  survival-tree that activates Charter-aligned fallbacks per blocked domain (biology→suki,
  logistics→wadachi, compute→ameno).

  House style: routing-policy maps stay STRING-keyed (\"blocked_entities\" / \"safe_entities\"
  / \"id\" / \"domain\"); pure decision fns are extracted so the routing logic is testable;
  host println / file I/O only behind #?(:clj ...). The Python `__main__` demo printer is
  mirrored in -main at the #?(:clj) edge."
  (:require [clojure.string :as str]
            #?(:clj [abaki.methods.analyze :as a])
            #?(:clj [clojure.java.io :as io])))

(def requested-vendor "entity:compute:megacorp_a")

(defn compute-routing-decision
  "Pure core of simulate_murakumo_compute_routing. Given a routing policy, decide what the
  Murakumo compute-router does for `requested-vendor`. Returns a string-keyed map:
    {\"blocked\" bool \"fallback\" <safe-compute-id-or-nil>}.
  `blocked` = the requested vendor's id is in blocked_entities; `fallback` = the first safe
  entity whose domain is \"compute\" (nil when none) — mirrors `safe[0]` / no-safe-provider."
  [routing-policy]
  (let [blocked (mapv #(get % "id") (get routing-policy "blocked_entities"))
        safe    (->> (get routing-policy "safe_entities")
                     (filter #(= (get % "domain") "compute"))
                     (mapv #(get % "id")))]
    {"blocked" (boolean (some #{requested-vendor} blocked))
     "fallback" (first safe)}))

(defn survival-branches
  "Pure core of simulate_ossekai_survival_tree. The set of distinct blocked domains
  (mirrors Python set([e['domain'] for e in routing_policy['blocked_entities']]))."
  [routing-policy]
  (set (map #(get % "domain") (get routing-policy "blocked_entities"))))

#?(:clj
   (defn simulate-murakumo-compute-routing
     "Intercept a compute request and route around a blocked vendor (println-faithful)."
     [routing-policy]
     (println "\n[Murakumo Compute Router] Intercepting request...")
     (let [{:strs [blocked fallback]} (compute-routing-decision routing-policy)]
       (if blocked
         (do
           (println (str "🚨 ALERT: Request to '" requested-vendor "' is BLOCKED by abaki policy."))
           (println "   Reason: High Chokepoint Index (Monopolistic behavior).")
           (if fallback
             (println (str "🔄 ROUTE AROUND: Redirecting workload to safe provider: " fallback))
             (println "❌ FATAL: No safe compute providers available. Failing securely.")))
         (println "✅ Request permitted.")))))

#?(:clj
   (defn simulate-ossekai-survival-tree
     "Generate the Ossekai survival tree: per blocked domain, activate a Charter-aligned
     fallback (println-faithful)."
     [routing-policy]
     (println "\n[Ossekai Survival Simulator] Generating survival tree...")
     (let [blocked-domains (survival-branches routing-policy)]
       (println "Survival Branches Activated:")
       (when (contains? blocked-domains "biology")
         (println "🌱 Biology/Agri branch: Dependency on F1 seeds blocked. Activating 'suki' (Local Heirloom Seed Bank) fallback."))
       (when (contains? blocked-domains "logistics")
         (println "🚚 Logistics branch: Centralized logistics blocked. Activating 'wadachi' (Autonomous mesh delivery) fallback."))
       (when (contains? blocked-domains "compute")
         (println "💻 Compute branch: Proprietary API blocked. Activating 'ameno' (WebGPU local inference) fallback."))
       (println "Ossekai simulation updated to reflect the new Charter-aligned constraints."))))

#?(:clj
   (defn -main
     "CLI entry: read out/routing-policy.json → simulate both reactions. File I/O at this edge."
     [& _argv]
     (let [base-dir    (-> *file* io/file .getParentFile .getParentFile)
           policy-file (io/file base-dir "out" "routing-policy.json")]
       (if-not (.exists policy-file)
         (println (str "Error: Policy file not found at " policy-file))
         (let [policy (a/read-json (slurp policy-file))]
           (println "=== etzhayyim React & Route-Around Execution ===")
           (simulate-murakumo-compute-routing policy)
           (simulate-ossekai-survival-tree policy)
           (println "\n================================================"))))))
