;; Tests for regen-graph-edn.clj (EDN relation-graph projection).
;;
;; The generator projects 90-docs/_registry/docs.edn → graph.edn with typed
;; ontology predicates. Tests cover:
;;   - doc: IRI prefixing
;;   - minimal projection + schema.org type mapping (adr→TechArticle / explanation→Article)
;;   - relation predicate mapping (related/supersedes/… as doc: IRI vectors)
;;   - no-id entry is defensive-skipped
;;   - unknown doc-type defaults to TechArticle
;;   - build-graph sorts :graph by :id
;;   - empty registry → empty :graph (not an error)
;;   - :context carries the expected predicates
;;   - render-edn round-trips (read-string of the rendered output is structurally equal)
;;
;; Run: bb 70-tools/scripts/docs/test_regen_graph_edn.clj

(require '[clojure.test :refer [deftest is run-tests]]
         '[clojure.edn :as edn]
         '[babashka.fs :as fs])

;; Load the implementation for its functions only -- see the guard's own comment for why the
;; default is the other way round.
(System/setProperty "regen-graph-edn.library-load" "1")
(load-file (str (fs/path (fs/parent *file*) "regen-graph-edn.clj")))
(alias 'g 'regen-graph-edn)

(deftest doc-iri-helper
  (is (= "doc:adr-2605262500" (#'g/doc-iri "adr-2605262500"))))

(deftest project-entry-minimal
  (let [node (g/project-entry {:id "test-1" :path "90-docs/foo.md" :title "Test 1"
                               :status "active" :doc-type "explanation"
                               :topic "test" :authoritative false})]
    (is (some? node))
    (is (= "doc:test-1" (:id node)))
    (is (= "Article" (:type node)))            ; explanation → Article
    (is (= "Test 1" (:title node)))
    (is (= "active" (:status node)))
    (is (= "test" (:topic node)))
    (is (= false (:authoritative node)))))

(deftest project-entry-with-relations
  (let [node (g/project-entry {:id "test-2" :path "90-docs/bar.md" :title "Test 2"
                               :status "active" :doc-type "adr" :topic "rel-test"
                               :authoritative true
                               :related ["test-1" "test-3"]
                               :supersedes ["old-1"]
                               :superseded-by ["new-1"]
                               :amends ["amend-1"]
                               :amended-by ["amender-1"]})]
    (is (= "TechArticle" (:type node)))        ; adr → TechArticle
    (is (= ["doc:test-1" "doc:test-3"] (:related node)))
    ;; EDN projection uses uniform vectors (no single→scalar collapse)
    (is (= ["doc:old-1"] (:supersedes node)))
    (is (= ["doc:new-1"] (:superseded-by node)))
    (is (= ["doc:amend-1"] (:amends node)))
    (is (= ["doc:amender-1"] (:amended-by node)))))

(deftest project-entry-no-id-returns-nil
  (is (nil? (g/project-entry {:path "90-docs/no-id.md" :title "headless"}))))

(deftest doc-type-default
  (let [node (g/project-entry {:id "test-unknown-type" :path "90-docs/foo.md"
                               :title "Test" :status "active"
                               :doc-type "snapshot" :topic "test" :authoritative true})]
    (is (= "TechArticle" (:type node)))))

(deftest build-graph-sorted
  (let [g (g/build-graph {:version 2 :updated-at "2026-05-27"
                          :entries [{:id "z-last" :path "90-docs/z.md" :title "Z"
                                     :status "active" :doc-type "adr" :topic "z"
                                     :authoritative true}
                                    {:id "a-first" :path "90-docs/a.md" :title "A"
                                     :status "active" :doc-type "explanation" :topic "a"
                                     :authoritative false}]})
        nodes (:graph g)]
    (is (contains? g :context))
    (is (= 2 (count nodes)))
    (is (= "doc:a-first" (:id (first nodes))))
    (is (= "doc:z-last" (:id (second nodes))))))

(deftest build-graph-empty
  (let [g (g/build-graph {:version 2 :updated-at "2026-05-27" :entries []})]
    (is (= [] (:graph g)))
    (is (contains? g :context))))

(deftest context-preserved
  (let [ctx g/context]
    (is (= "@id" (:id ctx)))
    (is (= "@type" (:type ctx)))
    (is (= "@id" (get-in ctx [:related :type])))
    (is (= "@id" (get-in ctx [:supersedes :type])))
    (is (= "@id" (get-in ctx [:superseded-by :type])))
    (is (= "@id" (get-in ctx [:amends :type])))
    (is (= "@id" (get-in ctx [:amended-by :type])))))

(deftest render-roundtrips
  (let [g (g/build-graph {:version 2 :updated-at "2026-05-27"
                          :entries [{:id "x" :path "90-docs/x.md" :title "X \"quoted\""
                                     :status "active" :doc-type "adr" :topic "x"
                                     :authoritative true :related ["y"]}]})
        parsed (edn/read-string (g/render-edn g))]
    (is (= (:graph g) (:graph parsed)))
    (is (= (:context g) (:context parsed)))))

(let [{:keys [fail error]} (run-tests 'user)]
  (System/exit (if (pos? (+ fail error)) 1 0)))
