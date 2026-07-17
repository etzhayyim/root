#!/usr/bin/env nbb
;; --- nbb shims (auto, ADR-2607173000) ---------------------------------
(def ^:private __fs (js/require "node:fs"))
(def ^:private __path (js/require "node:path"))
(def ^:private __cp (js/require "node:child_process"))
(def ^:private __os (js/require "node:os"))
(def ^:private __crypto (js/require "node:crypto"))
(defn- __sh [& args]
  (let [opts (when (map? (last args)) (last args))
        cmd (if opts (butlast args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:encoding "utf8"} (when opts {:cwd (:dir opts)}))))]
    {:exit (or (.-status r) 1) :out (or (.-stdout r) "") :err (or (.-stderr r) "")}))
(defn- __shell [& args]
  (let [opts (when (map? (first args)) (first args))
        cmd (if opts (rest args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:stdio "inherit" :encoding "utf8"}
                                      (when opts {:cwd (:dir opts)}))))]
    (when-not (zero? (or (.-status r) 1))
      (throw (js/Error. (str "shell failed: " (pr-str cmd)))))
    {:exit (or (.-status r) 0) :out "" :err ""}))
;; -----------------------------------------------------------------------
;; no-ignorable-staged — pre-commit guard (Clojure / babashka; root CLAUDE.md §clj/bb).
;;
;; Blocks build artifacts, caches, machine-local state, and *secret-bearing* dirs
;; (e.g. a browser `.sodai-chrome-profile/` holding cookies/login-data) from being
;; committed when no .gitignore happens to cover them. Motivated by the
;; ai-gftd-chat-shell incident (2026-06-25): the app dir had no .gitignore, so a
;; whole Chrome profile + node_modules + build output were stage-able and showed up
;; in `git status` / nearly landed in history.
;;
;; It computes the staged set itself (NOT from lefthook's {staged_files} glob) so
;; extension-less junk like Chrome's `Cookies`, `Login Data`, and leveldb `MANIFEST-*`
;; are caught too. Only NEWLY added/copied/renamed paths are checked (diff-filter ACR)
;; — already-tracked files are someone else's problem to remediate, not a commit blocker.
;;
;; Escape hatch: add a regex to 70-tools/scripts/lint/ignorable-allowlist.edn (:allow)
;; for an intentional exception, or `git commit --no-verify` to bypass entirely.
(require ']
         '[clojure.string :as str]
         '[clojure.edn :as edn]
         ')

;; ── denylist: [pattern label]; pattern is a regex over the repo-relative path ──
;; A path segment is delimited by '/' or string ends; patterns anchor on segments
;; so a *source* file literally named e.g. `build.rs` is NOT matched (only `build/…`).
(def deny
  [[#"(^|/)node_modules/"                 "node_modules (JS deps — reinstall, never commit)"]
   [#"(^|/)\.svelte-kit/"                 ".svelte-kit (SvelteKit build output)"]
   [#"(^|/)\.wrangler/"                   ".wrangler (Cloudflare build/cache)"]
   [#"(^|/)\.next/"                       ".next (Next.js build output)"]
   [#"(^|/)\.nuxt/"                       ".nuxt (Nuxt build output)"]
   [#"(^|/)\.turbo/"                      ".turbo (Turborepo cache)"]
   [#"(^|/)\.vercel/"                     ".vercel (Vercel build/cache)"]
   [#"(^|/)\.output/"                     ".output (build output)"]
   [#"(^|/)(dist|build)/"                 "dist/ or build/ (generated output)"]
   [#"(^|/)target/(debug|release|wasm32|[a-z0-9_]+-(unknown|apple|pc)-)" "target/ (Cargo build output)"]
   [#"(^|/)__pycache__/"                  "__pycache__ (Python bytecode cache)"]
   [#"\.py[cod]$"                         "compiled Python (*.pyc/pyo/pyd)"]
   [#"(^|/)\.pytest_cache/"               ".pytest_cache"]
   [#"(^|/)\.mypy_cache/"                 ".mypy_cache"]
   [#"(^|/)\.ruff_cache/"                 ".ruff_cache"]
   [#"(^|/)(\.venv|venv)/"               "Python virtualenv (.venv/venv)"]
   [#"(^|/)\.tox/"                        ".tox"]
   [#"\.egg-info(/|$)"                    "*.egg-info (Python package metadata)"]
   [#"(?i)chrome-profile"                 "⚠ browser profile — CONTAINS SECRETS (cookies/login-data); never commit"]
   [#"(^|/)src/paraglide/"                "generated paraglide i18n output (regenerated from messages/*.json)"]
   [#"(^|/)\.DS_Store$"                   ".DS_Store (macOS junk)"]
   [#"(^|/)Thumbs\.db$"                   "Thumbs.db (Windows junk)"]])

(defn- repo-root []
  (str/trim (:out (__shell {:out :string} "git rev-parse --show-toplevel"))))

(defn- staged-added-paths []
  (->> (__shell {:out :string} "git diff --cached --name-only --diff-filter=ACR")
       :out str/split-lines
       (map str/trim)
       (remove str/blank?)))

(defn- load-allow [root]
  (let [f (fs/file root "70-tools/scripts/lint/ignorable-allowlist.edn")]
    (if (fs/exists? f)
      (->> (:allow (edn/read-string (slurp (fs/file f))))
           (map re-pattern) vec)
      [])))

(defn- allowed? [allow path]
  (boolean (some #(re-find % path) allow)))

(defn- first-hit [path]
  (some (fn [[re label]] (when (re-find re path) label)) deny))

(let [root      (repo-root)
      allow     (load-allow root)
      staged    (staged-added-paths)
      hits      (->> staged
                     (remove #(allowed? allow %))
                     (keep (fn [p] (when-let [label (first-hit p)] [p label])))
                     vec)]
  (if (seq hits)
    (do
      (println "✘ no-ignorable-staged: refusing to commit generated/secret paths")
      (println "  (these should be .gitignored, not tracked):")
      (println)
      (doseq [[p label] hits]
        (println (format "   %-60s  %s" p label)))
      (println)
      (println "  Fix:")
      (println "    1. add a matching rule to the nearest .gitignore")
      (println "    2. unstage:  git rm -r --cached <path>")
      (println)
      (println "  Intentional? add a regex to 70-tools/scripts/lint/ignorable-allowlist.edn")
      (println "  (:allow [\"…\"]) — or bypass once with `git commit --no-verify`.")
      (.exit js/process 1))
    (.exit js/process 0)))
