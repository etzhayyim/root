#!/usr/bin/env bb
;; etzhayyim.lint.no-new-ts — enforce-forward the TS→cljs+edn migration (ADR-2606251200 §Decision 6).
(ns etzhayyim.lint.no-new-ts
  "Enforce-forward gate for the 60-apps TS→ClojureScript+EDN migration
  (ADR-2606251200). Mirrors `lint:no-new-shell` (ADR-2606072802): once an app is
  migrated/piloted to cljs-first, it admits NO NEW first-party `.ts` — existing TS
  is GRANDFATHERED in a baseline that only SHRINKS (port a `.ts` to cljs + delete it
  → `--update` drops it). Adding a `.ts` not in the baseline fails CI.

  Enforcement is PER-MIGRATED-APP (`enforced-roots`), not global — un-migrated apps
  are untouched until their wave. The pilot leads: `etzhayyim-project-explorer` is
  already cljs-first (0 first-party .ts / 33 .cljs), so its baseline is empty and the
  gate keeps it TS-free. As apps migrate, add their root here and `--update`.

    bb lint:no-new-ts            ; check (exit 1 on a new .ts in an enforced app)
    bb lint:no-new-ts --update   ; rewrite the baseline (operator, after a migration step)"
  (:require [babashka.fs :as fs]
            [clojure.string :as str]
            [clojure.edn :as edn]))

(def ^:private enforced-roots
  "App roots under TS-freeze. Grows as the migration advances."
  ["60-apps/etzhayyim-project-explorer"])

(def ^:private baseline-path "70-tools/src/etzhayyim/lint/ts-baseline.edn")
(def ^:private exclude-substrings
  ["/node_modules/" "/dist/" "/build/" "/.svelte-kit/" "/_app/" "/vendor/" "/.git/" ".d.ts"])

(defn- excluded? [p] (some #(str/includes? p %) exclude-substrings))

(defn present-ts
  "Sorted vector of first-party *.ts paths (repo-relative, /-separated) under `roots`."
  [roots]
  (->> (mapcat #(fs/glob % "**.ts") roots)
       (map (comp #(str/replace % "\\" "/") str))
       (remove excluded?)
       sort vec))

(defn new-ts
  "Files present now that are NOT in the grandfathered baseline (the violations)."
  [present baseline]
  (vec (sort (remove (set baseline) present))))

(defn removed-ts
  "Baseline entries no longer present (ported→deleted; the baseline should shrink)."
  [present baseline]
  (vec (sort (remove (set present) baseline))))

#?(:clj
   (defn -main [& args]
     (let [update? (boolean (some #{"--update"} args))
           present (present-ts enforced-roots)
           baseline (if (fs/exists? baseline-path)
                      (edn/read-string (slurp baseline-path)) [])]
       (cond
         update?
         (do (spit baseline-path
                   (str ";; etzhayyim.lint.no-new-ts — grandfathered first-party .ts baseline (per-migrated-app).\n"
                        ";; Shrinks-only: porting a .ts to cljs + deleting it drops it here. NEVER add by hand.\n"
                        ";; Regenerate: bb lint:no-new-ts --update\n"
                        (with-out-str (clojure.pprint/pprint present))))
             (println (str "baseline updated: " (count present) " grandfathered .ts across "
                           (count enforced-roots) " enforced app(s)")))

         :else
         (let [violations (new-ts present baseline)
               removed (removed-ts present baseline)]
           (when (seq removed)
             (println (str "note: " (count removed) " baselined .ts no longer present"
                           " (run --update to shrink the baseline): " (pr-str (take 5 removed))
                           (when (> (count removed) 5) " …"))))
           (if (seq violations)
             (do (println (str "FAIL: " (count violations) " NEW first-party .ts in a migrated app"
                               " — author these in ClojureScript (squint), not TypeScript"
                               " (ADR-2606251200 §Decision 6):"))
                 (doseq [v violations] (println (str "  + " v)))
                 (System/exit 1))
             (println (str "ok: no new first-party .ts in the " (count enforced-roots)
                           " enforced app(s) (" (count baseline) " grandfathered)"))))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
