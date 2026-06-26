#!/usr/bin/env bb
;; etzhayyim independent atproto PDS — install/uninstall the RESIDENT mesh server (NO k8s).
;; The PDS runs as a per-user macOS LaunchAgent (`bb serve`) whose state is the kotoba
;; Datom log on the LOCAL kotoba engine (KOTOBA_URL=loopback) and whose writes are signed
;; per-actor from the SEALED P-256 keystore — no StatefulSet/PV/Deployment/Ingress, the
;; launchd agent + a Cloudflare Tunnel replace the entire k8s footprint.
;;
;;   bb deploy/install.clj install    → render the plist from env, load it, kickstart
;;   bb deploy/install.clj uninstall  → bootout + remove the plist
;;   bb deploy/install.clj status     → agent state + tail the log
;;
;; Required env at install time (from the mesh node — NEVER committed):
;;   MURAKUMO_SEAL_KEY    seal for the actor-sealed P-256 keystore (present-only)
;;   PDS_ACTOR_KEYS_DIR   path to the per-actor sealed keystore (Path B registry)
;; Optional (sensible mesh defaults):
;;   KOTOBA_URL  (http://127.0.0.1:8077)   KOTOBA_GRAPH (etzhayyim-pds)
;;   PDS_HOST    (atproto.etzhayyim.com)    PORT (8787)
(require '[babashka.fs :as fs]
         '[babashka.process :as p]
         '[clojure.string :as str])

(def label  "com.etzhayyim.pds")
(def here   (str (fs/parent (fs/absolutize *file*))))                       ; …/deploy
(def pdsdir (str (fs/normalize (fs/absolutize (fs/path here "..")))))       ; the clj PDS dir
(def repo   (str (fs/normalize (fs/absolutize (fs/path here ".." ".." ".."))))) ; repo root
(def bb     (or (some-> (fs/which "bb") str) "/opt/homebrew/bin/bb"))
(def home   (System/getProperty "user.home"))
(def plist  (str home "/Library/LaunchAgents/" label ".plist"))
(def log    (str home "/Library/Logs/etzhayyim-pds.log"))
(def uid    (str/trim (:out (p/shell {:out :string} "id" "-u"))))
(def domain (str "gui/" uid))

(defn- env [k d] (or (not-empty (System/getenv k)) d))

(defn- sh! [& args] (apply p/shell {:continue true :out :string :err :string} args))
(defn- tail [path n]
  (if (fs/exists? path) (str/join "\n" (take-last n (str/split-lines (slurp path)))) "(no log)"))

(defn install []
  (let [seal       (System/getenv "MURAKUMO_SEAL_KEY")
        keys-dir   (System/getenv "PDS_ACTOR_KEYS_DIR")
        kotoba-url (env "KOTOBA_URL"   "http://127.0.0.1:8077")
        kotoba-gr  (env "KOTOBA_GRAPH" "etzhayyim-pds")
        pds-host   (env "PDS_HOST"     "atproto.etzhayyim.com")
        port       (env "PORT"         "8787")]
    (when (str/blank? seal)
      (println "WARN: MURAKUMO_SEAL_KEY unset → the PDS will run UNSIGNED (not Path B).")
      (println "      set it + PDS_ACTOR_KEYS_DIR for per-actor sealed signing, then re-install."))
    (when (str/blank? keys-dir)
      (println "WARN: PDS_ACTOR_KEYS_DIR unset → no per-actor registry; writes unsigned."))
    (fs/create-dirs (str home "/Library/LaunchAgents"))
    (fs/create-dirs (str home "/Library/Logs"))
    (let [rendered (-> (slurp (str (fs/path here "com.etzhayyim.pds.plist.template")))
                       (str/replace "@BB@"           bb)
                       (str/replace "@PDSDIR@"       pdsdir)
                       (str/replace "@HOME@"         home)
                       (str/replace "@KOTOBA_URL@"   kotoba-url)
                       (str/replace "@KOTOBA_GRAPH@" kotoba-gr)
                       (str/replace "@ACTOR_KEYS_DIR@" (or keys-dir ""))
                       (str/replace "@SEAL@"         (or seal ""))
                       (str/replace "@PDS_HOST@"     pds-host)
                       (str/replace "@PORT@"         port))]
      (spit plist rendered)
      ;; the rendered plist holds the seal — lock it down to the owner (mode 600).
      (fs/set-posix-file-permissions plist "rw-------"))
    (sh! "launchctl" "bootout" (str domain "/" label))                     ; idempotent reload
    (p/shell "launchctl" "bootstrap" domain plist)
    (println (str "installed + loaded: " plist))
    (println (str "  state = kotoba engine " kotoba-url " graph " kotoba-gr " · host " pds-host ":" port))
    (println "  NO k8s: launchd LaunchAgent + Cloudflare Tunnel replace the StatefulSet/Ingress.")
    (p/shell "launchctl" "kickstart" "-k" (str domain "/" label))
    (Thread/sleep 3000)
    (println (tail log 6))
    (println "\nnext: expose to the apex via the tunnel (deploy/cloudflared-pds.config.yml.template),")
    (println (str "      then set the apex Worker secret XRPC_PDS_UPSTREAM = https://" pds-host " + wrangler deploy."))))

(defn uninstall []
  (sh! "launchctl" "bootout" (str domain "/" label))
  (fs/delete-if-exists plist)
  (println (str "uninstalled: " label)))

(defn status []
  (let [out (:out (sh! "launchctl" "print" (str domain "/" label)))]
    (if (str/blank? out)
      (println "(not loaded)")
      (->> (str/split-lines out)
           (filter #(re-find #"(?i)state =|program =|last exit|pid =" %))
           (run! #(println (str/trim %))))))
  (println "--- last log ---")
  (println (tail log 8)))

(let [cmd (or (first *command-line-args*) "status")]
  (case cmd
    "install"   (install)
    "uninstall" (uninstall)
    "status"    (status)
    (do (println "usage: bb deploy/install.clj [install|uninstall|status]") (System/exit 2))))
