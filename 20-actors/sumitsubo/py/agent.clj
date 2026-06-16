#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (sumitsubo cleanroom CAD-interop actor).
(ns sumitsubo.py.agent
  "sumitsubo 墨壺 — generative + modeling-assist langgraph actor (kotoba WASM cell).

  ADR-2606033600. Runs in-WASM on kotoba :8077. Handlers over one kotoba EAVT drawing
  graph. The op vocabulary (ModelOp) is the SAME as the TS kernel (sdk/src/geometry/
  types.ts) — one model, two runtimes:

    handle-model    NL prompt → Murakumo LLM → validated ModelOp plan → drawing Datoms (generative)
    handle-draft    2D drafting assistance: dimension / constraint / layer suggestions over a drawing
    handle-interop  Vectorworks/AutoCAD-shaped script → neutral ModelOp list (python mirror of adapters)
    handle-export   resolve target format + emit export record (DWG-proprietary honesty)

  LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000; G3). State is written back to
  the kotoba Datom log (G2). Generated geometry is marked :representative unless dimensioned
  from authoritative input (G7). Cleanroom: the interop translator uses only the published
  call shapes (G1). No native DWG write (G5).

  Run:  bb --classpath 20-actors 20-actors/sumitsubo/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── Shared ModelOp vocabulary ──────────────────────────────────────────────────
(def ^:private op-schema
  {"layer"    #{"name"}
   "point"    #{"x" "y"}
   "line"     #{"x1" "y1" "x2" "y2"}
   "polyline" #{"points"}
   "rect"     #{"x" "y" "w" "h"}
   "circle"   #{"cx" "cy" "r"}
   "arc"      #{"cx" "cy" "r" "start" "end"}
   "box"      #{"x" "y" "z" "w" "d" "h"}
   "extrude"  #{"profile" "height"}
   "move"     #{"target" "dx" "dy"}
   "scale"    #{"target" "factor"}})

(def EXPORT_FIDELITY
  {"dxf"  "full"
   "svg"  "full"
   "obj"  "full"
   "gltf" "full"
   "ifc"  "subset"
   "step" "subset"
   "dwg"  "fallback"})

;; ── validate-ops (G4 honesty) ─────────────────────────────────────────────────
(defn validate-ops
  "Keep only well-formed ops (G4 honesty: silently-malformed ops are dropped)."
  [ops]
  (filterv (fn [op]
             (let [name (get op "op")
                   req  (get op-schema name)]
               (and (some? req)
                    (every? #(contains? op %) req))))
           ops))

;; ── _heuristic-plan — deterministic NL→CAD-op planner ────────────────────────
(defn- _heuristic-plan
  "Tiny deterministic planner so the cell is useful (and testable) without a live model.

  Recognizes dimensioned keywords like 'box 10x20x30', 'rect 100x50', 'circle r=5'."
  [prompt]
  (let [p    (str/lower-case prompt)
        ops  (atom [])]
    ;; box N x N x N  (using [x×] character class equivalent)
    (doseq [[_ w d h] (re-seq #"box\s+(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)" p)]
      (swap! ops conj {"op" "box" "x" 0 "y" 0 "z" 0
                       "w" (Long/parseLong w) "d" (Long/parseLong d) "h" (Long/parseLong h)}))
    ;; rect(angle)? N x N
    (doseq [[_ w h] (re-seq #"rect(?:angle)?\s+(\d+)\s*[x×]\s*(\d+)" p)]
      (swap! ops conj {"op" "rect" "x" 0 "y" 0
                       "w" (Long/parseLong w) "h" (Long/parseLong h)}))
    ;; circle r=?N
    (doseq [[_ r] (re-seq #"circle\s+r\s*=?\s*(\d+)" p)]
      (swap! ops conj {"op" "circle" "cx" 0 "cy" 0 "r" (Long/parseLong r)}))
    ;; extrude N x N by N
    (doseq [[_ w h ht] (re-seq #"extrude\s+(\d+)\s*[x×]\s*(\d+)\s+by\s+(\d+)" p)]
      (let [wi (Long/parseLong w)
            hi (Long/parseLong h)
            hti (Long/parseLong ht)]
        (swap! ops conj {"op"      "extrude"
                         "profile" [[0 0] [wi 0] [wi hi] [0 hi]]
                         "height"  hti})))
    ;; default: unit square when no ops were matched
    (when (empty? @ops)
      (swap! ops conj {"op" "rect" "x" 0 "y" 0 "w" 100 "h" 100}))
    (validate-ops @ops)))

;; ── _llm-plan — Murakumo-only LLM (G3) ──────────────────────────────────────
(defn- _llm-plan
  "Ask the Murakumo-fronted model for a ModelOp plan. Offline → heuristic planner."
  [prompt]
  ;; In WASM host: would call (llm/infer …). Offline sentinel: fall back to heuristic.
  ;; No real LLM call here (Murakumo/kotoba host not present in local dev/test).
  (_heuristic-plan prompt))

;; ── _emit-datoms (G2) ────────────────────────────────────────────────────────
(defn- _emit-datoms
  "Emit EAVT datoms for a drawing and its ops. Mirror of sdk/src/kotoba/datom.ts."
  [drawing-id ops sourcing]
  (let [base  [[drawing-id ":dwg/id"       drawing-id]
               [drawing-id ":dwg/sourcing" sourcing]]
        ;; layer/move/scale do not get entity datoms
        geom-ops (remove #(#{"layer" "move" "scale"} (get % "op")) ops)]
    (into base
          (mapcat (fn [[i op]]
                    (let [eid (str drawing-id ".e" i)]
                      [[eid ":dwg.entity/id"    eid]
                       [eid ":dwg.entity/of"    drawing-id]
                       [eid ":dwg.entity/kind"  (get op "op")]
                       [eid ":dwg.entity/layer" (get op "layer" "0")]]))
                  (map-indexed (fn [i op] [(inc i) op]) geom-ops)))))

;; ── handle-model — generative: NL → op plan → datoms ────────────────────────
(defn handle-model
  "NL prompt → Murakumo LLM → validated ModelOp plan → drawing datoms (G2/G7)."
  [state]
  (let [ops        (_llm-plan (get state "prompt" ""))
        drawing-id (get state "drawing_id" "drawing-1")
        sourcing   (get state "sourcing" "representative")  ; G7
        datoms     (_emit-datoms drawing-id ops sourcing)]
    (merge state {"ops" ops "datoms" datoms "sourcing" sourcing})))

;; ── handle-draft — 2D drafting assistance ────────────────────────────────────
(defn handle-draft
  "Suggest dimensions / constraints / layer hygiene. Heuristic + (optional) LLM polish."
  [state]
  (let [ops         (validate-ops (get state "ops" []))
        suggestions (atom [])
        has-layer   (some #(= (get % "op") "layer") ops)]
    (when (and (not has-layer) (seq ops))
      (swap! suggestions conj {"kind" "layer"
                                "note" "geometry on default layer '0'; create named layers"}))
    (doseq [o ops]
      (cond
        (= (get o "op") "rect")
        (swap! suggestions conj {"kind"   "dimension"
                                  "target" "rect"
                                  "note"   (str "width=" (get o "w") " height=" (get o "h"))})
        (= (get o "op") "circle")
        (swap! suggestions conj {"kind"   "dimension"
                                  "target" "circle"
                                  "note"   (str "diameter=" (* 2 (get o "r")))})
        (and (= (get o "op") "polyline") (not (get o "closed")))
        (swap! suggestions conj {"kind"   "constraint"
                                  "target" "polyline"
                                  "note"   "open polyline; close for a region/extrude"})))
    (merge state {"suggestions" @suggestions})))

;; ── handle-interop — vendor script → neutral ops ─────────────────────────────
(defn handle-interop
  "Vectorworks/AutoCAD-shaped script → neutral ModelOp list (python mirror of adapters, G1)."
  [state]
  (let [flavor (get state "flavor" "")
        script (get state "script" [])
        ops    (atom [])
        layer  (atom "0")]
    (doseq [line script]
      (when (seq line)
        (let [cmd  (-> (str (first line))
                       str/upper-case
                       (str/replace #"^[._]+" ""))
              args (vec (rest line))
              n    (fn [i] (double (nth args i)))]
          (cond
            (= cmd "LAYER")
            (do (reset! layer (str (nth args 0)))
                (swap! ops conj {"op" "layer" "name" @layer}))

            (= cmd "LINE")
            (swap! ops conj {"op" "line" "layer" @layer
                              "x1" (n 0) "y1" (n 1) "x2" (n 2) "y2" (n 3)})

            (contains? #{"RECT" "RECTANG" "RECTANGLE"} cmd)
            (let [x0 (n 0) y0 (n 1) x1 (n 2) y1 (n 3)]
              (swap! ops conj {"op" "rect" "layer" @layer
                                "x" (min x0 x1) "y" (min y0 y1)
                                "w" (Math/abs (- x1 x0)) "h" (Math/abs (- y1 y0))}))

            (contains? #{"CIRCLE" "OVAL"} cmd)
            (swap! ops conj {"op" "circle" "layer" @layer
                              "cx" (n 0) "cy" (n 1) "r" (n 2)})

            (contains? #{"ARC" "ARCBYCENTER"} cmd)
            (swap! ops conj {"op" "arc" "layer" @layer
                              "cx" (n 0) "cy" (n 1) "r" (n 2)
                              "start" (n 3) "end" (n 4)})

            (contains? #{"POLY" "PLINE" "POLYLINE"} cmd)
            (let [pts (mapv (fn [i] [(double (nth args i)) (double (nth args (inc i)))])
                            (range 0 (dec (count args)) 2))]
              (swap! ops conj {"op" "polyline" "layer" @layer
                                "points" pts "closed" false}))

            (= cmd "EXTRUDE")
            (let [flat   (butlast args)
                  height (double (last args))
                  prof   (mapv (fn [i] [(double (nth flat i)) (double (nth flat (inc i)))])
                               (range 0 (dec (count flat)) 2))]
              (swap! ops conj {"op" "extrude" "layer" @layer
                                "profile" prof "height" height}))

            ;; unsupported tokens skipped (G4 honesty)
            ))))
    (merge state {"ops" (validate-ops @ops) "flavor" flavor})))

;; ── handle-export — resolve format + emit export record (G4/G5 honesty) ──────
(defn handle-export
  "Resolve target format + emit export record. No native DWG write (G5)."
  [state]
  (let [fmt      (str/lower-case (str (get state "format" "dxf")))
        fidelity (get EXPORT_FIDELITY fmt "unsupported")
        record   (cond-> {"drawingId" (get state "drawing_id" "drawing-1")
                           "format"   fmt
                           "fidelity" fidelity
                           "native"   (not= fmt "dwg")}
                   (= fmt "dwg")
                   (merge {"advisory" "DWG_PROPRIETARY"
                            "fallback" "dxf"
                            "note"     "DWG is proprietary; emit DXF and convert via external ODA/LibreDWG."})
                   (= fidelity "subset")
                   (merge {"note" (str fmt " is an honest subset export (ADR-2606033600 N6).")}))]
    (merge state {"record" record})))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "validate-ops:" (validate-ops [{"op" "rect" "x" 0 "y" 0 "w" 10 "h" 10}]))
  (println "heuristic-plan (box+circle):"
           (_heuristic-plan "make a box 10x20x30 and a circle r=5"))
  (println "handle-export dxf:"
           (get-in (handle-export {"drawing_id" "d1" "format" "dxf"}) ["record" "fidelity"])))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
