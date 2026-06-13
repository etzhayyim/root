(ns etzhayyim.tools.test-maturation-agent
  "Tests for the langgraph-clj maturation agent (port of
  70-tools/langgraph_maturation_agent.py)."
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is testing use-fixtures]]
            [etzhayyim.tools.maturation-agent :as agent]))

;; ─── Fixture: temp actors dir with 2 fake actors + 1 empty one ───────

(def ^:dynamic *actors-dir* nil)

(def seed-schema "entity Profile {\n    id: string\n}\n")
(def seed-main-py "app = KotodamaApp()\n")

(defn- mk-actor!
  "Creates <root>/<actor>/{schema/<platform>.kotoba, src/main.py}."
  [root actor]
  (let [platform (str/replace actor "-compat" "")
        schema (io/file root actor "schema" (str platform ".kotoba"))
        main-py (io/file root actor "src" "main.py")]
    (io/make-parents schema)
    (spit schema seed-schema)
    (io/make-parents main-py)
    (spit main-py seed-main-py)))

(defn- delete-recursively! [^java.io.File f]
  (when (.isDirectory f)
    (doseq [child (.listFiles f)]
      (delete-recursively! child)))
  (.delete f))

(defn- with-fixture-dir [f]
  (let [root (.toFile (java.nio.file.Files/createTempDirectory
                       "maturation-agent-test"
                       (make-array java.nio.file.attribute.FileAttribute 0)))]
    (try
      (mk-actor! root "foo-compat")
      (mk-actor! root "bar-compat")
      ;; an actor dir WITHOUT schema/main.py files — must be skipped silently
      (.mkdirs (io/file root "baz-compat"))
      ;; a non-compat dir — must not be picked up at all
      (.mkdirs (io/file root "kotodama"))
      (binding [*actors-dir* (.getPath root)]
        (f))
      (finally
        (delete-recursively! root)))))

(use-fixtures :each with-fixture-dir)

;; ─── Tests ───────────────────────────────────────────────────────────

(deftest test-get-l1-actors-sorted
  (is (= ["bar-compat" "baz-compat" "foo-compat"]
         (agent/get-l1-actors *actors-dir*))))

(deftest test-agent-loop-upgrades-actors-to-l3
  (let [finals (agent/run-agent-loop {:actors-dir *actors-dir*})]
    (testing "graph threads state through the three nodes"
      (is (= 3 (count finals)))
      (let [foo-state (first (filter #(= "foo-compat" (:current-actor %)) finals))]
        (is (= "Found complex objects for foo" (:research-data foo-state)))))
    (testing "both real actors got the L3 schema appendix"
      (doseq [[actor platform] [["foo-compat" "foo"] ["bar-compat" "bar"]]]
        (let [schema (slurp (io/file *actors-dir* actor "schema" (str platform ".kotoba")))]
          (is (str/starts-with? schema seed-schema))
          (is (str/includes? schema "// Auto-generated L3 properties by LangGraph"))
          (is (str/includes? schema "entity AdvancedProfile {"))
          (is (= (str seed-schema agent/l3-schema-appendix) schema)))))
    (testing "both real actors got the L3 endpoint appendix"
      (doseq [actor ["foo-compat" "bar-compat"]]
        (let [main-py (slurp (io/file *actors-dir* actor "src" "main.py"))]
          (is (str/includes? main-py "@app.route(\"/v2/advanced\", methods=[\"POST\"])"))
          (is (str/includes? main-py "\"\"\"Auto-generated L3 endpoint.\"\"\""))
          (is (= (str seed-main-py agent/l3-endpoint-appendix) main-py)))))
    (testing "an actor dir without the files is skipped silently (Python parity)"
      (is (not (.exists (io/file *actors-dir* "baz-compat" "schema" "baz.kotoba"))))
      (is (not (.exists (io/file *actors-dir* "baz-compat" "src" "main.py")))))))

(deftest test-batch-size-limits-processing
  (agent/run-agent-loop {:actors-dir *actors-dir* :batch-size 1})
  (testing "only the first (sorted) actor is matured"
    (is (str/includes? (slurp (io/file *actors-dir* "bar-compat" "schema" "bar.kotoba"))
                       "entity AdvancedProfile"))
    (is (= seed-schema
           (slurp (io/file *actors-dir* "foo-compat" "schema" "foo.kotoba"))))))
