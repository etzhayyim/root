(ns etzhayyim.tools.discovery
  "Auto-discovery of ported actor test namespaces for the bb `test:actors` task.

  Replaces the previously hand-maintained `test:stubs` + `test:pywasm` ns lists
  (per ADR-2606131500-bb-test-discovery): every tier of the Python→Clojure
  refactor used to append its test nses to one shared list in bb.edn, so every
  feature branch edited the same region and merge-conflicted. Discovery makes
  bb.edn static — drop a `test_*.cljc` under 20-actors and it is picked up, with
  zero bb.edn churn.

  Scope = all `test_*.clj(c)` under 20-actors + 70-tools, MINUS:
    - mimamori. / yobel. / ibuki.   — owned by their dedicated bb tasks
    - etzhayyim.tools.*             — owned by test:tools (incl. this ns's siblings)
    - any path under a hyphen-dir   — SCI ns→path munge cannot load them
                                       (ns symbol normalises hyphens, file path
                                        keeps underscores; the dir hyphen breaks
                                        the round-trip — e.g. kuni-umi)."
  (:require [babashka.fs :as fs]
            [clojure.string :as str]))

;; longest-prefix-first so 70-tools/src strips before 70-tools, etc.
(def ^:private classpath-roots
  ["20-actors/kotodama/src"
   "50-infra/etzhayyim-moyai-credit/src"
   "70-tools/src"
   "20-actors"
   "70-tools"])

(defn- strip-root
  "Strip the longest matching classpath root prefix from a repo-relative path,
  yielding the classpath-relative path (the basis for the ns symbol)."
  [path]
  (or (some (fn [r] (when (str/starts-with? path (str r "/"))
                      (subs path (inc (count r)))))
            classpath-roots)
      path))

(defn- rel->ns
  "Classpath-relative path → namespace symbol (dir → `.`, `_` → `-`)."
  [rel]
  (-> rel
      (str/replace #"\.cljc?$" "")
      (str/replace "/" ".")
      (str/replace "_" "-")
      symbol))

(defn- hyphen-dir?
  "True if any directory segment of the CLASSPATH-RELATIVE path contains a hyphen
  (SCI cannot load such an ns — the dir-hyphen breaks the ns↔path munge
  round-trip). Checked on the rel path so the hyphenated classpath ROOTS
  (`20-actors`, `70-tools`) do not themselves trip it."
  [rel]
  (some #(str/includes? % "-") (butlast (str/split rel #"/"))))

(defn- excluded? [ns-sym]
  (let [n (str ns-sym)]
    (or (re-find #"^(mimamori|yobel|ibuki)\." n)
        (str/starts-with? n "etzhayyim.tools."))))

(defn declared-ns
  "The ns symbol a file actually declares (first top-level form), or nil if it is unreadable or
  does not start with an `(ns …)` form. Reads with `:read-cond :allow` so `.cljc` files parse."
  [path]
  (try
    (let [form (read-string {:read-cond :allow} (slurp (str path)))]
      (when (and (seq? form) (= 'ns (first form))) (second form)))
    (catch Exception _ nil)))

(defn actor-test-nss
  "Sorted, de-duplicated vector of discovered actor test namespaces.

  Only includes a file whose DECLARED ns equals the path-derived ns. This skips
  `run_tests_clj.sh`-style suites that declare a non-path ns (e.g. `root.danjo.methods.*`)
  and load their deps via cwd-relative `(load-file …)` — those are owned by their own runner
  and would crash a classpath `require` from the repo root."
  []
  (->> (concat (fs/glob "20-actors" "**/test_*.clj")
               (fs/glob "20-actors" "**/test_*.cljc")
               (fs/glob "70-tools"  "**/test_*.clj")
               (fs/glob "70-tools"  "**/test_*.cljc"))
       (map (fn [p] (let [path (str/replace (str p) #"^\./" "")]
                      {:path path :ns (rel->ns (strip-root path))})))
       (remove #(hyphen-dir? (strip-root (:path %))))
       (remove #(excluded? (:ns %)))
       (filter #(= (:ns %) (declared-ns (:path %))))   ; only path-matching declared ns (classpath-safe)
       (map :ns)
       distinct
       sort
       vec))
