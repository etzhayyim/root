#!/usr/bin/env bb
;; Working Clojure port of methods/bpmn.py.
(ns kabuto.methods.bpmn
  "kabuto 兜 — per-company BPMN 2.0 process-model emitter (ADR-2606022000).

  Emits GENERIC, well-formed BPMN 2.0 XML workflow templates per company (a procurement template
  + a disclosure template), anchors each as a content hash (kotoba-CID stand-in), and writes the
  queryable :company.process/* datoms (with the bpmn-cid) back into the Datom log. HONEST (G5):
  these are :synthesized GENERIC templates — a plausible public procurement/disclosure workflow,
  NOT a company's actual internal process. The XML validates against the OMG BPMN 2.0 namespace
  (renders in bpmn-js).

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/bpmn.clj [seed.edn] [--out OUTDIR]"
  (:require [kabuto.methods.kabuto-edn :as e]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))
(def bpmn-ns "http://www.omg.org/spec/BPMN/20100524/MODEL")

(def templates
  {:procurement ["Supplier procurement"
                 ["Identify supply need" "Issue RFQ to qualified suppliers"
                  "Evaluate bids (cost / capacity / ESG)" "Award & onboard supplier"
                  "Place purchase order" "Receive & inspect goods"]]
   :disclosure ["Supply-chain disclosure"
                ["Collect supplier list" "Run human-rights / ESG due diligence"
                 "Aggregate findings (aggregate-first)" "Publish public disclosure report"]]})

(defn- xml-escape [s]
  (-> (str s) (str/replace "&" "&amp;") (str/replace "<" "&lt;")
      (str/replace ">" "&gt;") (str/replace "\"" "&quot;")))

(defn build-bpmn
  "Return well-formed BPMN 2.0 XML: start → tasks (sequence) → end, with a deterministic
  left-to-right BPMNDI layout (byte-identical to bpmn.py)."
  [process-id name company-name tasks]
  (let [start (str process-id "_start")
        end (str process-id "_end")
        task-ids (mapv #(str process-id "_t" %) (range (count tasks)))
        seq* (vec (concat [start] task-ids [end]))
        kinds (vec (concat ["event"] (repeat (count tasks) "task") ["event"]))
        cy 120 gap 60
        geom (loop [g {} x 160 i 0]
               (if (>= i (count seq*))
                 g
                 (let [kind (kinds i)
                       w (if (= kind "task") 100 36)
                       h (if (= kind "task") 80 36)]
                   (recur (assoc g (seq* i) [x (- cy (quot h 2)) w h]) (+ x w gap) (inc i)))))
        nodes (concat [(str "      <startEvent id=\"" start "\" name=\"Start\"/>")]
                      (map (fn [tid label] (str "      <task id=\"" tid "\" name=\"" (xml-escape label) "\"/>"))
                           task-ids tasks)
                      [(str "      <endEvent id=\"" end "\" name=\"Done\"/>")])
        flow-pairs (for [i (range (dec (count seq*)))]
                     [(str process-id "_f" i) (seq* i) (seq* (inc i))])
        flows (map (fn [[fid s t]] (str "      <sequenceFlow id=\"" fid "\" sourceRef=\"" s "\" targetRef=\"" t "\"/>"))
                   flow-pairs)
        di (concat
            [(str "    <bpmndi:BPMNPlane id=\"plane_" process-id "\" bpmnElement=\"" process-id "\">")]
            (map (fn [nid] (let [[gx gy gw gh] (geom nid)]
                             (str "      <bpmndi:BPMNShape id=\"" nid "_di\" bpmnElement=\"" nid "\">"
                                  "<omgdc:Bounds x=\"" gx "\" y=\"" gy "\" width=\"" gw "\" height=\"" gh "\"/>"
                                  "</bpmndi:BPMNShape>"))) seq*)
            (map (fn [[fid s t]]
                   (let [[sx sy sw sh] (geom s) [tx ty tw th] (geom t)]
                     (str "      <bpmndi:BPMNEdge id=\"" fid "_di\" bpmnElement=\"" fid "\">"
                          "<omgdi:waypoint x=\"" (+ sx sw) "\" y=\"" (+ sy (quot sh 2)) "\"/>"
                          "<omgdi:waypoint x=\"" tx "\" y=\"" (+ ty (quot th 2)) "\"/>"
                          "</bpmndi:BPMNEdge>"))) flow-pairs)
            ["    </bpmndi:BPMNPlane>"])]
    (str "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
         "<definitions xmlns=\"" bpmn-ns "\" "
         "xmlns:bpmndi=\"http://www.omg.org/spec/BPMN/20100524/DI\" "
         "xmlns:omgdc=\"http://www.omg.org/spec/DD/20100524/DC\" "
         "xmlns:omgdi=\"http://www.omg.org/spec/DD/20100524/DI\" "
         "targetNamespace=\"https://etzhayyim.com/ns/kabuto/bpmn\" "
         "id=\"def_" process-id "\">\n"
         "  <!-- kabuto 兜 generic :synthesized template for " (xml-escape company-name)
         " (ADR-2606022000). NOT the company's actual internal process. -->\n"
         "  <process id=\"" process-id "\" name=\"" (xml-escape name) " — " (xml-escape company-name)
         "\" isExecutable=\"false\">\n"
         (str/join "\n" nodes) "\n"
         (str/join "\n" flows) "\n"
         "  </process>\n"
         "  <bpmndi:BPMNDiagram id=\"di_" process-id "\">\n"
         (str/join "\n" di) "\n"
         "  </bpmndi:BPMNDiagram>\n"
         "</definitions>\n")))

(defn content-cid
  "Deterministic content hash standing in for a kotoba-CID at R0."
  [data]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")
        hx (apply str (map #(format "%02x" (bit-and % 0xff)) (.digest md (.getBytes (str data) "UTF-8"))))]
    (str "cid.sha256:" (subs hx 0 32))))

(defn- es [s] (str "\"" (str/replace (str/replace (str s) "\\" "\\\\") "\"" "\\\"") "\""))

(defn main [& argv]
  (let [args (vec argv)
        out-idx (.indexOf args "--out")
        out-val (when (>= out-idx 0) (nth args (inc out-idx)))
        outdir (if out-val (io/file out-val) (io/file (actor-root) "out"))
        seed (or (first (remove #(or (str/starts-with? % "--") (= % out-val)) args))
                 (str (io/file (actor-root) "data" "seed-public-companies.kotoba.edn")))
        g (e/classify (e/load-edn seed))
        companies (:companies g)
        bpmndir (io/file outdir "bpmn")
        want (sort (distinct (concat (map (fn [p] [(:company.process/company p)
                                                   (or (:company.process/kind p) :procurement)]) (:processes g))
                                     (map (fn [cid] [cid :procurement]) (keys companies)))))
        emitted (atom [])]
    (.mkdirs bpmndir)
    (doseq [[cid kind] want]
      (let [[name tasks] (get templates kind (get templates :procurement))
            cname (get-in companies [cid :company/name] cid)
            slug (-> (str cid) (str/replace "org.corp." "") (str/replace "." "_"))
            proc-id (str "proc_" slug "_" (str/replace (str kind) #"^:" ""))
            xml (build-bpmn proc-id name cname tasks)]
        (spit (io/file bpmndir (str slug "." (str/replace (str kind) #"^:" "") ".bpmn")) xml)
        (swap! emitted conj [(str "proc." cid "." (str/replace (str kind) #"^:" "")) cid name kind (content-cid xml)])))
    (spit (io/file outdir "processes.kotoba.edn")
          (str/join "\n"
                    (concat
                     [";; kabuto — BPMN process datoms with computed content CIDs (ADR-2606022000)."
                      ";; :synthesized generic templates (G5); bpmn XML under out/bpmn/. NOT actual processes." "["]
                     (map (fn [[pid cid name kind cidh]]
                            (format " {:company.process/id %s :company.process/company %s :company.process/name %s :company.process/kind %s :company.process/bpmn-cid %s :company.process/sourcing :synthesized}"
                                    (es pid) (es cid) (es name) kind (es cidh))) @emitted)
                     ["]" ""])))
    (println (format "kabuto.bpmn: wrote %d BPMN files + processes.kotoba.edn" (count @emitted)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
