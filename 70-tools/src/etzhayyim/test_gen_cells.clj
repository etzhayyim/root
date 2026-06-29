(ns etzhayyim.test-gen-cells
  "Tests for `bb gen:cells` — fold actor `:actor/heartbeat-cells` declarations into the
  fleet cell registry. Exercises declared-cells / emit-cell / check / apply! against
  temp fixtures (no touching the real cells.edn)."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [etzhayyim.gen-cells :as g]))

(defn- tmp-fixture
  "A temp actors-dir (one actor 'foo' declaring a heartbeat cell) + a temp cells.edn
  with one pre-existing cell. Returns {:adir :cells}."
  []
  (let [base  (io/file (System/getProperty "java.io.tmpdir") (str "gencells-" (System/nanoTime)))
        adir  (io/file base "actors")
        a1    (io/file adir "foo")
        cells (io/file base "cells.edn")]
    (.mkdirs a1)
    (spit (io/file a1 "manifest.edn")
          (pr-str {:actor/id "foo"
                   :actor/heartbeat-cells
                   [{:cell/name "FooHeartbeatCell" :cell/module "foo.cell" :cell/entry "fire"
                     :cell/node "dan" :cell/cron "5 * * * *" :cell/healthz 13900 :cell/adr ["X"]}]}))
    (spit cells (str "{:runner {:healthz_port_range [13000 14000]} "
                     ":cell [{:name \"Existing\" :module \"e.cell\" :entry \"fire\" :node \"levi\" "
                     ":trigger {:kind \"cron\" :expr \"0 * * * *\"} :healthz_port 13800 :adr [\"Y\"]}]}"))
    {:adir (str adir) :cells (str cells)}))

(deftest declared-emit-check-apply
  (let [{:keys [adir cells]} (tmp-fixture)]
    (binding [g/*actors-dir* adir g/*cells-path* cells]
      (testing "declared-cells reads :actor/heartbeat-cells (NOT :actor/cells)"
        (let [d (g/declared-cells)]
          (is (= 1 (count d)))
          (is (= "FooHeartbeatCell" (:name (first d))))
          (is (= {:kind "cron" :expr "5 * * * *"} (:trigger (first d))))))
      (testing "emit-cell is comma-free + round-trips to the same data"
        (let [c (dissoc (first (g/declared-cells)) :__actor)
              s (g/emit-cell c)]
          (is (not (str/includes? s ",")) "matches cells.edn's comma-free style")
          (is (= c (edn/read-string s)) "round-trips")))
      (testing "check reports drift BEFORE apply (declared cell missing)"
        (let [{:keys [errors missing]} (g/check)]
          (is (= ["FooHeartbeatCell"] missing))
          (is (seq errors))))
      (testing "apply! appends the declared cell, existing preserved"
        (let [r (g/apply!)
              reg (edn/read-string (slurp cells))
              names (set (map :name (:cell reg)))]
          (is (= ["FooHeartbeatCell"] (:appended r)))
          (is (empty? (:errors r)))
          (is (= #{"Existing" "FooHeartbeatCell"} names))
          (is (= 2 (count (:cell reg))) "exactly one cell added")))
      (testing "check is GREEN after apply"
        (is (empty? (:errors (g/check)))))
      (testing "apply! is idempotent (second run appends nothing)"
        (is (= [] (:appended (g/apply!))))))))
