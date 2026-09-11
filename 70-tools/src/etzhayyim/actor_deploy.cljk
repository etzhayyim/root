(ns etzhayyim.actor-deploy
  "Unified `e7m actor` deploy dispatcher (ADR-2607022300).

  Each sub-command DELEGATES to an existing per-facet CLJC implementation —
  rename-only, no reimplementation, and NO python (the repo is porting py→cljc,
  per the root CLAUDE.md 'Operational code = clj/bb' rule). The 3 substrates
  each own ONE concern — storage(kotoba) / compute-resident(murakumo) /
  publish(aozora) — so the verbs are not peer 'run the actor here' targets:
  aozora is an identity-register + publish-sink, NOT a compute substrate.

  Usage:
    e7m actor mesh      <name> [--trigger ..]   → etzhayyim.actor-mesh     (package → kotoba.app.edn)
    e7m actor publish   <name> [--apply]        → etzhayyim.actor-publish  (kotoba-rad sovereign identity)
    e7m actor pin       <cid> [name]            → etzhayyim.kotobase-pin   (kotoba storage facet)
    e7m actor reside    --node <n> […]          → lite-runner (cljc cell-runner; murakumo compute facet)
    e7m actor identify  <name> [--apply]        → etzhayyim.aozora-deploy  (aozora publish facet)
    e7m actor deploy --all <name>               → mesh → identify (name-keyed facets)

  Layering (ADR-2607022300):
    author → kotoba(storage) → {murakumo | browser-WASM}(compute) → aozora(publish)
  See that ADR for the topology + per-facet maturity (pin/reside partly-built R0)."
  (:require [babashka.process :refer [shell]]
            [clojure.string :as str]))

(def ^:private facets
  {"mesh"     "`bb actor:mesh` — package → kotoba.app.edn"
   "publish"  "`bb actor:publish` — kotoba-rad sovereign identity"
   "pin"      "`bb kotobase:pin` — kotoba storage facet (args: <cid> [name])"
   "reside"   "lite-runner (cljc) — murakumo compute facet, kototama runtime (args: --node <n> --registry <p> --cells-root <p> [--once] [--healthz-port <n>])"
   "identify" "`bb aozora:deploy` — aozora publish facet (args: <name> [--apply])"})

(defn- delegate
  "Require the ns and call its -main with args (delegation, NOT reimplementation)."
  [ns-sym args]
  (require ns-sym)
  (apply (resolve (symbol (str ns-sym) "-main")) args))

(defn- reside
  "Run the cljc kototama runtime (lite-runner) — NO python (repo-wide py→cljc).
  One bb supervisor per node: reads cells.edn, cron-fires assigned cells,
  records each fire on a local kotoba ops commit-DAG. Args pass through."
  [args]
  (apply shell {:dir "50-infra/cluster/murakumo/cell-runner"}
         "bb" "-cp" "." "-m" "lite-runner" args))

(defn- deploy-all
  "Run the name-keyed facets: mesh (package) → identify (aozora profile). The
  pin/reside facets take substrate-specific args (<cid>, --node) not derivable
  from a bare <name> at R0, so they are advised rather than auto-run."
  [name]
  (println "▶ e7m actor deploy --all" name)
  (println "  [1/2] mesh (package → kotoba.app.edn)")
  (delegate 'etzhayyim.actor-mesh [name])
  (println "  [2/2] identify (aozora profile)")
  (delegate 'etzhayyim.aozora-deploy [name])
  (println "  — pin (kotoba) needs the packaged CID; reside (murakumo) needs --node —")
  (println "    e7m actor pin <cid>" (or name "<name>"))
  (println "    e7m actor reside --node <node> --registry <path> --cells-root <path>"))

(defn -main
  "argv = [<verb> ...facet-args]. Verb routes to the facet; bare invocation
  prints usage. Routed by etzhayyim.cli/dispatchable under `bb e7m actor …`."
  [& args]
  (let [[verb & rest] args]
    (case verb
      "mesh"     (delegate 'etzhayyim.actor-mesh rest)
      "publish"  (delegate 'etzhayyim.actor-publish rest)
      "pin"      (delegate 'etzhayyim.kotobase-pin rest)
      "reside"   (reside rest)
      "identify" (delegate 'etzhayyim.aozora-deploy rest)
      "deploy"   (if (= "--all" (first rest))
                   (deploy-all (second rest))
                   (do (println "usage: e7m actor deploy --all <name>")
                       (System/exit 1)))
      (do (println "e7m actor <verb> — unified deploy dispatcher (ADR-2607022300).")
          (println "3 substrates, 3 concerns — storage(kotoba) / compute(murakumo) / publish(aozora):")
          (doseq [[k v] (sort facets)] (println "  " k (str (apply str (repeat (max 1 (- 11 (count k))) " "))) v))
          (println "  deploy --all <name> — mesh → identify (name-keyed facets)")
          (System/exit 1)))))
