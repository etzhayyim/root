#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (sumitsubo actor test harness).
(ns sumitsubo.py.test-agent
  "sumitsubo 墨壺 — test harness (babashka clojure.test; no kotoba host needed).

  Verifies the structural invariants of ADR-2606033600:
    G1 cleanroom (only published call shapes used)
    G2 kotoba Datom log emission
    G4 honesty (malformed ops dropped; unsupported tokens skipped)
    G5 no native DWG write
    G7 generated geometry marked representative"
  (:require [clojure.test :refer [deftest testing is run-tests]]
            [sumitsubo.py.agent :as agent]))

;; ── validate-ops ──────────────────────────────────────────────────────────────
(deftest test-validate-ops
  (testing "well-formed op kept"
    (let [good [{"op" "rect" "x" 0 "y" 0 "w" 10 "h" 10}]]
      (is (= good (agent/validate-ops good)))))
  (testing "unknown op dropped (G1/G4)"
    (is (= [] (agent/validate-ops [{"op" "frobnicate"}]))))
  (testing "op missing required fields dropped"
    (is (= [] (agent/validate-ops [{"op" "circle" "cx" 0}])))))

;; ── handle-model generative ───────────────────────────────────────────────────
(deftest test-model-generative
  (testing "NL prompt → box + circle ops"
    (let [out   (agent/handle-model {"prompt" "make a box 10x20x30 and a circle r=5"
                                     "drawing_id" "d1"})
          kinds (set (map #(get % "op") (get out "ops")))]
      (is (contains? kinds "box"))
      (is (contains? kinds "circle"))))
  (testing "generated geometry representative (G7)"
    (let [out (agent/handle-model {"prompt" "make a box 10x20x30 and a circle r=5"
                                   "drawing_id" "d1"})]
      (is (= "representative" (get out "sourcing")))))
  (testing "emits :dwg.* datoms (G2)"
    (let [out   (agent/handle-model {"prompt" "make a box 10x20x30 and a circle r=5"
                                     "drawing_id" "d1"})
          attrs (set (map #(nth % 1) (get out "datoms")))]
      (is (contains? attrs ":dwg/id"))
      (is (contains? attrs ":dwg.entity/kind"))))
  (testing "sourcing stamped on drawing"
    (let [out (agent/handle-model {"prompt" "make a box 10x20x30 and a circle r=5"
                                   "drawing_id" "d1"})]
      (is (some #(= (nth % 1) ":dwg/sourcing") (get out "datoms"))))))

;; ── handle-model default ──────────────────────────────────────────────────────
(deftest test-model-default
  (testing "always yields at least one op (default square)"
    (let [out (agent/handle-model {"prompt" "something abstract" "drawing_id" "d2"})]
      (is (>= (count (get out "ops")) 1)))))

;; ── handle-draft ──────────────────────────────────────────────────────────────
(deftest test-draft
  (let [ops [{"op" "rect" "x" 0 "y" 0 "w" 40 "h" 20}
             {"op" "circle" "cx" 0 "cy" 0 "r" 5}
             {"op" "polyline" "points" [[0 0] [1 1]] "closed" false}]
        out  (agent/handle-draft {"ops" ops})
        kinds (set (map #(get % "kind") (get out "suggestions")))]
    (testing "suggests named layers when on default layer"
      (is (contains? kinds "layer")))
    (testing "suggests dimensions for rect/circle"
      (is (contains? kinds "dimension")))
    (testing "flags open polyline"
      (is (contains? kinds "constraint")))))

;; ── handle-interop vectorworks ────────────────────────────────────────────────
(deftest test-interop-vectorworks
  (let [script [["Layer" "design"]
                ["Rect" 0 0 100 50]
                ["Oval" 0 0 20 20]
                ["Extrude" 0 0 10 0 10 10 0 10 5]]
        out    (agent/handle-interop {"flavor" "vectorworks" "script" script})
        kinds  (map #(get % "op") (get out "ops"))]
    (testing "VS Layer+Rect translated"
      (is (some #{"layer"} kinds))
      (is (some #{"rect"} kinds)))
    (testing "VS Extrude → extrude op"
      (is (some #{"extrude"} kinds)))))

;; ── handle-interop autocad ────────────────────────────────────────────────────
(deftest test-interop-autocad
  (let [script [["LAYER" "0"]
                ["LINE" 0 0 10 0]
                ["CIRCLE" 5 5 2]
                ["PLINE" 0 0 10 0 10 10]
                ["BOGUS" 1]]
        out   (agent/handle-interop {"flavor" "autocad" "script" script})
        kinds (map #(get % "op") (get out "ops"))]
    (testing "AutoCAD LINE/CIRCLE translated"
      (is (= 1 (count (filter #{"line"} kinds))))
      (is (some #{"circle"} kinds)))
    (testing "PLINE → polyline"
      (is (some #{"polyline"} kinds)))
    (testing "unsupported token skipped honestly (G4)"
      (is (not (some #{"frobnicate"} kinds)))
      (is (= 4 (count (get out "ops")))))))

;; ── handle-export ─────────────────────────────────────────────────────────────
(deftest test-export
  (testing "dxf full + native"
    (let [rec (get (agent/handle-export {"drawing_id" "d1" "format" "dxf"}) "record")]
      (is (= "full" (get rec "fidelity")))
      (is (true? (get rec "native")))))
  (testing "ifc subset honesty (N6)"
    (let [rec (get (agent/handle-export {"drawing_id" "d1" "format" "ifc"}) "record")]
      (is (= "subset" (get rec "fidelity")))
      (is (contains? rec "note"))))
  (testing "dwg never native (G5)"
    (let [rec (get (agent/handle-export {"drawing_id" "d1" "format" "dwg"}) "record")]
      (is (false? (get rec "native")))
      (is (= "DWG_PROPRIETARY" (get rec "advisory")))))
  (testing "gltf full"
    (is (= "full" (get agent/EXPORT_FIDELITY "gltf")))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'sumitsubo.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
