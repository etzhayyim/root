;; etzhayyim.training — ML training job management XRPC client (cljc port).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/training.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-auth-headers           — "Bearer <tok>" + Content-Type header
;;     build-list-request           — GET /xrpc/com.etzhayyim.training.listJobs
;;     build-get-request            — GET /xrpc/com.etzhayyim.training.getJob
;;     build-start-request          — POST /xrpc/com.etzhayyim.training.startJob
;;     build-cancel-request         — POST /xrpc/com.etzhayyim.training.cancelJob
;;     build-run-request            — POST /xrpc/com.etzhayyim.apps.training.run{Sft,Lora,Distill}
;;     build-promote-request        — POST /xrpc/com.etzhayyim.apps.training.promote
;;     build-eval-request           — POST /xrpc/com.etzhayyim.apps.training.runEval
;;     build-list-runs-request      — POST /xrpc/com.etzhayyim.apps.training.listRuns
;;     build-list-checkpoints-request — POST /xrpc/com.etzhayyim.apps.training.listCheckpoints
;;     build-list-snapshots-request — POST /xrpc/com.etzhayyim.apps.training.listSnapshots
;;     build-coverage-request       — POST /xrpc/com.etzhayyim.apps.training.coverage
;;     build-serving-request        — POST /xrpc/com.etzhayyim.apps.training.serving
;;     training-nsid                — map kind → NSID string
;;     validate-run-opts!           — throw ex-info on missing required options
;;     parse-bench-list             — split comma-separated bench string
;;
;;   IO (HTTP-shaping verified via injectable :http-fn, no live calls):
;;     xrpc-get    — GET {pds}/xrpc/{nsid} with params
;;     xrpc-post   — POST {pds}/xrpc/{nsid} with JSON body
;;
;; INJECTABLE HTTP CLIENT:
;;   xrpc-get / xrpc-post accept an optional :http-fn in opts.
;;
;; SECURITY:
;;   No secrets at load time.  accessJwt read lazily from auth data.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.training)(println :ok)"

(ns etzhayyim.training
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def training-nsid
  "Map from kind keyword/string → XRPC NSID string."
  {"sft"     "com.etzhayyim.apps.training.runSft"
   "lora"    "com.etzhayyim.apps.training.runLora"
   "distill" "com.etzhayyim.apps.training.runDistill"})

;; ---------------------------------------------------------------------------
;; Pure: header + validation helpers
;; ---------------------------------------------------------------------------

(defn build-auth-headers
  "Build Authorization + Content-Type headers from an access token.
  Pure: accepts token directly."
  [token]
  {"Authorization" (str "Bearer " token)
   "Content-Type"  "application/json"})

(defn parse-bench-list
  "Split a comma-separated bench string into a trimmed vector.
  Mirrors [b.strip() for b in bench.split(',') if b.strip()]."
  [bench-str]
  (vec (filter seq (map str/trim (str/split (or bench-str "") #",")))))

(defn validate-run-opts!
  "Throw ex-info if required run options are missing.
  Mirrors the click.ClickException raises in training_run."
  [{:keys [kind dataset base-model student-base teacher-kind]}]
  (when (not (seq dataset))
    (throw (ex-info "--dataset is required" {:field :dataset})))
  (when (and (#{"sft" "lora"} kind) (not (seq base-model)))
    (throw (ex-info (str "--base is required for kind=" kind) {:field :base-model})))
  (when (and (= kind "distill") (not (seq student-base)))
    (throw (ex-info "--student-base is required for kind=distill" {:field :student-base})))
  (when (and (= kind "distill") (not (seq teacher-kind)))
    (throw (ex-info "--teacher-kind is required for kind=distill (run | actor | artifact)"
                    {:field :teacher-kind}))))

;; ---------------------------------------------------------------------------
;; Pure: request builders
;; ---------------------------------------------------------------------------

(defn build-list-request
  "Build GET listJobs request map. filter-status optional."
  [{:keys [pds-url filter-status]}]
  (let [base (str (str/replace pds-url #"/$" "")
                  "/xrpc/com.etzhayyim.training.listJobs")]
    {:method :get
     :url    base
     :params (cond-> {} (seq filter-status) (assoc "status" filter-status))}))

(defn build-get-request
  "Build GET getJob request map."
  [{:keys [pds-url job-id]}]
  {:method :get
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.training.getJob")
   :params {"id" job-id}})

(defn build-start-request
  "Build POST startJob request map."
  [{:keys [pds-url job-type model dataset]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.training.startJob")
   :body   {"type" job-type "model" model "dataset" dataset}})

(defn build-cancel-request
  "Build POST cancelJob request map."
  [{:keys [pds-url job-id]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.training.cancelJob")
   :body   {"id" job-id}})

(defn build-run-request
  "Build POST run{Sft,Lora,Distill} request map.
  Mirrors the payload assembly in training_run."
  [{:keys [pds-url kind dataset run-id label gpu-target seed
           rationale eval-benches hyperparams base-model student-base
           teacher-kind teacher-run-id teacher-actor distill-method]}]
  (let [nsid    (get training-nsid kind)
        _       (when (nil? nsid)
                  (throw (ex-info (str "Unknown training kind: " kind) {:kind kind})))
        benches (parse-bench-list (or eval-benches "internal-loss"))
        payload (cond-> {"datasetName" dataset}
                  (seq run-id)       (assoc "runId"         run-id)
                  (seq label)        (assoc "datasetLabel"  label)
                  (seq gpu-target)   (assoc "gpuTarget"     gpu-target)
                  (and seed (pos? seed)) (assoc "seed"      seed)
                  (seq rationale)    (assoc "rationale"     rationale)
                  (seq benches)      (assoc "evalBenches"   benches)
                  hyperparams        (assoc "hyperparams"   hyperparams)
                  (#{"sft" "lora"} kind) (assoc "baseModel" base-model)
                  (= kind "distill") (assoc "studentBaseModel" student-base
                                           "teacherKind"       teacher-kind
                                           "distillMethod"     (or distill-method "soft-logits"))
                  (and (= kind "distill") (seq teacher-run-id))
                  (assoc "teacherRunId" teacher-run-id)
                  (and (= kind "distill") (seq teacher-actor))
                  (assoc "teacherActor" teacher-actor))]
    {:method :post
     :url    (str (str/replace pds-url #"/$" "") "/xrpc/" nsid)
     :body   payload}))

(defn build-promote-request
  "Build POST promote request map."
  [{:keys [pds-url checkpoint-id alias target by rationale]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.apps.training.promote")
   :body   (cond-> {"checkpointId" checkpoint-id "alias" alias}
             (seq target)   (assoc "servingTarget" target)
             (seq by)       (assoc "promotedBy"    by)
             (seq rationale) (assoc "rationale"    rationale))})

(defn build-eval-request
  "Build POST runEval request map."
  [{:keys [pds-url checkpoint-id bench eval-dataset eval-revision limit gpu]}]
  (let [benches (parse-bench-list (or bench "internal-loss"))]
    (when (empty? benches)
      (throw (ex-info "--bench must list at least one bench name" {:bench bench})))
    {:method :post
     :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.apps.training.runEval")
     :body   (cond-> {"checkpointId" checkpoint-id "benches" benches}
               (seq eval-dataset)  (assoc "evalDatasetName"     eval-dataset)
               (seq eval-revision) (assoc "evalDatasetRevision" eval-revision)
               (and limit (pos? limit)) (assoc "sampleLimit"    limit)
               (seq gpu)           (assoc "gpuTarget"           gpu))}))

(defn build-list-runs-request
  "Build POST listRuns request map."
  [{:keys [pds-url kind filter-status limit]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.apps.training.listRuns")
   :body   (cond-> {"limit" (or limit 50)}
             (seq kind)          (assoc "kind"   kind)
             (seq filter-status) (assoc "status" filter-status))})

(defn build-list-checkpoints-request
  "Build POST listCheckpoints request map."
  [{:keys [pds-url run only-final limit]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.apps.training.listCheckpoints")
   :body   (cond-> {"limit" (or limit 50) "onlyFinal" (boolean only-final)}
             (seq run) (assoc "runId" run))})

(defn build-list-snapshots-request
  "Build POST listSnapshots request map."
  [{:keys [pds-url dataset filter-status limit]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.apps.training.listSnapshots")
   :body   (cond-> {"limit" (or limit 50)}
             (seq dataset)       (assoc "datasetName" dataset)
             (seq filter-status) (assoc "status"      filter-status))})

(defn build-coverage-request
  "Build POST coverage request map."
  [{:keys [pds-url]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.apps.training.coverage")
   :body   {}})

(defn build-serving-request
  "Build POST serving request map."
  [{:keys [pds-url alias]}]
  {:method :post
   :url    (str (str/replace pds-url #"/$" "") "/xrpc/com.etzhayyim.apps.training.serving")
   :body   (cond-> {} (seq alias) (assoc "alias" alias))})

;; ---------------------------------------------------------------------------
;; IO: XRPC dispatch
;; ---------------------------------------------------------------------------

(defn xrpc-get
  "GET {url} with params and auth headers.
  opts:
    :token   — access JWT (required)
    :http-fn — injectable: (fn [url headers params] → {:status :body})
    :dry-run — return the request shape without calling"
  [{:keys [url params]} opts]
  (let [headers (build-auth-headers (:token opts))
        http-fn (or (:http-fn opts)
                    #?(:bb (fn [u h p]
                             (http/get u {:headers h :query-params p}))
                       :default nil))]
    (when (not http-fn)
      (throw (ex-info "http-fn required" {})))
    (if (:dry-run opts)
      {:dry-run true :url url :headers headers :params params}
      (let [resp (http-fn url headers (or params {}))
            body (json/parse-string (:body resp))]
        body))))

(defn xrpc-post
  "POST {url} with JSON body and auth headers.
  opts:
    :token   — access JWT (required)
    :http-fn — injectable: (fn [url headers body-map] → {:status :body})
    :dry-run — return the request shape without calling"
  [{:keys [url body]} opts]
  (let [headers (build-auth-headers (:token opts))
        http-fn (or (:http-fn opts)
                    #?(:bb (fn [u h b]
                             (http/post u {:headers h :body (json/generate-string b)}))
                       :default nil))]
    (when (not http-fn)
      (throw (ex-info "http-fn required" {})))
    (if (:dry-run opts)
      {:dry-run true :url url :headers headers :body body}
      (let [resp (http-fn url headers (or body {}))
            data (json/parse-string (:body resp))]
        data))))

;; ---------------------------------------------------------------------------
;; CLI entrypoint — mirrors the `training` click group (JVM/bb only).
;;
;; SIDE-EFFECTING actor: `run`/`start`/`promote`/`eval`/`cancel` launch real
;; training jobs over XRPC.  -main DEFAULTS TO A DRY-RUN PLAN (prints the
;; request map the python CLI would POST/GET, never sends it).  The live leg
;; would require an access token + reachable PDS; verification never sends.
;; ---------------------------------------------------------------------------

#?(:clj
   (do
     (defn- t-parse
       "Tiny argv parser. bool-flags = set of flags taking no value.
        Returns [flags-map positionals]."
       [args bool-flags]
       (loop [a (seq args) flags {} pos []]
         (if (empty? a)
           [flags pos]
           (let [tok (first a)]
             (cond
               (contains? bool-flags tok) (recur (rest a) (assoc flags tok true) pos)
               (str/starts-with? tok "--") (recur (drop 2 a) (assoc flags tok (second a)) pos)
               :else (recur (rest a) flags (conj pos tok)))))))

     (defn- t-pds [flags] (or (get flags "--pds") "https://pds.local"))

     (defn- t-emit [req flags]
       (if (get flags "--json")
         (println (json/generate-string req {:pretty true}))
         (do
           (println "PLAN (dry-run — not sent):")
           (println (str (clojure.string/upper-case (name (:method req))) " " (:url req)))
           (when (:params req) (println "  params:" (json/generate-string (:params req))))
           (when (:body req)   (println "  body:  " (json/generate-string (:body req)))))))

     (defn- t-usage []
       (println "usage: training <subcommand> [options]")
       (println "subcommands: list get run start cancel promote eval")
       (println "             list-runs list-checkpoints list-snapshots coverage serving")
       (println "side-effecting (run/start/promote/eval/cancel): default = dry-run plan"))

     (defn -main [& args]
       (let [bool-flags #{"--json" "--only-final"}
             [sub & rst] args
             [flags pos] (t-parse rst bool-flags)
             pds (t-pds flags)]
         (case sub
           nil    (t-usage)
           "list" (t-emit (build-list-request {:pds-url pds :filter-status (get flags "--status")}) flags)
           "get"  (t-emit (build-get-request {:pds-url pds :job-id (first pos)}) flags)
           "start" (t-emit (build-start-request {:pds-url pds
                                                 :job-type (or (get flags "--type") "lora")
                                                 :model (or (get flags "--model") "")
                                                 :dataset (or (get flags "--dataset") "")}) flags)
           "cancel" (t-emit (build-cancel-request {:pds-url pds :job-id (first pos)}) flags)
           "run"  (try
                    (let [m {:pds-url pds
                             :kind (or (get flags "--kind") "sft")
                             :dataset (or (get flags "--dataset") "")
                             :base-model (or (get flags "--base") "")
                             :student-base (or (get flags "--student-base") "")
                             :label (get flags "--label")
                             :run-id (get flags "--run-id")
                             :gpu-target (get flags "--gpu")
                             :seed (some-> (get flags "--seed") parse-long)
                             :rationale (get flags "--rationale")
                             :eval-benches (or (get flags "--eval-benches") "internal-loss")
                             :hyperparams (some-> (get flags "--hyperparams") (json/parse-string))
                             :teacher-kind (get flags "--teacher-kind")
                             :teacher-run-id (get flags "--teacher-run-id")
                             :teacher-actor (get flags "--teacher-actor")
                             :distill-method (or (get flags "--distill-method") "soft-logits")}]
                      (validate-run-opts! m)
                      (t-emit (build-run-request m) flags))
                    (catch clojure.lang.ExceptionInfo e
                      (println "error:" (ex-message e))))
           "promote" (t-emit (build-promote-request {:pds-url pds :checkpoint-id (first pos)
                                                     :alias (get flags "--alias")
                                                     :target (get flags "--target")
                                                     :by (get flags "--by")
                                                     :rationale (get flags "--rationale")}) flags)
           "eval" (try
                    (t-emit (build-eval-request {:pds-url pds :checkpoint-id (first pos)
                                                 :bench (or (get flags "--bench") "internal-loss")
                                                 :eval-dataset (get flags "--eval-dataset")
                                                 :eval-revision (get flags "--eval-revision")
                                                 :limit (some-> (get flags "--limit") parse-long)
                                                 :gpu (get flags "--gpu")}) flags)
                    (catch clojure.lang.ExceptionInfo e (println "error:" (ex-message e))))
           "list-runs" (t-emit (build-list-runs-request {:pds-url pds :kind (get flags "--kind")
                                                         :filter-status (get flags "--status")
                                                         :limit (or (some-> (get flags "--limit") parse-long) 50)}) flags)
           "list-checkpoints" (t-emit (build-list-checkpoints-request {:pds-url pds :run (get flags "--run")
                                                                       :only-final (get flags "--only-final")
                                                                       :limit (or (some-> (get flags "--limit") parse-long) 50)}) flags)
           "list-snapshots" (t-emit (build-list-snapshots-request {:pds-url pds :dataset (get flags "--dataset")
                                                                   :filter-status (get flags "--status")
                                                                   :limit (or (some-> (get flags "--limit") parse-long) 50)}) flags)
           "coverage" (t-emit (build-coverage-request {:pds-url pds}) flags)
           "serving" (t-emit (build-serving-request {:pds-url pds :alias (get flags "--alias")}) flags)
           (do (println "unknown subcommand:" sub) (t-usage)))))))
