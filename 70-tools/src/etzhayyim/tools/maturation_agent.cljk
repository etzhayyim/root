(ns etzhayyim.tools.maturation-agent
  "LangGraph Autonomous Maturation Agent — Powered by Kotodama.

  Clojure port of 70-tools/langgraph_maturation_agent.py onto langgraph-clj.

  An autonomous loop that iterates the Clean Room *-compat actors and
  attempts to upgrade them from L1 (Scaffolded) to L3 (Advanced) via a
  real StateGraph:

    :research-api → :generate-schema → :generate-wasm → END

  1. Analyzing the current schema (research node).
  2. Formulating a more complex, production-like Kotoba schema
     (appended to schema/<platform>.kotoba).
  3. Updating the Py Kotodama WASM endpoints in src/main.py to handle
     advanced validation (appended L3 endpoint).

  Differences from the Python original (intentional):
    - no time.sleep / random — deterministic (the sleep only simulated
      LLM latency)
    - the actors dir is parameterized (no hardcoded \"20-actors\";
      `-main` passes \"20-actors\" to match the Python CLI behavior)."
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [langgraph.graph :as g]))

;; ─── Appended L3 artifacts (byte-for-byte the Python text) ────────────

(def l3-schema-appendix
  (str "\n    // Auto-generated L3 properties by LangGraph\n"
       "    entity AdvancedProfile {\n"
       "        id: string @unique\n"
       "        metadata: json\n"
       "    }\n"))

(def l3-endpoint-appendix
  (str "\n"
       "@app.route(\"/v2/advanced\", methods=[\"POST\"])\n"
       "def advanced_endpoint(request):\n"
       "    \"\"\"Auto-generated L3 endpoint.\"\"\"\n"
       "    return {\"status\": \"L3_UPGRADED\"}, 200\n"))

;; ─── Helpers ─────────────────────────────────────────────────────────

(defn- platform-of [actor]
  (str/replace actor "-compat" ""))

(defn get-l1-actors
  "Sorted *-compat actor dirs under actors-dir.
  (In reality, this would use evaluate_maturity logic.)"
  [actors-dir]
  (->> (.listFiles (io/file actors-dir))
       (filter #(.isDirectory ^java.io.File %))
       (map #(.getName ^java.io.File %))
       (filter #(str/ends-with? % "-compat"))
       sort
       vec))

(defn- append-if-exists!
  "Appends text to path when the file exists (the Python silently skips
  missing files — preserved)."
  [path text]
  (when (.exists (io/file path))
    (spit path text :append true)))

;; ─── Node functions ──────────────────────────────────────────────────

(defn node-research-api [state]
  (let [platform (platform-of (:current-actor state))]
    (println (str "[" (str/upper-case platform) "] Node: Researching API Docs..."))
    {:research-data (str "Found complex objects for " platform)}))

(defn node-generate-schema [state actors-dir]
  (let [actor (:current-actor state)
        platform (platform-of actor)]
    (println (str "[" (str/upper-case platform) "] Node: Generating L3 Kotoba Schema..."))
    (append-if-exists!
     (str (io/file actors-dir actor "schema" (str platform ".kotoba")))
     l3-schema-appendix)
    {}))

(defn node-generate-wasm [state actors-dir]
  (let [actor (:current-actor state)
        platform (platform-of actor)]
    (println (str "[" (str/upper-case platform) "] Node: Upgrading WASM Endpoints to L3..."))
    (append-if-exists!
     (str (io/file actors-dir actor "src" "main.py"))
     l3-endpoint-appendix)
    {}))

;; ─── Graph ───────────────────────────────────────────────────────────

(defn build-graph
  "Builds + compiles the maturation StateGraph for actors-dir."
  [actors-dir]
  (-> (g/state-graph)
      (g/add-node :research-api node-research-api)
      (g/add-node :generate-schema (fn [s] (node-generate-schema s actors-dir)))
      (g/add-node :generate-wasm (fn [s] (node-generate-wasm s actors-dir)))

      (g/set-entry-point :research-api)
      (g/add-edge :research-api :generate-schema)
      (g/add-edge :generate-schema :generate-wasm)
      (g/add-edge :generate-wasm g/END)

      (g/compile-graph {})))

(defn run-agent-loop
  "Runs the maturation agent over the first batch-size (default 5)
  *-compat actors in actors-dir. Returns the vector of final states."
  [{:keys [actors-dir batch-size] :or {batch-size 5}}]
  (let [actors (get-l1-actors actors-dir)
        graph (build-graph actors-dir)]
    (println (str "LangGraph Agent Booting. Target: " (count actors) " L1 Actors.\n"))
    (mapv (fn [actor]
            (println (str "\n--- Maturing Actor: " actor " ---"))
            (let [final (g/invoke graph {:current-actor actor} {})]
              (println (str "[" actor "] Maturation Complete. Re-classified as L3."))
              final))
          (take batch-size actors))))

(defn -main [& _args]
  (run-agent-loop {:actors-dir "20-actors" :batch-size 5}))
