(ns etzhayyim.fleet-deploy
  "fleet-deploy (bb) — render + install the resident LaunchAgents that make the
  self-evolution loop ACTUALLY run (ADR-2606271400 D4/D5). Today `bb fleet:probe`
  reports 1/24 heartbeats resident + the leashed-PDS post path code-complete-but-idle;
  this closes that gap by installing:

    - the post-drain agent  — runs `bb drain` (etzhayyim PDS project) on an interval,
      presenting a member leash so ibuki's prepared posts flow to the PDS, attributed
      to the consenting member (the leashed-autonomous posting RUNTIME, ADR-2606111400);
    - (referenced) the cell-runner agent — the per-node heartbeat supervisor.

  Per the repo rule (residence = a launchd LaunchAgent, not a `nohup &`), this RENDERS
  the plist deterministically from config and installs it via `launchctl` (a system
  binary; the LOGIC is clj). `--render` (default) is pure-printable + the unit of the
  tests; `--install-local` / `--uninstall-local` act on ~/Library/LaunchAgents on THIS
  machine (where the PDS runs for the ADR runbook); no key is held (the leash is read
  from the member-provided env at run time, never embedded).

  Run:  bb fleet:deploy                 (render the post-drain plist to stdout)
        bb fleet:deploy --install-local (write + bootstrap the LaunchAgent here)
        bb fleet:deploy --uninstall-local"
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            #?(:bb [babashka.process :as proc]
               :clj [babashka.process :as proc])))

(def post-drain-label "com.etzhayyim.post-drain")
(def pds-project "50-infra/etzhayyim-atproto-pds-clj")
(def default-interval-s 300)

(defn- xml-escape [s]
  (-> (str s) (str/replace "&" "&amp;") (str/replace "<" "&lt;") (str/replace ">" "&gt;")))

(defn render-post-drain-plist
  "Render the post-drain LaunchAgent. `env` carries the member-provided run config
  (PDS_DRAIN_BASE / PDS_DRAIN_QUEUE / PDS_DRAIN_LEASH / cursor / receipts). The leash
  is the member's STANDING CONSENT presented at run time — passed through the agent's
  EnvironmentVariables, never a held signing key (no-server-key: the PDS signs)."
  [{:keys [label working-dir bb-path interval-s env]
    :or {label post-drain-label interval-s default-interval-s
         bb-path "/opt/homebrew/bin/bb" env {}}}]
  (let [env-rows (->> env
                      (map (fn [[k v]]
                             (str "    <key>" (xml-escape k) "</key>\n"
                                  "    <string>" (xml-escape v) "</string>")))
                      (str/join "\n"))]
    (str "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
         "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
         "<plist version=\"1.0\">\n<dict>\n"
         "  <key>Label</key><string>" (xml-escape label) "</string>\n"
         "  <key>ProgramArguments</key>\n  <array>\n"
         "    <string>" (xml-escape bb-path) "</string>\n"
         "    <string>drain</string>\n  </array>\n"
         "  <key>WorkingDirectory</key><string>" (xml-escape working-dir) "</string>\n"
         "  <key>StartInterval</key><integer>" interval-s "</integer>\n"
         "  <key>RunAtLoad</key><true/>\n"
         "  <key>EnvironmentVariables</key>\n  <dict>\n" env-rows "\n  </dict>\n"
         "  <key>StandardOutPath</key><string>/tmp/" (xml-escape label) ".out.log</string>\n"
         "  <key>StandardErrorPath</key><string>/tmp/" (xml-escape label) ".err.log</string>\n"
         "</dict>\n</plist>\n")))

(defn- launch-agents-path [label]
  (str (System/getProperty "user.home") "/Library/LaunchAgents/" label ".plist"))

(defn- drain-env-from-process []
  ;; only forward the drain knobs the member/operator set in THIS process env;
  ;; PDS_DRAIN_LEASH is the member's standing consent (present-only, never our key).
  (into {} (keep (fn [k] (when-let [v (System/getenv k)] [k v]))
                 ["PDS_DRAIN_BASE" "PDS_DRAIN_QUEUE" "PDS_DRAIN_CURSOR"
                  "PDS_DRAIN_RECEIPTS" "PDS_DRAIN_LEASH"])))

(defn- sh [& args]
  (try (let [{:keys [out err exit]} (apply proc/sh {:out :string :err :string} args)]
         {:out out :err err :exit exit})
       (catch Exception e {:out "" :err (.getMessage e) :exit 127})))

(defn install-local!
  "Write the post-drain plist to ~/Library/LaunchAgents and bootstrap it for the current
  GUI user. Idempotent: bootout first, then bootstrap + kickstart."
  []
  (let [home (System/getProperty "user.home")
        wd   (str home "/github/com-junkawasaki/orgs/etzhayyim/root/" pds-project)
        plist (render-post-drain-plist {:working-dir wd :env (drain-env-from-process)})
        path (launch-agents-path post-drain-label)
        uid (str/trim (:out (sh "id" "-u")))
        domain (str "gui/" uid)]
    (io/make-parents path)
    (spit path plist)
    (sh "launchctl" "bootout" domain path) ; ignore if not loaded
    (let [b (sh "launchctl" "bootstrap" domain path)
          k (sh "launchctl" "kickstart" "-k" (str domain "/" post-drain-label))]
      {:plist-path path :bootstrap-exit (:exit b) :kickstart-exit (:exit k)
       :bootstrap-err (:err b)})))

(defn uninstall-local! []
  (let [path (launch-agents-path post-drain-label)
        uid (str/trim (:out (sh "id" "-u")))]
    (sh "launchctl" "bootout" (str "gui/" uid) path)
    (when (.exists (io/file path)) (.delete (io/file path)))
    {:removed path}))

(defn -main [& args]
  (let [a (set args)]
    (cond
      (a "--install-local")   (println (pr-str (install-local!)))
      (a "--uninstall-local") (println (pr-str (uninstall-local!)))
      :else (println (render-post-drain-plist
                       {:working-dir (str "<repo>/" pds-project)
                        :env (merge {"PDS_DRAIN_BASE" "http://127.0.0.1:2583"
                                     "PDS_DRAIN_QUEUE" "<ibuki posts queue>"
                                     "PDS_DRAIN_LEASH" "<member leash from `bb leash-issue`>"}
                                    (drain-env-from-process))})))))
