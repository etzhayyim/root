;; etzhayyim.coverage — Coverage analysis pure logic (cljc port, wave 3a).
;;
;; Pure-logic port of the non-IO core of
;; 70-tools/etzhayyim-py/src/etzhayyim/coverage.py
;;
;; Ported (pure logic, no IO):
;;   required-fields / optional-fields        — actor metadata field lists
;;   check-actor-completeness                 — per-field presence map
;;   build-heal-prompt                        — LLM prompt builder for missing fields
;;   extract-json-block                       — extract first {...} JSON block from a string
;;   compute-actor-score                      — integer completeness percentage (0-100)
;;   actor-summary                            — build actor summary map from completeness
;;   oil-keywords                             — set of oil/energy domain keywords
;;   oil-match?                               — test if actor text contains an oil keyword
;;   governance-issues                        — missing governance fields list
;;   governance-ok?                           — true if no governance issues
;;
;; IO legs deferred (NOT ported):
;;   _scan_actors           — rglob("kotodama.jsonld") + JSON parse → babashka.fs/glob
;;   _call_llm_sync         — httpx POST Murakumo/Ollama → babashka.http-client
;;   _heal_one/_run_heal    — write-back to filesystem + ThreadPoolExecutor
;;   _detect_and_run_tests  — subprocess pytest/cargo/go → babashka.process
;;   All click CLI commands — wave 4+ (babashka.cli)
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.coverage :as cov])
;;   (cov/check-actor-completeness {"nanoid" "abc12345" "did" "did:web:x" "name" "foo" "performerType" "agent"})
;;   ;=> {"nanoid" true, "did" true, "name" true, "performerType" true,
;;   ;    "uiType" false, "runtimeType" false, "collections" false, "governance" false}

(ns etzhayyim.coverage
  (:require [clojure.string :as str]))

;; ── field lists (mirrors Python _REQUIRED_FIELDS / _OPTIONAL_FIELDS) ────────────

(def required-fields
  "Actor metadata fields that MUST be present."
  ["nanoid" "did" "name" "performerType"])

(def optional-fields
  "Actor metadata fields that are checked but not required."
  ["uiType" "runtimeType" "collections" "governance"])

(def all-checked-fields
  (into required-fields optional-fields))

;; ── pure completeness logic ──────────────────────────────────────────────────────

(defn check-actor-completeness
  "Returns a map of field → boolean indicating whether each field is present and non-blank.
   Mirrors Python _check_actor_completeness(data)."
  [data]
  (into {}
        (map (fn [field]
               (let [v (get data field)]
                 [field (boolean (and v (not (str/blank? (str v)))))]))
             all-checked-fields)))

(defn compute-actor-score
  "Integer completeness percentage (0-100) from a completeness map.
   Mirrors Python: int(sum(completeness.values()) / len(completeness) * 100)."
  [completeness]
  (let [n (count completeness)]
    (if (zero? n)
      0
      (int (* (/ (double (count (filter identity (vals completeness)))) n) 100)))))

(defn actor-summary
  "Build an actor summary map given raw data map and its relative path string.
   Returns a map with :nanoid :name :path :score :missing :completeness.
   Mirrors the dict built inside Python _scan_actors."
  [data path-str]
  (let [completeness (check-actor-completeness data)
        missing      (filter (fn [f]
                               (and (some #{f} required-fields)
                                    (not (get completeness f))))
                             required-fields)
        score        (compute-actor-score completeness)]
    {:nanoid      (get data "nanoid" "")
     :name        (get data "name" "")
     :path        path-str
     :score       score
     :missing     (vec missing)
     :completeness completeness}))

;; ── LLM prompt builder ───────────────────────────────────────────────────────────

(defn build-heal-prompt
  "Build the LLM metadata-fill prompt for an actor with missing fields.
   actor  = {:nanoid str :name str :path str :missing [str ...]}
   Returns a string prompt.
   Mirrors Python _build_heal_prompt(actor)."
  [{:keys [nanoid name path missing]}]
  (let [ctx        (str "nanoid=" (pr-str (or nanoid ""))
                        ", name=" (pr-str (or name ""))
                        ", path=" (pr-str (or path "")))
        field-list (str/join ", " (map #(str "\"" % "\"") (or missing [])))]
    (str "You are a metadata filler for AI actor manifests on the etzhayyim.com platform.\n"
         "Actor context: " ctx "\n"
         "Missing fields: " field-list "\n\n"
         "Generate appropriate values for the missing fields based on the actor's name and path.\n"
         "Output ONLY a valid JSON object with exactly these keys: " field-list "\n"
         "Infer values from the actor name/path. For 'performerType' use one of: actor, agent, worker, service.\n"
         "For 'did' generate a placeholder like did:plc:unknown-{nanoid}.\n"
         "Output only JSON:")))

;; ── JSON-block extractor ─────────────────────────────────────────────────────────

(defn extract-json-block
  "Extract the first {...} block from a raw LLM response string.
   Returns the matched substring or nil.
   Mirrors Python _RE_JSON_BLOCK.search(raw)."
  [raw]
  (when (string? raw)
    (let [start (.indexOf raw "{")]
      (when (>= start 0)
        (loop [i    (inc start)
               depth 1
               in-str false
               escape false]
          (cond
            (>= i (count raw))          nil
            (and in-str escape)         (recur (inc i) depth true false)
            (and in-str (= (get raw i) \\)) (recur (inc i) depth true true)
            (and in-str (= (get raw i) \"))  (recur (inc i) depth false false)
            in-str                      (recur (inc i) depth true false)
            (= (get raw i) \")          (recur (inc i) depth true false)
            (= (get raw i) \{)          (recur (inc i) (inc depth) false false)
            (= (get raw i) \})
            (let [d (dec depth)]
              (if (zero? d)
                (.substring raw start (inc i))
                (recur (inc i) d false false)))
            :else                       (recur (inc i) depth false false)))))))

;; ── oil/energy keyword matching ──────────────────────────────────────────────────

(def oil-keywords
  "Domain keywords indicating an oil/energy actor.
   Mirrors Python _OIL_KEYWORDS."
  #{"oil" "energy" "crude" "barrel" "naphtha" "petroleum" "lng" "refinery"})

(defn oil-match?
  "Returns true if the combined name+description text contains any oil keyword (case-insensitive).
   data = actor JSON map (keys 'name', 'description').
   Mirrors Python: any(k in name for k in _OIL_KEYWORDS)."
  [data]
  (let [text (str/lower-case (str (get data "name" "") (get data "description" "")))]
    (boolean (some #(str/includes? text %) oil-keywords))))

;; ── governance completeness ───────────────────────────────────────────────────────

(def governance-fields
  "Actor fields checked for governance coverage."
  ["operator" "authority" "visibility"])

(defn governance-issues
  "Returns a vector of governance field names that are missing or blank.
   Mirrors Python: issues = [fld for fld in ['operator','authority','visibility'] if not data.get(fld)]."
  [data]
  (filterv (fn [fld]
             (let [v (get data fld)]
               (or (nil? v) (str/blank? (str v)))))
           governance-fields))

(defn governance-ok?
  "Returns true when all governance fields are present."
  [data]
  (empty? (governance-issues data)))
