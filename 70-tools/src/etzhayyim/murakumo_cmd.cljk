;; etzhayyim.murakumo-cmd — Murakumo LLM fleet management CLI port
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/murakumo_cmd.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-status-request         — shape the GET /murakumo.getStatus request
;;     build-list-request           — shape the GET /murakumo.listPods request
;;     build-route-request          — shape the GET /murakumo.getRouting request
;;     build-infer-request          — shape the POST /murakumo.infer request
;;     build-xrpc-request           — shape a generic POST XRPC request
;;     build-train-experts-request  — shape POST /murakumo.trainExperts
;;     build-fleet-jotai-request    — shape GET /murakumo.fleetStatus
;;     build-fleet-versions-request — shape GET /murakumo.workerVersions
;;     build-git-root-command       — argv to find git root
;;     build-eval-command           — argv for eval_v6_bench.py subprocess
;;     build-ssh-command            — argv for an SSH call to a mini
;;     build-nomad-command          — argv for a nomad CLI call
;;     build-scp-command            — argv for scp deploy
;;     parse-fleet-models           — parse fleet-models.json data (pure)
;;     resolve-install-cmd          — compute install shell command string (pure)
;;     probe-cmd-for-model          — build the probe shell command for a model
;;     parse-nodes-json             — parse nomad node JSON output (pure)
;;     resolve-node-id              — find Nomad node ID in parsed nodes list
;;     resolve-alloc-id             — find Nomad alloc ID in parsed allocs list
;;     pipeline-steps               — the canonical pipeline steps list (data)
;;
;;   IO (subprocess/HTTP via injectable fns, no live calls in tests):
;;     call-xrpc-get                — GET an XRPC endpoint via :http-fn
;;     call-xrpc-post               — POST an XRPC endpoint via :http-fn
;;     run-git-root                 — find git root via :proc-fn
;;     run-ssh-on-mini              — SSH into a mini via :proc-fn
;;     run-nomad                    — invoke nomad CLI via :proc-fn
;;     probe-model-on-mini          — check model presence via :proc-fn
;;
;; INJECTABLE PROCESS FN:
;;   Every IO fn that shells out accepts :proc-fn in opts.
;;   No default authority: callers inject a process capability. Tests inject a
;;   fake that records argv without executing.
;;
;; INJECTABLE HTTP FN:
;;   HTTP legs require an explicit :http-fn capability.
;;
;; SECURITY / SECRETS:
;;   Environment is explicit data supplied by a host. No token, process environment,
;;   HF_TOKEN or MURAKUMO_FLEET_SSH_PASS is acquired by portable code.
;;
;; SUBCOMMAND COVERAGE (Wave 7B honest partial):
;;   PORTED (argv shape + HTTP shape fully testable offline):
;;     status / list / route / infer / xrpc
;;     models declare / models apply (install cmd shape)
;;     fleet jotai / fleet versions / fleet nodes / fleet drain / fleet undrain
;;     fleet restart / fleet logs / fleet deploy (dry-run path)
;;     eval (bench command shape)
;;     graph-extract / graph-ingest / coverage-export (command shapes)
;;     train-experts (XRPC shape)
;;     plan (pure data)
;;     kubelet-deploy (dry-run path)
;;   DEFERRED (low-priority, complex runtime-only paths):
;;     fleet watch (continuous poll loop — no pure-shape testing surface)
;;     models list (concurrent probe fan-out, SSH-bound, no offline surface)
;;     fleet-plan + optimize (complex multi-path scripts, XRPC-only legs done)
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.murakumo-cmd)(println :ok)"

(ns etzhayyim.murakumo-cmd
  (:require [clojure.string :as str]
            [cheshire.core  :as json]))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

;; No default-nomad-addr on purpose — see resolve-nomad-addr.
(def ^:private daemon-deploy-path "/usr/local/share/murakumo/daemon.py")
(def ^:private murakumo-training-dir "60-apps/etzhayyim-project-murakumo/training")

;; The canonical Hayate V6 pipeline steps (pure data — matches Python _MURAKUMO_STEPS)
(def pipeline-steps
  [{:command "plan"           :nsid "com.etzhayyim.murakumo.planPipeline"
    :purpose "Show the canonical Hayate V6 data/train/inference pipeline steps."}
   {:command "graph-extract"  :nsid "com.etzhayyim.murakumo.graphExtract"
    :purpose "Extract entities/relations from did_domains with Qwen4B worker."}
   {:command "graph-ingest"   :nsid "com.etzhayyim.murakumo.graphIngest"
    :purpose "Register graph entities as DID nodes and store into LanceDB."}
   {:command "coverage-export" :nsid "com.etzhayyim.murakumo.coverageExport"
    :purpose "Export coverage domains from yata/PDS into coverage_domains npy."}
   {:command "fleet-plan"     :nsid "com.etzhayyim.murakumo.fleetPlan"
    :purpose "Generate slot allocation plan for Hayate V6 fleet training."}
   {:command "train-experts"  :nsid "com.etzhayyim.murakumo.trainExperts"
    :purpose "Run phase-2 expert training and persist bf16/int8 experts."}
   {:command "eval"           :nsid "com.etzhayyim.murakumo.evalV6"
    :purpose "Run Hayate V6 benchmark/eval for regression checks."}
   {:command "optimize"       :nsid "com.etzhayyim.murakumo.optimizeCycle"
    :purpose "Run one efficient optimization cycle (ingest → score → chunk-train → eval)."}])

;; ---------------------------------------------------------------------------
;; Pure: auth header building (reads env lazily when called — no load-time IO)
;; ---------------------------------------------------------------------------

(defn resolve-auth-token
  "Select auth token from an explicit host-provided environment map.
  Returns the token string or empty string.
  The zero-arity form has no ambient authority and therefore returns empty."
  ([] (resolve-auth-token {}))
  ([env]
   (or (get env "ETZHAYYIM_ACCESS_JWT")
       (get env "ETZHAYYIM_ACCESS_TOKEN")
       "")))

(defn build-auth-headers
  "Build Authorization + Content-Type headers map.
  tok may be empty string (will produce a bearer header with empty token —
  caller should validate before making live calls).
  Mirrors Python _auth_headers() — pure map construction."
  [tok]
  {"Authorization"  (str "Bearer " tok)
   "Content-Type"   "application/json"})

;; ---------------------------------------------------------------------------
;; Pure: PDS URL normalization
;; ---------------------------------------------------------------------------

(defn normalize-pds
  "Strip trailing slash from a PDS URL.
  Mirrors Python (pds or resolve_pds()).rstrip('/') — pure string op."
  [pds-url]
  (if (str/ends-with? pds-url "/")
    (subs pds-url 0 (dec (count pds-url)))
    pds-url))

;; ---------------------------------------------------------------------------
;; Pure: HTTP request-shaping layer
;; All build-*-request fns return {:method :url :headers :body?} maps.
;; Tests call these to verify parity with the Python CLI request construction.
;; ---------------------------------------------------------------------------

(defn build-status-request
  "Build GET /xrpc/com.etzhayyim.murakumo.getStatus request map.
  Mirrors Python murakumo_status() httpx.get call."
  [pds-url tok]
  {:method  :get
   :url     (str (normalize-pds pds-url) "/xrpc/com.etzhayyim.murakumo.getStatus")
   :headers (build-auth-headers tok)})

(defn build-list-request
  "Build GET /xrpc/com.etzhayyim.murakumo.listPods request map.
  Mirrors Python murakumo_list() httpx.get call."
  [pds-url tok]
  {:method  :get
   :url     (str (normalize-pds pds-url) "/xrpc/com.etzhayyim.murakumo.listPods")
   :headers (build-auth-headers tok)})

(defn build-route-request
  "Build GET /xrpc/com.etzhayyim.murakumo.getRouting request map.
  Mirrors Python murakumo_route() httpx.get call."
  [pds-url tok]
  {:method  :get
   :url     (str (normalize-pds pds-url) "/xrpc/com.etzhayyim.murakumo.getRouting")
   :headers (build-auth-headers tok)})

(defn build-infer-request
  "Build POST /xrpc/com.etzhayyim.murakumo.infer request map.
  prompt   — required string
  model    — optional override (empty string = use fleet routing)
  Mirrors Python murakumo_infer() httpx.post call."
  [pds-url tok prompt model]
  (let [body (cond-> {:prompt prompt}
               (seq model) (assoc :model model))]
    {:method  :post
     :url     (str (normalize-pds pds-url) "/xrpc/com.etzhayyim.murakumo.infer")
     :headers (build-auth-headers tok)
     :body    body}))

(defn build-xrpc-request
  "Build a generic POST XRPC request.
  payload-str is a JSON string.
  Mirrors Python murakumo_xrpc() httpx.post call."
  [pds-url tok nsid payload-str]
  {:method  :post
   :url     (str (normalize-pds pds-url) "/xrpc/" nsid)
   :headers (merge (build-auth-headers tok) {"content-type" "application/json"})
   :body    (json/parse-string payload-str true)})

(defn build-fleet-jotai-request
  "Build GET /xrpc/com.etzhayyim.murakumo.fleetStatus request map.
  Mirrors Python murakumo_fleet_jotai() httpx.get call."
  [pds-url tok limit]
  {:method  :get
   :url     (str (normalize-pds pds-url) "/xrpc/com.etzhayyim.murakumo.fleetStatus"
                 "?limit=" limit)
   :headers (build-auth-headers tok)})

(defn build-fleet-versions-request
  "Build GET /xrpc/com.etzhayyim.murakumo.workerVersions request map.
  Mirrors Python murakumo_fleet_versions() httpx.get call."
  [pds-url tok]
  {:method  :get
   :url     (str (normalize-pds pds-url) "/xrpc/com.etzhayyim.murakumo.workerVersions")
   :headers (build-auth-headers tok)})

(defn build-train-experts-request
  "Build POST /xrpc/com.etzhayyim.murakumo.trainExperts request map.
  Mirrors Python murakumo_train_experts() httpx.post call."
  [pds-url tok {:keys [label n-labels label-start epochs slots-per device]
                :or   {label "" n-labels 2 label-start 0
                       epochs 1 slots-per 128 device "wgpu"}}]
  {:method  :post
   :url     (str (normalize-pds pds-url) "/xrpc/com.etzhayyim.murakumo.trainExperts")
   :headers (build-auth-headers tok)
   :body    {:label       label
             :nLabels     n-labels
             :labelStart  label-start
             :epochs      epochs
             :slotsPer    slots-per
             :backend     device}})

;; ---------------------------------------------------------------------------
;; Pure: subprocess command-building (argv vectors)
;; argv = vector of strings, no shell-string interpolation (injection-safe)
;; ---------------------------------------------------------------------------

(defn build-git-root-command
  "Return argv vector for 'git rev-parse --show-toplevel'.
  Mirrors Python subprocess.run(['git', 'rev-parse', '--show-toplevel'])."
  []
  ["git" "rev-parse" "--show-toplevel"])

(defn build-eval-command
  "Build argv vector for running eval_v6_bench.py.
  Mirrors Python murakumo_eval() subprocess.run call.
  Opts keys: :python-bin :mode :limit :dim :groups :checkpoint"
  [training-dir {:keys [python-bin mode limit dim groups checkpoint]
                 :or   {python-bin "python3.11" mode "eval"
                        limit 20 dim 256 groups 1 checkpoint ""}}]
  (let [bench-script (str training-dir "/eval_v6_bench.py")
        base-cmd     [python-bin bench-script
                      "--mode"   mode
                      "--limit"  (str limit)
                      "--dim"    (str dim)
                      "--groups" (str groups)]]
    (if (and (= mode "eval") (seq checkpoint))
      (conj base-cmd "--checkpoint" checkpoint)
      (if (seq checkpoint)
        (conj base-cmd "--checkpoint" checkpoint)
        base-cmd))))

(defn build-ssh-command
  "Build argv vector for an SSH call to a Mac mini fleet member.
  mini is the short hostname (e.g. 'amaterasu').
  remote-cmd is the shell command string to execute remotely.
  Mirrors Python _ssh_on_mini() subprocess.run call."
  [mini remote-cmd]
  ["ssh"
   "-o" "BatchMode=yes"
   "-o" "ConnectTimeout=5"
   "-o" "StrictHostKeyChecking=no"
   (str mini "@" mini ".murakumo.lan")
   remote-cmd])

(defn build-nomad-command
  "Build argv vector for a nomad CLI call.
  nomad-path is the resolved path to the nomad binary.
  args is a seq of string arguments.
  Mirrors Python _run_nomad() subprocess.run call."
  [nomad-path & args]
  (into [nomad-path] args))

(defn build-scp-command
  "Build argv vector for deploying daemon.py via scp to a fleet node.
  Mirrors Python murakumo_fleet_deploy() SCP intent."
  [src-path node-host dest-path]
  ["scp" "-o" "StrictHostKeyChecking=no"
   src-path
   (str node-host ":" dest-path)])

;; ---------------------------------------------------------------------------
;; Pure: fleet-models.json parsing
;; ---------------------------------------------------------------------------

(defn parse-fleet-models
  "Parse fleet-models.json data map.
  Returns {:fleet [...] :models {...}} (same keys as the JSON).
  Mirrors Python _load_fleet_models() data access — pure."
  [data]
  {:fleet  (get data "fleet" [])
   :models (get data "models" {})})

(defn probe-cmd-for-model
  "Build the remote shell command string that checks whether a model is present
  on a mini. Returns nil if the kind is unsupported.
  Mirrors Python _probe_model_on_mini() command construction — pure."
  [model-info]
  (let [kind (get model-info "kind" "")]
    (case kind
      "ollama"
      (let [tag (get model-info "ollama_tag" "")]
        (str "curl -fsS --max-time 3 http://localhost:11434/api/tags 2>/dev/null"
             " | grep -q '\"name\":\"" tag "\"'"))

      "comfyui_checkpoint"
      (let [path     (get model-info "path" "")
            filename (get model-info "filename" "")]
        (str "test -s ~/comfyui/" path "/" filename))

      "comfyui_diffusers"
      (let [repo (str/replace (get model-info "diffusers_repo" "") "/" "--")]
        (str "test -d ~/.cache/huggingface/hub/models--" repo "/snapshots"))

      "comfyui_wan"
      (let [parts (for [c (get model-info "components" [])]
                    (str "test -s ~/comfyui/"
                         (get c "path" "") "/" (get c "file" "")))]
        (if (seq parts)
          (str/join " && " parts)
          "false"))

      nil)))

(defn resolve-install-cmd
  "Compute the install shell command string for a model on a mini.
  hf-token is injected as a string (never read at load time).
  Returns nil for unsupported kinds.
  Mirrors Python _install_cmd() — pure string construction."
  [model-info hf-token]
  (let [kind (get model-info "kind" "")]
    (case kind
      "ollama"
      (let [tag (get model-info "ollama_tag" "")]
        (str "ollama pull " tag))

      "comfyui_checkpoint"
      (let [path     (get model-info "path" "")
            filename (get model-info "filename" "")
            hf-repo  (get model-info "hf_repo" "")
            hf-file  (get model-info "hf_file" "")
            url      (str "https://huggingface.co/" hf-repo "/resolve/main/" hf-file)]
        (str "set -e; mkdir -p ~/comfyui/" path "; cd ~/comfyui/" path "; "
             "if [ -s '" filename "' ]; then exit 0; fi; "
             "curl -sL --fail -H 'Authorization: Bearer " hf-token "' "
             "-o '" filename "' '" url "'"))

      "comfyui_diffusers"
      (let [repo (get model-info "diffusers_repo" "")]
        (str "python3 -c \"from diffusers import DiffusionPipeline; "
             "DiffusionPipeline.from_pretrained('" repo "')\""))

      nil)))

;; ---------------------------------------------------------------------------
;; Pure: Nomad JSON output parsing
;; ---------------------------------------------------------------------------

(defn parse-nodes-json
  "Parse Nomad 'node status -json' output string into a vector of node maps.
  Mirrors Python usage of json.loads(out) in murakumo_fleet_nodes."
  [json-str]
  (json/parse-string json-str true))

(defn resolve-node-id
  "Find a Nomad node ID by name in a parsed nodes list.
  name-or-meta is matched against :Name or :Meta {:fleet_node}.
  Returns the node ID string or nil.
  Mirrors Python _nomad_node_id() — pure list search."
  [nodes node-name]
  (some (fn [n]
          (when (or (= (str (:Name n)) node-name)
                    (= (get-in n [:Meta :fleet_node]) node-name))
            (:ID n)))
        nodes))

(defn resolve-alloc-id
  "Find a running Nomad allocation ID for a node name.
  Returns the alloc ID string or nil.
  Mirrors Python _nomad_alloc_id() — pure list search."
  [allocs node-name]
  (some (fn [a]
          (when (and (= (str (:NodeName a)) node-name)
                     (= (str (:ClientStatus a)) "running"))
            (:ID a)))
        allocs))

;; ---------------------------------------------------------------------------
;; Pure: Nomad addr resolution
;; ---------------------------------------------------------------------------

(defn resolve-nomad-addr
  "Select NOMAD_ADDR from explicit host environment data. There is no default.
  Throws ex-info when the host supplied no address, like the other unconfigured
  host capabilities in this namespace.
  Mirrors Python _resolve_nomad_addr().

  This returned a literal \"http://benjamin.local:4646\" until 2026-08-12.
  `benjamin` is a real murakumo mac-mini and `.local` is the mDNS namespace
  (RFC 6762), so any host on the same link can claim that name by answering
  first.  Nothing in the repo — and no entry in deps.edn :platform — states a
  Nomad address, so that literal was the only one there was: a host nobody
  chose, aimed at by default.

  UNLIKE the Python twin this was NOT a credential path, and the fix here is
  parity and hardening rather than a security fix.  Python's _run_nomad passes
  {**os.environ} to the nomad CLI, so a NOMAD_TOKEN set in the operator's shell
  travelled to that host as X-Nomad-Token.  This namespace takes the environment
  as explicit host data (default {}) and holds no ambient authority, so nothing
  could travel that a caller had not already handed over deliberately.  What is
  fixed here is that the twins no longer disagree, and that a reader of this
  file no longer finds a squattable fleet host presented as a sane default."
  ([] (resolve-nomad-addr {}))
  ([env]
   (let [addr (str/trim (or (get env "NOMAD_ADDR") ""))]
     (when (str/blank? addr)
       (throw (ex-info "Murakumo host capability not configured: :nomad-addr"
                       {:missing-capability :nomad-addr})))
     ;; Callers build (str addr "/v1/nodes"), so a trailing slash would yield
     ;; "…//v1/nodes". The old `or` did not guard that either.
     (str/replace addr #"/+$" ""))))

;; ---------------------------------------------------------------------------
;; IO: default implementations
;; ---------------------------------------------------------------------------

(defn- missing-capability [capability]
  (fn [& _]
    (throw (ex-info (str "Murakumo host capability not configured: " capability)
                    {:missing-capability capability}))))

(def ^:private default-proc-fn (missing-capability :process))

(def ^:private default-http-fn (missing-capability :http))

;; ---------------------------------------------------------------------------
;; IO: git root
;; ---------------------------------------------------------------------------

(defn run-git-root
  "Resolve git repo root via subprocess.
  Returns the root path string or raises ex-info.
  Opts: :proc-fn"
  ([] (run-git-root {}))
  ([{:keys [proc-fn] :or {proc-fn default-proc-fn}}]
   (let [argv (build-git-root-command)
         r    (proc-fn argv {})]
     (if (zero? (:exit r))
       (str/trim (:out r))
       (throw (ex-info "not in a git repository" {:argv argv :exit (:exit r)}))))))

;; ---------------------------------------------------------------------------
;; IO: XRPC HTTP helpers (injectable http-fn)
;; ---------------------------------------------------------------------------

(defn call-xrpc-get
  "GET an XRPC endpoint.  Returns parsed JSON body map.
  Raises ex-info on HTTP error (>=400).
  Mirrors Python httpx.get(...).raise_for_status() pattern."
  ([req] (call-xrpc-get req {}))
  ([req {:keys [http-fn] :or {http-fn default-http-fn}}]
   (let [resp (http-fn req)]
     (when (>= (:status resp) 400)
       (throw (ex-info (str "XRPC " (:status resp) " GET " (:url req))
                       {:status (:status resp) :body (:body resp)})))
     (json/parse-string (:body resp) true))))

(defn call-xrpc-post
  "POST an XRPC endpoint.  Returns parsed JSON body map.
  Raises ex-info on HTTP error (>=400)."
  ([req] (call-xrpc-post req {}))
  ([req {:keys [http-fn] :or {http-fn default-http-fn}}]
   (let [resp (http-fn req)]
     (when (>= (:status resp) 400)
       (throw (ex-info (str "XRPC " (:status resp) " POST " (:url req))
                       {:status (:status resp) :body (:body resp)})))
     (json/parse-string (:body resp) true))))

;; ---------------------------------------------------------------------------
;; IO: SSH to a mini
;; ---------------------------------------------------------------------------

(defn run-ssh-on-mini
  "SSH into a fleet mini and run remote-cmd.
  Returns {:ok bool :output str}.
  Opts: :proc-fn :timeout-ms"
  ([mini remote-cmd] (run-ssh-on-mini mini remote-cmd {}))
  ([mini remote-cmd {:keys [proc-fn] :or {proc-fn default-proc-fn}}]
   (let [argv (build-ssh-command mini remote-cmd)
         r    (proc-fn argv {})]
     {:ok     (zero? (:exit r))
      :output (str (:out r) (:err r))})))

;; ---------------------------------------------------------------------------
;; IO: model probing via SSH
;; ---------------------------------------------------------------------------

(defn probe-model-on-mini
  "Check whether model-info is present on mini via SSH probe.
  Returns true if present.
  Opts: :proc-fn"
  ([mini model-info] (probe-model-on-mini mini model-info {}))
  ([mini model-info opts]
   (if-let [cmd (probe-cmd-for-model model-info)]
     (:ok (run-ssh-on-mini mini cmd opts))
     false)))

;; ---------------------------------------------------------------------------
;; IO: nomad CLI wrapper
;; ---------------------------------------------------------------------------

(defn run-nomad
  "Invoke the nomad CLI with args.
  Returns {:exit :out :err}.
  Opts: :proc-fn :nomad-path :nomad-addr :env"
  ([args] (run-nomad args {}))
  ([args {:keys [proc-fn nomad-path nomad-addr env]
          :or   {proc-fn   default-proc-fn
                 nomad-path "nomad"
                 nomad-addr nil}}]
   (let [env  (or env {})
         addr (or nomad-addr (resolve-nomad-addr env))
         argv (apply build-nomad-command nomad-path args)
         child-env (assoc env "NOMAD_ADDR" addr)]
     (proc-fn argv {:env child-env}))))

;; ---------------------------------------------------------------------------
;; Dry-run plan printing
;; ---------------------------------------------------------------------------

(defn print-dry-run-plan
  "Print a human-readable dry-run summary of the operations that WOULD be
  executed — no subprocess or network calls.
  Mirrors the 'dry-run' output pattern used throughout Python murakumo_cmd.py."
  [plan-items]
  (println "murakumo dry-run plan — no network or subprocess calls")
  (println "=========================================================")
  (doseq [{:keys [op description argv request]} plan-items]
    (println (str "  [" (name op) "] " description))
    (when argv    (println (str "    argv:    " (str/join " " argv))))
    (when request (println (str "    method:  " (str/upper-case (name (:method request "")))
                                "  url: " (:url request)))))
  (println "\ndry-run: no changes applied."))
