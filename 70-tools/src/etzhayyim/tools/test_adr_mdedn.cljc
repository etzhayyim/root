(ns etzhayyim.tools.test-adr-mdedn
  "Tests for etzhayyim.tools.adr-mdedn (.md ↔ .md.edn round-trip)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim.tools.adr-mdedn :as m]))

(def sample-md
  (str "---\n"
       "id: adr-2606162030-silicon-fab-flow-clj-port\n"
       "title: \"ADR-2606162030: silicon fab → runnable cljc + kotoba-Datom\"\n"
       "status: accepted\n"
       "doc_type: adr\n"
       "topic: silicon-fab-flow-clj-port\n"
       "authoritative: true\n"
       "last_verified: 2026-06-16\n"
       "priority: 5.5\n"
       "axis: architecture\n"
       "weight: 0.3\n"
       "priority_note: \"Implementation record; no invariant amended.\"\n"
       "authoritative_for:\n"
       "  - \"silicon fab-flow runnable methods\"\n"
       "depends_on:\n"
       "  - adr-2605242500-silicon-charter\n"
       "  - adr-2605262130-kotoba-storage-substrate-unification\n"
       "related:\n"
       "  - adr-2606082000-niyaku-port-cargo-handling\n"
       "supersedes: []\n"
       "superseded_by: []\n"
       "---\n\n"
       "# ADR-2606162030: silicon fab → runnable cljc\n\n"
       "**Status**: accepted\n\n"
       "# Context\n\n"
       "Body with a \"quoted\" word and a backslash \\ and code `Y = exp(-D*A)`.\n"))

(deftest test-md->data-shape
  (let [d (m/md->data sample-md)]
    (is (= "adr-2606162030-silicon-fab-flow-clj-port" (:id d)))
    (is (= true (:authoritative d)))            ; typed boolean
    (is (= 5.5 (:priority d)))                  ; typed number
    (is (= [] (:supersedes d)))                 ; empty vector
    (is (= ["adr-2605242500-silicon-charter"
            "adr-2605262130-kotoba-storage-substrate-unification"]
           (:depends-on d)))
    (is (str/starts-with? (:body d) "# ADR-2606162030"))
    (is (str/includes? (:body d) "\"quoted\""))))  ; quotes survive in body

(deftest test-mdedn-is-valid-edn
  (let [d (m/md->data sample-md)
        text (m/emit-mdedn d "x.md")]
    ;; the emitted file is valid commented EDN and re-reads to the same data
    (is (str/starts-with? text ";;"))           ; has a comment header
    (is (str/includes? text "#md \""))          ; body is a #md tagged string
    (is (= d (m/read-mdedn text)))))

(deftest test-roundtrip-md->mdedn->data
  ;; .md → data → .md.edn → data  is identity on the DATA
  (let [d (m/md->data sample-md)]
    (is (= d (m/read-mdedn (m/emit-mdedn d))))))

(deftest test-roundtrip-md->mdedn->md->data
  ;; full loop through both representations preserves the data
  (let [d (m/md->data sample-md)
        mdedn (m/emit-mdedn d)
        d2 (m/read-mdedn mdedn)
        md2 (m/mdedn->md d2)
        d3 (m/md->data md2)]
    (is (= d d2))
    (is (= d d3))))

(deftest test-rendered-md-has-frontmatter-and-body
  (let [d (m/md->data sample-md)
        md (m/mdedn->md d)]
    (is (str/starts-with? md "---\n"))
    (is (str/includes? md "id: adr-2606162030-silicon-fab-flow-clj-port"))
    (is (str/includes? md "title: \"ADR-2606162030:"))   ; title re-quoted
    (is (str/includes? md "supersedes: []"))
    (is (str/includes? md "# Context"))))

(deftest test-body-escaping-edge
  ;; a body containing #md-breaking chars survives the EDN string round-trip
  (let [d {:id "x" :status "draft" :body "line with \" and \\ and ] and ;not-a-comment"}
        back (m/read-mdedn (m/emit-mdedn d))]
    (is (= (:body d) (:body back)))))

(deftest test-no-frontmatter-doc
  (let [d (m/md->data "# Just a title\n\nno front matter here\n")]
    (is (= "# Just a title\n\nno front matter here" (:body d)))
    (is (= #{:body} (set (keys d))))))

(def ^:private entries
  [{:id "adr-2606162200-b" :title "B: has a \"quote\"" :status "accepted"
    :doc-type "adr" :priority 5.0 :authoritative true :depends-on ["adr-x"]
    :file "2606162200-b.md"}
   {:id "adr-2606162030-a" :title "A" :status "proposed" :doc-type "adr"
    :file "2606162030-a.md"}])

(deftest test-emit-index-is-parseable-edn
  ;; the GENERATED index parses with clojure.edn (the 2.8MB single-line one did NOT)
  (let [text (m/emit-index entries)
        parsed (clojure.edn/read-string text)]
    (is (str/starts-with? text ";;"))            ; header comment
    (is (= 2 (count parsed)))
    (is (= "adr-2606162200-b" (:id (first parsed))))
    (is (= true (:authoritative (first parsed))))  ; typed boolean survives
    (is (= ["adr-x"] (:depends-on (first parsed))))))

(deftest test-emit-index-one-entry-per-line
  ;; diff/merge-friendliness: exactly one entry per line between the [ ] brackets
  (let [lines (str/split-lines (m/emit-index entries))
        entry-lines (filter #(str/starts-with? % "{") lines)]
    (is (= 2 (count entry-lines)))))

(deftest test-entry-id-coerced-to-string
  ;; a bare-numeric front-matter id must not stay a Long (it breaks the id sort)
  (let [tmp (java.io.File/createTempFile "adr" ".md")]
    (spit tmp "---\nid: 2605152300\n---\n\n# Numeric id ADR\n")
    (let [e (m/file->entry (.getPath tmp))]
      (is (string? (:id e)))
      (is (= "2605152300" (:id e))))
    (.delete tmp)))

(deftest test-no-frontmatter-entry-fallbacks
  (let [tmp (java.io.File/createTempFile "2699010101-foo" ".md")
        path (.getPath tmp)]
    (spit tmp "# A Title Without Front Matter\n\nbody\n")
    (let [e (m/file->entry path)]
      (is (= "A Title Without Front Matter" (:title e)))
      (is (= "unknown" (:status e)))
      (is (= "adr" (:doc-type e))))
    (.delete tmp)))

(deftest test-edn-comments-and-discard-are-ignored
  ;; a hand-authored .md.edn with ;; comments and #_ discard parses cleanly
  (let [text (str ";; a header comment\n"
                  "{:id \"x\"\n"
                  " #_:draft #_\"discarded note\"\n"
                  " :status \"accepted\"  ; trailing comment\n"
                  " :body #md \"# Hi\"}\n")
        d (m/read-mdedn text)]
    (is (= "x" (:id d)))
    (is (= "accepted" (:status d)))
    (is (= "# Hi" (:body d)))
    (is (not (contains? d :draft)))))
