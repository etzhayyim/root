(ns etzhayyim.watchdog
  "External supervisor for the organism — the immune-system kaizen.

   The organism's OWN watchdog (health.json) is pull-only and lives INSIDE the heartbeat
   loop, so a WEDGED loop (a layer hangs, the single-threaded loop blocks) freezes health.json
   silently while the process stays alive — launchd KeepAlive only sees whole-process DEATH,
   never a stuck layer. This is an INDEPENDENT process (launchd runs `-check` every 60s) that
   reads health.json freshness from OUTSIDE: if the loop has not ticked in `wedge-ms` it force
   -restarts the organism, turning an invisible hang into a clean restart (the regrade's #3
   whole-loop-death blind spot). It also probes the SUBSTRATE the organism rides on (kotoba
   :8077, IPFS API, the served page) so a dead dependency is visible, and writes watchdog.json
   so the supervision itself is observable. Shells out to system binaries only (launchctl /
   pgrep / id) per the clj/bb operational rule; no first-party logic in shell."
  (:require [cheshire.core :as json]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [babashka.process :as p]
            [babashka.http-client :as http]))

(def ^:private health-json "50-infra/etzhayyim-did-web/public/organism/health.json")
(def ^:private out-paths
  ["orgs/etzhayyim/com-etzhayyim-app-organism/public/watchdog.json"
   "50-infra/etzhayyim-did-web/public/organism/watchdog.json"])
(def ^:private service "com.etzhayyim.organism.heartbeat")
;; the loop ticks write-health! every 2s; 120s of silence = unambiguously wedged
;; (pulse cadence is 6s, so this is 20 missed pulse beats) — conservative, no false restarts.
(def ^:private wedge-ms 120000)

(defn- uid [] (str/trim (:out (p/shell {:out :string :continue true} "id" "-u"))))

(defn- reachable
  "true if the URL answered at all (connection made), regardless of status code — we are
   asking 'is the process listening', not 'is the response 200'."
  [url]
  (try (some? (:status (http/get url {:timeout 4000 :throw false}))) (catch Throwable _ false)))

(defn- ok-200 [url]
  (try (= 200 (:status (http/get url {:timeout 4000 :throw false}))) (catch Throwable _ false)))

(defn- organism-up? []
  (try (-> (p/shell {:out :string :continue true} "pgrep" "-f" "organism:heartbeat")
           :out str/trim seq boolean)
       (catch Throwable _ false)))

(defn- kick! []
  (let [u (uid)]
    (if-not (re-matches #"\d+" u)               ; guard a malformed service-target (gui//svc)
      (binding [*out* *err*] (println "[watchdog] ⚠ wedge detected but uid unresolved — NOT kicking:" (pr-str u)))
      (do
        (binding [*out* *err*] (println "[watchdog] ⚠ organism wedged/down — kickstart -k restart"))
        (try (p/shell {:continue true} "launchctl" "kickstart" "-k"
                      (str "gui/" u "/" service))
             (catch Throwable e (binding [*out* *err*] (println "[watchdog] kick failed:" (.getMessage e)))))))))

(defn -check
  "One supervision pass (launchd StartInterval re-invokes it every 60s — not a resident loop)."
  [& _]
  (let [now    (System/currentTimeMillis)
        health (try (json/parse-string (slurp health-json)) (catch Throwable _ nil))
        h-now  (get health "now")
        age    (when h-now (- now h-now))
        up     (organism-up?)
        ;; wedged = the loop has gone silent past the threshold (process may still be alive),
        ;; OR the process is gone and launchd has not already brought it back.
        wedged (or (not up) (and age (> age wedge-ms)))
        _      (when wedged (kick!))
        kotoba (ok-200 "http://localhost:8077/health")
        ipfs   (reachable "http://localhost:5001/api/v0/version")
        page   (reachable "http://localhost:8799/organism/health.json")
        status {:checkedAt (str (java.time.Instant/ofEpochMilli now))
                :organismUp up :loopAgeMs age :wedged (boolean wedged)
                :action (if wedged "kickstart" "none")
                :substrate {:kotoba kotoba :ipfs ipfs :servedPage page}}]
    (doseq [pth out-paths] (io/make-parents pth) (spit pth (json/generate-string status {:pretty true})))
    (binding [*out* *err*]
      (println (format "[watchdog] organism=%s loopAge=%sms kotoba=%s ipfs=%s page=%s%s"
                       up age kotoba ipfs page (if wedged "  WEDGED→kick" ""))))
    status))
