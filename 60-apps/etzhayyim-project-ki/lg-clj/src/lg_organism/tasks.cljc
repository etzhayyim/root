(ns lg-organism.tasks
  "Organism worker tasks — clj port of the `kotodama.*_worker_main` handlers
  dispatched by `lg/lg_organism/server.py` (ADR-2606280030).

  22 tasks across 7 organism workers:
    hakkou (3) : createFermentRecord, llmTransform, finalizeFerment
    kabi   (1) : anastomosisProbe
    ki     (4) : absorb, synthesize, bloom, ring
    kinoko (1) : checkFlowThreshold
    kobo   (3) : budAgent, sporulate, germinate
    koke   (5) : scanRawSignals, fixSignal, classifyFixation, handoffToHakkou,
                 handoffToSaikin
    saikin (5) : probeEnvironment, transferSignal, formColony, lyse, handoffToKi

  DEVIATION (boundary): the real `kotodama.*` worker bodies are a NATIVE +
  RisingWave/psycopg boundary that is forbidden in this substrate (CLAUDE.md:
  RisingWave is off-limits; persistence must target the kotoba Datom log). Each
  task here is therefore an INJECTABLE seam (the actor swap pattern): a
  deterministic, side-effect-free stub default that preserves the request/echo
  contract so the 23-graph dispatcher is fully verifiable under bb. Production
  swaps each entry of `*task-handlers*` for a kotoba-Datom-log-backed impl; the
  `hakkou.llmTransform` default already routes through the Murakumo loopback
  seam (`lg-organism.llm/*llm-chat*`)."
  (:require [clojure.string :as str]
            [lg-organism.llm :as llm]))

(defn- worker-echo
  "Deterministic stub: echo the worker/task NSID segment + received input. This
  keeps the graph output JSON-serializable and the dispatch path testable while
  the real kotoba-Datom-log-backed worker is swapped in at deploy time."
  [worker task input]
  {:status "stub-ok"
   :worker worker
   :task   task
   :input  (or input {})})

;; ── hakkou (発酵) ────────────────────────────────────────────────────────────
(defn task-create-ferment-record [in] (worker-echo "hakkou" "createFermentRecord" in))

(defn task-llm-transform
  "The one task with a real LLM edge: routes through the Murakumo loopback seam.
  `:system` / `:prompt` (or `:input`) come from the request map."
  [in]
  (let [system (or (:system in) "You are the hakkou fermentation transform worker.")
        user   (str (or (:prompt in) (:input in) (:text in) ""))
        res    (llm/*llm-chat* system user)]
    (if (map? res)
      (worker-echo "hakkou" "llmTransform" (assoc in :llm res))
      {:status "ok" :worker "hakkou" :task "llmTransform" :output res})))

(defn task-finalize-ferment [in] (worker-echo "hakkou" "finalizeFerment" in))

;; ── kabi (黴) ────────────────────────────────────────────────────────────────
(defn task-anastomosis-probe [in] (worker-echo "kabi" "anastomosisProbe" in))

;; ── ki (基/気) ───────────────────────────────────────────────────────────────
(defn task-absorb     [in] (worker-echo "ki" "absorb" in))
(defn task-synthesize [in] (worker-echo "ki" "synthesize" in))
(defn task-bloom      [in] (worker-echo "ki" "bloom" in))
(defn task-ring       [in] (worker-echo "ki" "ring" in))

;; ── kinoko (茸) ──────────────────────────────────────────────────────────────
(defn task-check-flow-threshold [in] (worker-echo "kinoko" "checkFlowThreshold" in))

;; ── kobo (酵母) ──────────────────────────────────────────────────────────────
(defn task-bud-agent  [in] (worker-echo "kobo" "budAgent" in))
(defn task-sporulate  [in] (worker-echo "kobo" "sporulate" in))
(defn task-germinate  [in] (worker-echo "kobo" "germinate" in))

;; ── koke (苔) ────────────────────────────────────────────────────────────────
(defn task-scan-raw-signals   [in] (worker-echo "koke" "scanRawSignals" in))
(defn task-fix-signal         [in] (worker-echo "koke" "fixSignal" in))
(defn task-classify-fixation  [in] (worker-echo "koke" "classifyFixation" in))
(defn task-handoff-to-hakkou  [in] (worker-echo "koke" "handoffToHakkou" in))
(defn task-handoff-to-saikin  [in] (worker-echo "koke" "handoffToSaikin" in))

;; ── saikin (細菌) ────────────────────────────────────────────────────────────
(defn task-probe-environment [in] (worker-echo "saikin" "probeEnvironment" in))
(defn task-transfer-signal   [in] (worker-echo "saikin" "transferSignal" in))
(defn task-form-colony       [in] (worker-echo "saikin" "formColony" in))
(defn task-lyse              [in] (worker-echo "saikin" "lyse" in))
(defn task-handoff-to-ki     [in] (worker-echo "saikin" "handoffToKi" in))

;; ── NSID → handler registry (parity with server.py TASKS) ───────────────────
;; Keys are the canonical XRPC NSIDs; the last segment is the graph/assistant id.
(def ^:dynamic *task-handlers*
  "Injectable NSID→handler map (the actor swap seam). Deployers rebind entries
  to kotoba-Datom-log-backed impls; tests rebind to assertion stubs."
  {;; hakkou
   "com.etzhayyim.hakkou.createFermentRecord"      task-create-ferment-record
   "com.etzhayyim.hakkou.llmTransform"             task-llm-transform
   "com.etzhayyim.hakkou.finalizeFerment"          task-finalize-ferment
   ;; kabi
   "com.etzhayyim.apps.kabi.anastomosisProbe"      task-anastomosis-probe
   ;; ki
   "com.etzhayyim.ki.absorb"                       task-absorb
   "com.etzhayyim.ki.synthesize"                   task-synthesize
   "com.etzhayyim.ki.bloom"                        task-bloom
   "com.etzhayyim.ki.ring"                         task-ring
   ;; kinoko
   "com.etzhayyim.apps.kinoko.checkFlowThreshold"  task-check-flow-threshold
   ;; kobo
   "com.etzhayyim.apps.kobo.budAgent"              task-bud-agent
   "com.etzhayyim.apps.kobo.sporulate"             task-sporulate
   "com.etzhayyim.apps.kobo.germinate"             task-germinate
   ;; koke
   "com.etzhayyim.koke.scanRawSignals"             task-scan-raw-signals
   "com.etzhayyim.koke.fixSignal"                  task-fix-signal
   "com.etzhayyim.koke.classifyFixation"           task-classify-fixation
   "com.etzhayyim.koke.handoffToHakkou"            task-handoff-to-hakkou
   "com.etzhayyim.koke.handoffToSaikin"            task-handoff-to-saikin
   ;; saikin
   "com.etzhayyim.apps.saikin.probeEnvironment"    task-probe-environment
   "com.etzhayyim.apps.saikin.transferSignal"      task-transfer-signal
   "com.etzhayyim.apps.saikin.formColony"          task-form-colony
   "com.etzhayyim.apps.saikin.lyse"                task-lyse
   "com.etzhayyim.apps.saikin.handoffToKi"         task-handoff-to-ki})

(defn nsid->assistant
  "NSID → graph/assistant id = the last dotted segment (parity with the Python
  `nsid.rsplit('.', 1)[-1]`)."
  [nsid]
  (last (str/split (str nsid) #"\.")))
