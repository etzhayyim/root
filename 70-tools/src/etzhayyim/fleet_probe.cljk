(ns etzhayyim.fleet-probe
  "fleet-probe (bb) — does the murakumo heartbeat fleet ACTUALLY run, or is it
  only DEFINED in cells.edn? This is the clj/bb answer to \"murakumo fleet で kotoba
  上で常駐しているのか / artificial-organism は動いているのか\" (per repo rule: ops code
  is clj/bb over the Datom log, not py/sh).

  The gap it measures: cells.edn / fleet.edn DEFINE which heartbeat cell runs on
  which node at which cron — but residence is a separate operator step (a launchd
  LaunchAgent / k3s DaemonSet must actually be up on the physical Mac-mini). The
  per-node healthz server binds 127.0.0.1 ONLY (lite_runner.py `_serve_healthz`),
  so residence can only be observed from ON the node — we reach each node over
  `ssh <name>` (Tailscale) and probe loopback.

  Per beat it gathers, for every cron/lan-api heartbeat cell:
    - is its node ONLINE   (tailscale status)
    - is a cell-runner / heartbeat PROCESS up (launchctl + pgrep, on the node)
    - does its healthz port ANSWER on 127.0.0.1 (curl, on the node)
  → classifies each cell  :alive / :defined-only-silent / :node-unreachable
  and probes the evo-x2 inference backend (Ollama/LiteLLM) + the issachar kotoba
  :8077 engine. Writes an EDN report (data/fleet-probe.edn, gitignored) + a human
  summary. Shelling out to ssh/tailscale/curl (system binaries) via
  babashka.process is allowed; the LOGIC is clj.

  Run:  bb fleet:probe                 (all online nodes)
        bb fleet:probe --nodes a,b     (subset)
        bb fleet:probe --no-ssh        (tailscale + inference only, no node login)"
  (:require [clojure.edn :as edn]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [clojure.pprint :as pprint]
            #?(:bb [babashka.process :as proc]
               :clj [babashka.process :as proc])))

;; ── repo-relative paths ─────────────────────────────────────────────────────
(def CELLS-EDN "50-infra/cluster/murakumo/cell-runner/cells.edn")
(def FLEET-EDN "50-infra/murakumo/fleet.edn")
(def REPORT-OUT "out/fleet-probe.edn") ; root out/ is gitignored (.gitignore:18)

;; ── pure: parse the DEFINED expectation ─────────────────────────────────────
(defn expected-heartbeats
  "From cells.edn → the resident cells we expect a daemon to be serving:
  cron heartbeats + lan-api services (both bind a healthz port). Returns
  [{:name :node :healthz-port :trigger :cron?}]."
  [cells-edn]
  (->> (:cell cells-edn)
       (keep (fn [{:keys [name node healthz_port trigger]}]
               (let [kind (:kind trigger)]
                 (when (and node healthz_port (#{"cron" "lan-api"} kind))
                   {:name name :node node :healthz-port healthz_port
                    :trigger kind :cron (:expr trigger)}))))
       (sort-by (juxt :node :healthz-port))
       vec))

(defn parse-tailscale-status
  "tailscale status text → {node-name {:ts-ip s :online? bool}}. A line is
  `<ip> <host> <user> <os> <state...>`; offline lines contain 'offline'."
  [s]
  (->> (str/split-lines (or s ""))
       (keep (fn [line]
               (let [cols (str/split (str/trim line) #"\s+")]
                 (when (>= (count cols) 4)
                   (let [[ip host] cols
                         rest-> (str/lower-case (str/join " " (drop 4 cols)))
                         online? (and (not (str/includes? rest-> "offline"))
                                      (str/includes? rest-> "active"))]
                     [host {:ts-ip ip :online? online?
                            :state (str/join " " (drop 4 cols))}])))))
       (into {})))

(defn classify
  "Given a heartbeat row + node online? + the node's probe result, classify."
  [{:keys [healthz-port]} online? node-probe]
  (cond
    (not online?)                          :node-unreachable
    (nil? node-probe)                      :node-unreachable
    (:ssh-error node-probe)                :node-unreachable
    (contains? (:healthz-ok node-probe)
               healthz-port)               :alive
    :else                                  :defined-only-silent))

;; ── IO: shell out (system binaries — allowed) ───────────────────────────────
(defn- sh [& args]
  (try (let [{:keys [out err exit]}
             (apply proc/sh {:out :string :err :string} args)]
         {:out out :err err :exit exit})
       (catch Exception e {:out "" :err (.getMessage e) :exit 127})))

(defn tailscale-status [] (:out (sh "tailscale" "status")))

(def ^:private REMOTE-PROBE
  ;; one shell run per node: launchctl + pgrep + per-port loopback healthz.
  ;; PORTS placeholder is replaced with the node's space-separated port list.
  (str "echo '##LAUNCHCTL##'; "
       "launchctl list 2>/dev/null | grep -iE 'etzhayyim|cell-runner|organism|heartbeat|litellm|kotoba|murakumo' || true; "
       "echo '##PGREP##'; "
       "pgrep -fl 'lite_runner|cell_runner|organism|heartbeat|litellm|kotoba' 2>/dev/null || true; "
       "echo '##HEALTHZ##'; "
       ;; OK only if the body carries the lite_runner healthz signature ({\"ok\":..,\"node\":..});
       ;; a bare listener that 404s (e.g. kotoba on a neighbouring port) is NOT this cell.
       "for p in PORTS; do "
       "  b=$(curl -s -m 2 \"127.0.0.1:$p\" 2>/dev/null); "
       "  case \"$b\" in *'\"ok\"'*|*'\"node\"'*) echo \"$p OK\";; *) echo \"$p DOWN\";; esac; "
       "done"))

(defn probe-node
  "ssh into node, run the combined residence probe over the given healthz ports.
  Returns {:launchctl [..] :pgrep [..] :healthz-ok #{ports} :raw s} or {:ssh-error s}."
  [node ports]
  (let [cmd (str/replace REMOTE-PROBE "PORTS" (str/join " " (sort ports)))
        {:keys [out err exit]}
        (sh "ssh" "-o" "BatchMode=yes" "-o" "ConnectTimeout=6"
            "-o" "StrictHostKeyChecking=accept-new" node cmd)]
    (if (not= 0 exit)
      {:ssh-error (str/trim (str err)) :exit exit}
      (let [section (fn [tag]
                      (->> (str/split out (re-pattern (str "##" tag "##")))
                           second (#(or % ""))
                           (#(first (str/split % #"##")))
                           str/split-lines
                           (map str/trim) (remove str/blank?) vec))
            healthz (section "HEALTHZ")]
        {:launchctl (section "LAUNCHCTL")
         :pgrep     (section "PGREP")
         :healthz-ok (->> healthz
                          (keep #(let [[p st] (str/split % #"\s+")]
                                   (when (= st "OK") (parse-long (str p)))))
                          set)
         :raw out}))))

(defn probe-http [url]
  (let [{:keys [out exit]}
        (sh "curl" "-s" "-m" "5" "-o" "/dev/null" "-w" "%{http_code}" url)]
    {:url url :http (when (= 0 exit) (str/trim out))
     :ok (= "200" (str/trim (str out)))}))

;; ── orchestration ───────────────────────────────────────────────────────────
(defn run-probe [{:keys [only-nodes ssh?]}]
  (let [cells   (edn/read-string (slurp CELLS-EDN))
        hbs     (cond->> (expected-heartbeats cells)
                  (seq only-nodes) (filter #(only-nodes (:node %))))
        ts      (parse-tailscale-status (tailscale-status))
        nodes   (distinct (map :node hbs))
        ;; per-node: ports to probe
        node->ports (reduce (fn [m {:keys [node healthz-port]}]
                              (update m node (fnil conj #{}) healthz-port))
                            {} hbs)
        ;; probe each ONLINE node over ssh (parallel)
        node->probe (when ssh?
                      (into {}
                            (pmap (fn [n]
                                    [n (if (get-in ts [n :online?])
                                         (probe-node n (node->ports n))
                                         nil)])
                                  nodes)))
        rows    (mapv (fn [{:keys [node healthz-port] :as hb}]
                        (let [online? (boolean (get-in ts [node :online?]))
                              np (get node->probe node)]
                          (assoc hb
                                 :online online?
                                 :status (if ssh?
                                           (classify hb online? np)
                                           (if online? :node-online-unprobed :node-unreachable)))))
                      hbs)
        ;; inference backends (evo-x2) + kotoba
        infer   {:ollama-lan  (probe-http "http://192.168.1.16:11434/v1/models")
                 :litellm-lan (probe-http "http://192.168.1.16:4000/v1/models")
                 :ollama-ts   (probe-http "http://100.82.98.110:11434/v1/models")}
        ;; kotoba is a real server that answers (404 on /) — TCP-listener check, not
        ;; the lite_runner healthz signature: http_code != 000 means a server is up.
        kotoba  (when ssh?
                  (let [{:keys [out exit]}
                        (sh "ssh" "-o" "BatchMode=yes" "-o" "ConnectTimeout=6" "issachar"
                            "curl -s -m 3 -o /dev/null -w '%{http_code}' 127.0.0.1:8077/ || echo 000")
                        code (str/trim (str out))]
                    {:reachable (and (= 0 exit) (not= "000" code) (not (str/blank? code)))
                     :http code}))]
    {:generated-by "etzhayyim.fleet-probe"
     :nodes (into {} (map (fn [n] [n (merge (get ts n {:online? false})
                                            {:probed? (and ssh? (boolean (get-in ts [n :online?])))})])
                          nodes))
     :heartbeats rows
     :inference infer
     :kotoba kotoba
     :summary (frequencies (map :status rows))}))

;; ── human summary ───────────────────────────────────────────────────────────
(defn print-report [{:keys [heartbeats summary inference kotoba nodes]}]
  (println "── murakumo heartbeat fleet — RESIDENCE PROBE ─────────────────────")
  (println (format "%-32s %-10s %-7s %-6s %s" "CELL" "NODE" "ONLINE" "PORT" "STATUS"))
  (doseq [{:keys [name node online healthz-port status]} heartbeats]
    (println (format "%-32s %-10s %-7s %-6s %s"
                     (subs name 0 (min 32 (count name)))
                     node (if online "yes" "NO") healthz-port (clojure.core/name status))))
  (println "──────────────────────────────────────────────────────────────────")
  (println "summary:" (into (sorted-map) summary))
  (println "nodes:" (->> nodes (map (fn [[n {:keys [online?]}]] (str n (if online? "✓" "✗")))) (str/join " ")))
  (println "inference (evo-x2):")
  (doseq [[k {:keys [url http ok]}] inference]
    (println (format "  %-12s %s -> %s" (clojure.core/name k) url (if ok "200 OK" (str "DOWN/" http)))))
  (when kotoba (println "kotoba :8077 (issachar):" (if (:reachable kotoba) (str "UP (http " (:http kotoba) ")") (str "DOWN " (or (:http kotoba) "")))))
  (println "──────────────────────────────────────────────────────────────────"))

(defn -main [& args]
  (let [argset (set args)
        only   (when-let [a (some->> args (drop-while #(not= "--nodes" %)) second)]
                 (set (str/split a #",")))
        report (run-probe {:only-nodes only :ssh? (not (argset "--no-ssh"))})]
    (io/make-parents REPORT-OUT)
    (spit REPORT-OUT (with-out-str (pprint/pprint report)))
    (print-report report)
    (println "EDN report →" REPORT-OUT)))
