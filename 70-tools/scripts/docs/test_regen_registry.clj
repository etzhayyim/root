;; Tests for regen-registry.clj (babashka port of regen-registry.py).
;; Run: nbb scripts/run-task.cljs test:docs-registry
;; (which is `clojure -Sdeps … -M 70-tools/scripts/docs/test_regen_registry.clj`, from the repo
;; root -- `here` is derived from *file*, so the working directory matters.)
;; Covers parse-frontmatter (happy + edge), entry build/order, JSON+EDN
;; encoders, byte-identity round-trip, and the live-repo freshness guard.

(ns test-regen-registry
  (:require [clojure.test :refer [deftest is run-tests]]
            [babashka.fs :as fs]
            [babashka.process :as p]
            [cheshire.core :as json]
            [clojure.string :as str]))

(def here (fs/parent (fs/absolutize *file*)))
(def impl (str (fs/path here "regen-registry.clj")))

;; Load the implementation for its functions only. Declaring that explicitly is what keeps its
;; entry guard from running -main and exiting this process -- see the guard's own comment for why
;; the default is the other way round.
(System/setProperty "regen-registry.library-load" "1")
(load-file impl)

(defn- pf [t] (regen-registry/parse-frontmatter t))

(deftest script-exists
  (is (fs/exists? impl)))

(deftest parse-frontmatter-minimal
  (let [out (pf "---\nid: x\ntitle: Hello\nauthoritative: true\n---\nbody")]
    (is (= "x" (get out "id")))
    (is (= "Hello" (get out "title")))
    (is (true? (get out "authoritative")))))

(deftest parse-frontmatter-lists
  (let [out (pf "---\nid: x\nrelated:\n  - a\n  - \"b\"\nempty: []\n---\n")]
    (is (= ["a" "b"] (get out "related")))
    (is (= [] (get out "empty")))))

(deftest parse-frontmatter-no-yaml-returns-nil
  (is (nil? (pf "no front matter here"))))

(deftest parse-frontmatter-unterminated-returns-nil
  (is (nil? (pf "---\nid: x\ntitle: y\n"))))

(deftest parse-frontmatter-bool-false
  (is (false? (get (pf "---\nid: x\nauthoritative: false\n---\n") "authoritative"))))

(deftest parse-frontmatter-quoted-arraylike-stays-string
  ;; the tiny parser treats a YAML inline-array value as a scalar string
  (let [out (pf "---\nid: x\nsuperseded_by: [\"2606161200 (D2 only)\"]\n---\n")]
    (is (= "[\"2606161200 (D2 only)\"]" (get out "superseded_by")))))

(deftest build-entry-shape-and-order
  (let [e (regen-registry/build-entry "90-docs/a.md" {"id" "a" "title" "A" "doc_type" "adr"})]
    (is (= "path" (ffirst e)))                       ; path always first
    (is (= ["id" "a"] (second e)))                   ; then surfaced order
    (is (some #(= ["authoritative" false] %) e))     ; authoritative defaulted
    (is (some #(= ["related" []] %) e))))            ; list keys defaulted

(deftest json-encoder-fidelity
  (is (= "true" (#'regen-registry/json-encode true 0)))
  (is (= "\"he said \\\"hi\\\"\"" (#'regen-registry/json-encode "he said \"hi\"" 0)))
  (is (= "[]" (#'regen-registry/json-encode [] 0))))

(deftest edn-encoder-fidelity
  (is (= ":doc-type" (#'regen-registry/edn-keyword "doc_type")))
  (is (= "\"a\\\\b\"" (#'regen-registry/edn-value "a\\b")))
  (is (= "[\"a\" \"b\"]" (#'regen-registry/edn-value ["a" "b"]))))

(deftest render-json-shape
  (let [out (regen-registry/render-json
             [(regen-registry/build-entry "90-docs/a.md" {"id" "a" "title" "A"})] "2026-06-16")
        parsed (json/parse-string out false)]
    (is (str/starts-with? out "{\n  \"version\": 2,\n"))
    (is (= 2 (get parsed "version")))
    (is (= 1 (count (get parsed "entries"))))
    (is (str/ends-with? out "}\n"))))

(deftest render-edn-shape
  (let [out (regen-registry/render-edn
             [(regen-registry/build-entry "90-docs/a.md" {"id" "a" "doc_type" "adr"})] "2026-06-16")]
    (is (str/starts-with? out "{:version 2\n :updated-at "))
    (is (str/includes? out ":doc-type \"adr\""))
    (is (not (str/includes? out ":doc_type")))      ; snake never leaks into EDN
    (is (str/ends-with? out "]}\n"))))

(deftest live-repo-in-sync
  ;; The committed registry must match what we'd regenerate (json + edn).
  ;;
  ;; This used to shell out to `bb 70-tools/scripts/docs/regen-registry.clj --check`. Two things
  ;; were wrong with that after ADR-2607173000 retired babashka: the binary is gone on any fleet
  ;; node, and the subprocess bought nothing -- the implementation is ALREADY load-file'd into this
  ;; process above, and its -main RETURNS an exit code rather than calling System/exit (the exit is
  ;; in the script's own entry guard). So call it directly and capture what it prints. One fewer
  ;; process, one fewer runtime assumption, and a failure now reports in this process's output
  ;; instead of inside a captured string.
  ;; Capture *err* as well as *out*: -main prints the "in sync" line to stdout but every drift
  ;; message to stderr, so capturing only stdout reports a failure with an empty explanation.
  (let [out (java.io.StringWriter.)
        err (java.io.StringWriter.)
        exit (binding [*out* out *err* err] (regen-registry/-main "--check"))
        text (str out err)]
    (is (zero? exit) (str "registry drift: " text))
    (is (str/includes? text "in sync"))))

;; Unconditional exit. The guard was `(when (= *file* (System/getProperty "babashka.file")) …)`,
;; which is false under every runtime except babashka -- so run under anything else this file ran
;; its tests, printed the failures, and then exited 0 regardless. A test runner that always
;; succeeds does not report a green suite; it reports nothing, in the shape of a green suite.
(let [{:keys [fail error]} (run-tests 'test-regen-registry)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
