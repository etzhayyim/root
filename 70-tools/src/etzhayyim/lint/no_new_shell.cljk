#!/usr/bin/env bb
;; etzhayyim.lint.no-new-shell — enforce the repo clj/bb rule going forward.
(ns etzhayyim.lint.no-new-shell
  "Enforce-forward gate for the repo-wide rule (root CLAUDE.md §\"Operational code = clj/bb\"):
  first-party operational/tooling scripts SHOULD be clj/bb, NOT shell. Existing `.sh` are
  GRANDFATHERED (the rule bars *newly authored* ones), so this gate does NOT mass-port them —
  it BASELINES the set that existed at adoption and FAILS only when a NEW first-party `.sh`
  appears under 20-actors. New actors must ship `run_tests.clj`, not `run_tests.sh`
  (vitals already prefers the .clj runner; ADR-2606072802 enforce-forward).

  The baseline shrinks-only: porting a grandfathered `.sh` to bb + deleting it is always
  allowed (run `--update` to drop it from the baseline). Adding a `.sh` not in the baseline
  fails CI.

    bb lint:no-new-shell            ; check (exit 1 on a new .sh)
    bb lint:no-new-shell --update   ; rewrite the baseline (operator, after an intentional change)"
  (:require [babashka.fs :as fs]
            [clojure.string :as str]
            [clojure.edn :as edn]))

(def ^:private scan-root "20-actors")
(def ^:private baseline-path "70-tools/src/etzhayyim/lint/shell-baseline.edn")
(def ^:private exclude-substrings ["/node_modules/" "/vendor/" "/lib/" "/.claude/" "/.git/"])

(defn- excluded? [p] (some #(str/includes? p %) exclude-substrings))

(defn present-scripts
  "Sorted vector of first-party *.sh paths (repo-relative, /-separated) under scan-root."
  [root]
  (->> (fs/glob root "**.sh")
       (map (comp #(str/replace % "\\" "/") str))
       (remove excluded?)
       sort vec))

(defn new-scripts
  "Scripts present now that are NOT in the grandfathered baseline (the violations)."
  [present baseline]
  (vec (sort (remove (set baseline) present))))

(defn removed-scripts
  "Baseline entries no longer present (ported→deleted; the baseline should shrink to drop them)."
  [present baseline]
  (vec (sort (remove (set present) baseline))))

#?(:clj
   (defn -main [& args]
     (let [update? (boolean (some #{"--update"} args))
           present (present-scripts scan-root)
           baseline (if (fs/exists? baseline-path)
                      (edn/read-string (slurp baseline-path)) [])]
       (cond
         update?
         (do (spit baseline-path
                   (str ";; etzhayyim.lint.no-new-shell — grandfathered first-party .sh baseline.\n"
                        ";; Shrinks-only: porting a .sh to bb + deleting it drops it here. NEVER add by hand.\n"
                        ";; Regenerate: bb lint:no-new-shell --update\n"
                        (with-out-str (clojure.pprint/pprint present))))
             (println (str "baseline updated: " (count present) " grandfathered .sh under " scan-root)))

         :else
         (let [violations (new-scripts present baseline)
               removed (removed-scripts present baseline)]
           (when (seq removed)
             (println (str "note: " (count removed) " baselined .sh no longer present"
                           " (run --update to shrink the baseline): " (pr-str (take 5 removed))
                           (when (> (count removed) 5) " …"))))
           (if (seq violations)
             (do (println (str "FAIL: " (count violations) " NEW first-party .sh under " scan-root
                               " — author these in clj/bb (run_tests.clj, methods/*.cljc), not shell"
                               " (root CLAUDE.md §\"Operational code = clj/bb\"):"))
                 (doseq [v violations] (println (str "  + " v)))
                 (System/exit 1))
             (println (str "ok: no new first-party .sh under " scan-root
                           " (" (count baseline) " grandfathered)"))))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
